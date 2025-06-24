import pathlib
import pandas as pd 
import datetime
from collections import defaultdict
import time
import numpy as np
import json 
import base64
import logging
logger = logging.getLogger(__name__)
from kafka import KafkaProducer

try:
    from libs.mqttInterface import MqttInterface
    from libs import configurationManager  
except:
    from .mqttInterface import MqttInterface
    from . import configurationManager  

class ImportToDataLakeManager():
    def __init__(self):
        # countup
        self.cnt = 0
        try:
            configuration = configurationManager.getConfig("DataForwarder")
            broker = configuration["broker"]
            port = configuration["port"]
            topic_sub = "xxx"
            topic_pub = "local_data/dataForwarder"
            username = configuration["user_name"]
            password = configuration["password"]
        except:
            logger.info("Mqtt configuration is incomplete.")
        
        try:
            self.mqttInterface = MqttInterface(broker, port, topic_sub, topic_pub, username, password)
            self.mqttInterface.connectMqtt()
        except:
            self.mqttInterface = None
            logger.info("Mqtt broker was not reachable.")

        try: 
            self.producer = KafkaProducer(bootstrap_servers='fwgserv02a:9091')
        except:
            self.producer = None
            logger.info("Kafka broker was not reachable.")

    @staticmethod
    def convertStrToTimestampInSeconds(msg):
        if isinstance(msg, str):
            return datetime.datetime.strptime(msg, "%Y%m%d-%H.%M.%S.%f").timestamp()
        else:
            lst = []
            for bla in msg:
                lst.append(datetime.datetime.strptime(bla, "%Y%m%d-%H.%M.%S.%f").timestamp())
            return pd.Series(lst, name="timestamp")

    @staticmethod
    def blings(df):
        df['full_datetime'] = df['Date'].apply(str) + '-' +  df['Time']
        df['timestamp'] = df['full_datetime'].apply(ImportToDataLakeManager.convertStrToTimestampInSeconds)
        return df

    def collectAndSendData(self, project="example_project", working_directory_path=None, protocol="MQTT"):
        if working_directory_path is None:
            working_directory_path = pathlib.Path(f'./{project}/')

        dat_path = sorted(working_directory_path.glob('**/pH.csv'))
        
        ## Find the scheme csv
        scheme_path = list(working_directory_path.glob(f'**/scheme.csv'))[0]
        df_scheme = pd.read_csv(scheme_path, skipinitialspace=True)
            
        for path_to_pH in dat_path:
            path = path_to_pH.parent
            print(path)
            run = path.name
            
            ## Find the setup parameter file 
            setup_params_lst = list(working_directory_path.glob(f'**/{run}.csv'))
            if len(setup_params_lst) > 0:
                setup_params_path = setup_params_lst[0]
                df_setup_params = pd.read_csv(setup_params_path, skipinitialspace=True)
                df_setup_params["Stage"] = df_setup_params["Stage"].apply(lambda x: x.replace('Concentrate', 'C'))        
                df_setup_params.set_index("Stage", inplace=True)
            else:
                # handle the case where there is no csv with additional setup data
                df_setup_params = pd.DataFrame()
                df_setup_params["Stage"] = df_scheme["Stage"]
                df_setup_params["Stage"] = df_setup_params["Stage"].apply(lambda x: x.replace('Concentrate', 'C'))    
                df_setup_params.set_index("Stage", inplace=True)

            #list of available measurement data columns
            dat_col_lst = []
            df_lst = []
            for file in ["RTD", "ORP", "LIDAR", "EC", "pH"]:
                if (path/f'{file}.csv').exists():
                    dat_col_lst.append(file)
                    print(path/f'{file}.csv')
                    
                    fs = open (path/f'{file}.csv', "r") 
                    line = fs.readline()
                    cnt = 0
                    while line == fs.readline():
                        cnt += 1                        
                    fs.close()
                    
                    df = pd.read_csv(path/f'{file}.csv', usecols=['Date', 'Time', file, 'StageType', 'StageName'], skiprows=cnt, skipinitialspace=True)
                    df["StageType"] = df["StageType"].apply(lambda x: x.replace('Concentrate', 'C'))
                    df["StageName"] = df["StageName"].apply(lambda x: x.replace('Concentrate', 'C'))
                    df = ImportToDataLakeManager.blings(df)
                    df["timestamp"] = (df["timestamp"]//2)*2 #because the first value of each category will be passed on => timestamp of the first is very close to the actual 
                    df.set_index("timestamp", inplace=True)
                    df_lst.append(df)

            #Merge the dfs such that all df columns and rows are inserted into one huge df that uses the rounded timestampvalue as an index
            df_merge = df_lst.pop()
            while len(df_lst) != 0:
                df_merge = pd.merge(df_merge, df_lst.pop(), left_index=True, right_index=True, how="outer", suffixes=('', '_h'))

            #Select the measurement data columns and the additional columns with no suffixes
            df = df_merge[dat_col_lst]

            #Construct StageType column from the columns provided by pH.csv, RTD.csv, etc ...
            stageType_col_lst = [col for col in df_merge.columns if "StageType" in col]
            df['StageType'] = df_merge[stageType_col_lst].bfill(axis=1)[stageType_col_lst[0]]

            #Construct StageName column from the columns provided by pH.csv, RTD.csv, etc ...
            stageName_col_lst = [col for col in df_merge.columns if "StageName" in col]
            df['StageName'] = df_merge[stageName_col_lst].bfill(axis=1)[stageName_col_lst[0]]

            #Remove multiple rows with the same timestamp by filling up nan values and then taking the first value    
            agg_dict = {k: lambda x: x.bfill().iloc[0] for k in dat_col_lst}
            agg_dict.update({
                "StageType": lambda x: x.iloc[0],
                "StageName": lambda x: x.iloc[0]
            })
            df_data = df.groupby(df.index).agg(agg_dict)
            
            #df_data has rounded timestamp as index
            timestamp_data_arr = np.array(list(df_data.index))

            ## Search for images
            timestamp_lst = []
            img_name_lst = []
            # Define a defaultdict where each new key defaults to an empty list
            timestamp_int_to_img_tupel_map = defaultdict(list)
            for img_path in sorted(path.glob('???????*.png')):
                #somtimes CAM2_ is appended to the image files indicating a high resolution image
                split_tpl = img_path.stem.split('_')
                #timestamp_str = split_tpl[-2] 
                timestamp_str = split_tpl[0]
                timestamp = ImportToDataLakeManager.convertStrToTimestampInSeconds(timestamp_str)
                img_name_lst.append(img_path.name)
                timestamp_lst.append(timestamp)

                #find the best match of image and data timestampwise
                ind_best_match = np.argmin(np.abs(timestamp_data_arr - timestamp))
                timestamp_best_match = timestamp_data_arr[ind_best_match]

                #construct map from timestamp of data dataframe to timestamp of image
                timestamp_int_to_img_tupel_map[timestamp_best_match].append((timestamp, img_path.name))

            if len(timestamp_data_arr) > 0:
                for ts, ts_next in zip(timestamp_data_arr, np.append(timestamp_data_arr[1:], timestamp_data_arr[-1])):
                    #Prepare the data        
                    data = {"timestamp" : None, "ORP" : None, "pH" : None, "EC" : None, "RTD" : None, "LIDAR" : None}
                    data["timestamp"] = round(ts*1000)
                    for dat_col in dat_col_lst:
                        data[dat_col] = df_data.loc[ts, dat_col]

                    setup_config = {}
                    
                    stage_name = df_data.loc[ts, "StageName"]
                    setup_state = {"stage_type" : df_data.loc[ts, "StageType"]}
                    setup_params = df_setup_params.loc[stage_name].to_dict()
                    setup_state.update(setup_params)
                            
                    # check for available images by checking if there is a mapping between the timestamps and the images
                    if ts in timestamp_int_to_img_tupel_map.keys():
                        ## update the metadata
                        #for avoiding wrong assignment of the StageType and Stage name to the image ... usually images are taken in the flotation stage
                        if  df_data["StageType"].loc[ts] != "Flotation": 
                            stage_name = df_data.loc[ts_next, "StageName"]
                            setup_state = {"stage_type" : df_data.loc[ts_next, "StageType"]}
                            setup_params = df_setup_params.loc[stage_name].dropna().to_dict()                
                            setup_state.update(setup_params)

                        for tupel in timestamp_int_to_img_tupel_map[ts]:
                            ts_img = tupel[0]
                            imagename = tupel[1]
                            
                            ## update the data
                            #override the timestamp value with the more exact one of the image
                            data["timestamp"] = round(ts_img*1000)
                            
                            ##read the image
                            with open(path/imagename, "rb") as file:
                                img_bytes = file.read()
                            image_str = f"{base64.b64encode(img_bytes)}" [2:-1] #remove leading b' and tailing '
                            self.sendOffData(
                                timestamp=data["timestamp"], \
                                ORP = data["ORP"], \
                                pH = data["pH"], \
                                EC = data["EC"], \
                                RTD = data["RTD"], \
                                LIDAR = data["LIDAR"], \
                                project = project, \
                                run = run, \
                                stage_name = stage_name, \
                                setup_state = setup_state, \
                                setup_config = setup_config, \
                                hardware_state = None, \
                                hardware_config = None, \
                                software_state = None, \
                                software_config = None, \
                                image_top_view = image_str, \
                                image_side_view = None, \
                                protocol = protocol
                            )
                    else:
                        self.sendOffData(
                            timestamp=data["timestamp"], \
                            ORP = data["ORP"], \
                            pH = data["pH"], \
                            EC = data["EC"], \
                            RTD = data["RTD"], \
                            LIDAR = data["LIDAR"], \
                            project = project, \
                            run = run, \
                            stage_name = stage_name, \
                            setup_state = setup_state, \
                            setup_config = setup_config, \
                            hardware_state = None, \
                            hardware_config = None, \
                            software_state = None, \
                            software_config = None, \
                            image_top_view = None, \
                            image_side_view = None, \
                            protocol = protocol
                        )
            else:
                print(f"No data extractable from the csv files in {path}")

    def sendOffData(self, timestamp=0, ORP=0.0, pH=0.0, EC=0.0, RTD=0.0, LIDAR=0.0, project="", run="", stage_name="", setup_state=None, setup_config=None, hardware_state=None, hardware_config=None, software_state=None, software_config=None, image_top_view="", image_side_view="", protocol="MQTT"):
        params = [str(pd.to_datetime(timestamp, unit="ms") + pd.Timedelta(hours=2)), ORP, pH, EC, RTD, LIDAR, project, run, stage_name, setup_state, setup_config, hardware_state, hardware_config, software_state, software_config, image_top_view, image_side_view]
        for i, par in enumerate(params):
            if par is None or pd.isna(par):
                params[i] = ""
            elif isinstance(par, dict):
                #check if the entries of the dict are nan or None or whatever and remove them
                rm_lst = []
                for k,v in par.items():
                    if v is None or pd.isna(v):
                        rm_lst.append(k)
                for k in rm_lst:
                    par.pop(k)
                #check if the dictionary is empty ...
                if len(par) > 0:
                    params[i] = json.dumps(par, allow_nan=True)         
                else:
                    params[i] = ""
            elif not isinstance(par, str):
                #int64 not json serializable
                if isinstance(par, np.int64):
                    par = float(par)
                params[i] = json.dumps(par, allow_nan=True)
    
        #Join to result string and publish
        res_str = '&'.join(params) #+ '\n'
        if protocol == "MQTT" and self.mqttInterface is not None:
            self.mqttInterface.publish(res_str)
        elif protocol == "kafka" and self.producer is not None:
            self.producer.send("lab_assistant_live_data", res_str.encode())

        #control rate
        target_rate = 10 #MiB/s
        target_rate *= 2**20 #MiB/s -> B/s
        sleep_time = len(res_str)/target_rate
        time.sleep(sleep_time)

        #output short version to terminal
        print('&'.join(params[:-2]))
        self.cnt +=1
        print(self.cnt)

if __name__ == "__main__":
    pass
    #collectData()
