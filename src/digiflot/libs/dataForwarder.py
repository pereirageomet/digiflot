import time
import multiprocessing as mp
from datetime import datetime, timezone
try:
    from libs import dataForwarderSubProcess
    ##ConfigurationManager
    from libs import configurationManager  
except:
    from . import dataForwarderSubProcess
    ##ConfigurationManager
    from . import configurationManager  

class DataForwarder():
    def __init__(self, taskModel, camInstance, controller):
        self.configuration = configurationManager.getConfig("DataForwarder")
        self.taskModel = taskModel
        self.camInstance = camInstance
        self.controller = controller
        self._process_handle = None
        self._insights_queue = None
        self._message_queue = None        
    #setter
    def setController(self, controller):
        self.controller = controller

    #getter
    def getBroker(self):
        return self.configuration["broker"]

    #getter
    def getPort(self):
        return self.configuration["port"]

    #getter
    def getUsername(self):
        return self.configuration["username"]

    #getter
    def getPassword(self):
        return self.configuration["password"]

    #getter
    def getTopic_pub(self):
        return self.configuration["topic_pub"]

    def __del__(self):
        if self._process_handle is not None:
            self._process_handle.join(timeout=10)  # Wait for 10 seconds
            if self._process_handle.is_alive():
                print("Process is taking too long. Terminating...")
                self._process_handle.terminate()
                self._process_handle.join()    

    def pushDataToDataLake(self, images_included):
        if self.isRunning():
            insights_dct = self.collectInsights(images_included)
            self._insights_queue.put(insights_dct)

    # Collecting data from the software
    def collectInsights(self, images_included=True):
        data = self.collectMeasurementData()
        data = self.filterDictForDataLakeDataColumns(data)
        conf_dct = configurationManager.convertSharedConfigtoSerializableDict()
        semi = self.taskModel.provideSemiStructuredData()
        #if images_included:
        #    img_bytes = self.fetchImageBytes()
        #else: 
        #    img_bytes = b""
        #return {"sensor_data": data, "image_top_view": img_bytes, "image_side_view": b"", "model_data_JSON": semi, "configuration" : conf_dct} 
        return {"sensor_data": data,  "model_data_JSON": semi, "configuration" : conf_dct, "images_included": images_included} 

    def collectMeasurementData(self):
        # generation of timestamp = point of time of query
        unix_timestamp_sec = time.time()
        datetime_obj = datetime.fromtimestamp(unix_timestamp_sec).astimezone(timezone.utc)
        formatted_timestamp = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        data_dict = {"timestamp": formatted_timestamp}
        for dev_name, dev_handle in self.controller.deviceDictionary.items():
            # get the last fetched values for each device
            data_dict[dev_name] = dev_handle.getMeasuredValue()
        return data_dict

    def filterDictForDataLakeDataColumns(self, dct):
        ret = {"timestamp" : None, "ORP" : None, "pH" : None, "RTD" : None, "EC" : None, "LIDAR" : None}
        for k in ret.keys():
            try:
                ret[k] = dct[k]
            except:
                pass
        return ret

    def fetchImageBytes(self):
        _, img_bytes = self.camInstance.getLatestImage(image_format= "TIFF")
        if img_bytes is None:
            img_bytes = b""
        return img_bytes

    # StreamProcessHandling
    def reconnectStreamToMqttBroker(self, broker="10.20.30.40", port = 1212, topic_sub="Server/Sub", topic_pub="topic", username="PASS", password="PASS"):
        if self.isRunning():
            self._message_queue.put({"message" : "LOAD", "broker" : broker, "port" : port, "topic_sub" : topic_sub, "topic_pub" : topic_pub, "username" : username, "password" : password})
        else:
            #update configuration, if it is not running
            self.configuration["broker"] = broker
            self.configuration["port"] = port
            self.configuration["topic_sub"] =topic_sub
            self.configuration["topic_pub"] = topic_pub
            self.configuration["username"] = username
            self.configuration["password"] = password

    def finishProcessesAndQueues(self):
        if self.isRunning():
            time.sleep(0.2)        
            self._message_queue.put("FINISH") 
            time.sleep(0.2)
            DataForwarder.requestQueueClosure(self._message_queue, "CLOSE_MESSAGE_QUEUE")
            time.sleep(0.2)
            DataForwarder.requestQueueClosure(self._insights_queue, "CLOSE_INSIGHTS_QUEUE")

            self._process_handle.join(timeout=10)  # Wait for 1 second
            if self._process_handle.is_alive():
                print("Process is taking too long. Terminating...")
                self._process_handle.terminate()
                self._process_handle.join()   
            self._process_handle = None

    @staticmethod
    def requestQueueClosure(queue, sentinel_message):
        queue.put(sentinel_message)
        queue.close()
        queue.join_thread()

    def startDataForwarderService(self):
        imageHeight, imageWidth, nof_pixel_values = self.camInstance.getImageParameters()
        self._insights_queue = mp.Queue()
        self._message_queue = mp.Queue()
        self._process_handle = mp.Process(target=dataForwarderSubProcess.startDataForwarderLoop, args=(self._insights_queue, self.camInstance.image_array, imageHeight, imageWidth, nof_pixel_values, self._message_queue, self.configuration))
        self._process_handle.start()

    def terminateForwarderService(self):
          if self.isRunning():
            self._process_handle.terminate()
            self._process_handle.join()    

    def isRunning(self):
        return self._process_handle is not None and self._process_handle.is_alive()
