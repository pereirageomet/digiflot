from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFormLayout, QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)

try:
    from libs.mqttInterface import MqttInterface
    from libs import eventManager
    from libs import configurationManager  
except:
    from .mqttInterface import MqttInterface
    from . import eventManager
    from . import configurationManager  

import time
from datetime import datetime, timezone
import pandas as pd
import json
import logging
logger = logging.getLogger(__name__)
class TabViewInformation(QWidget):
    def __init__(self, taskModel, lidar):
        super().__init__()

        self.taskModel = taskModel
        self.lidar = lidar

        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout()

        # Initial information
        initial_info_group = QGroupBox("Initial information")
        initial_info_layout = QFormLayout()
        self.sample_mass = QLineEdit()
        self.flotation_cell_weight = QLineEdit()
        self.flotation_cell_water_sample = QLineEdit()
        self.lidar_distance = QLineEdit()
        self.lidar_distance.setVisible(self.lidar.showLIDAR)
        
        initial_info_layout.addRow("Sample mass", self.sample_mass)
        initial_info_layout.addRow("Flotation cell weight", self.flotation_cell_weight)
        initial_info_layout.addRow("Flotation cell + water + sample", self.flotation_cell_water_sample)
        initial_info_layout.addRow("Distance between LiDAR and top of the flotation cell", self.lidar_distance)
        initial_info_layout.itemAt(6).widget().setVisible(self.lidar.showLIDAR)
        initial_info_group.setLayout(initial_info_layout)

        # Water usage
        water_usage_group = QGroupBox("Water usage")
        water_usage_layout = QHBoxLayout()

        self.df_waterUsage = pd.DataFrame({"Water bottle names" : [f"Bottle {i}" for i in range(1,7)], "Initial mass" : ["" for i in range(1,7)], "Final mass" : ["" for i in range(1,7)]})
        self.table_waterusage = TabViewInformation.generateTableWidgetFromDataframe(self.df_waterUsage)
        water_usage_layout.addWidget(self.table_waterusage)
        water_usage_group.setLayout(water_usage_layout)

        # Flotation products
        flotation_products_group = QGroupBox("Flotation products")
        self.flotation_products_layout = QHBoxLayout()

        col_list = [f"Conc{i}" for i in range(1, self.taskModel.nconc + 1)] + ["Tails"]
        self.df_flotationProducts = pd.DataFrame({"Tray mass" : col_list, "Filter mass" : col_list, "Mass: sample+tray+water" : col_list, "Mass: filter+sample" : col_list})
        self.table_floationProducts = TabViewInformation.generateTableWidgetFromDataframe(self.df_flotationProducts)
        self.flotation_products_layout.addWidget(self.table_floationProducts)
        flotation_products_group.setLayout(self.flotation_products_layout)

        # Observations
        observations_group = QGroupBox("Observations")
        observations_layout = QVBoxLayout()
        self.observations = QLineEdit()
        self.export_button = QPushButton("Export information")
        eventManager.registerEvent("exportButtonClicked", self.export_button.clicked)

        observations_layout.addWidget(self.observations)
        observations_layout.addWidget(self.export_button)
        observations_group.setLayout(observations_layout)

        mainLayout.addWidget(initial_info_group)
        mainLayout.addWidget(water_usage_group)
        mainLayout.addWidget(flotation_products_group)
        mainLayout.addWidget(observations_group)

        self.setLayout(mainLayout)

    @staticmethod
    def generateTableWidgetFromDataframe(df):
        tableWidget = QTableWidget()
        tableWidget.setColumnCount(len(df.columns))
        tableWidget.setHorizontalHeaderLabels(df.columns)
        tableWidget.setRowCount(len(df))
        TabViewInformation.updateTableWidgetFromDataframe(df, tableWidget)
        return tableWidget

    @staticmethod
    def updateTableWidgetFromDataframe(df, tableWidget_target):
        for i, row in enumerate(df.values):
            for j, val in enumerate(row):
                tableWidget_target.setItem(i, j, QTableWidgetItem(str(val)))
        #Strech the columns
        header=tableWidget_target.horizontalHeader()
        for j, _ in enumerate(df.columns):
            header.setSectionResizeMode(j, QHeaderView.Stretch)
        #Strech the rows
        header = tableWidget_target.verticalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    @staticmethod
    def loadDataIntoDataFrameFromTableWidget(tableWidget, df_target):
        #Assumption: tableWidget is based on df schema
        number_of_rows = tableWidget.rowCount()
        for i in range(number_of_rows):
            for j, column in enumerate(df_target.columns):
                tmp_item = tableWidget.item(i,j)
                df_target.loc[i, column] = tmp_item.data(0)

    def resetInformationTab(self):
        self.sample_mass.setText("")
        self.flotation_cell_weight.setText("")
        self.flotation_cell_water_sample.setText("")
        self.lidar_distance.setText("")
        self.observations.setText("")  
        self.reloadTablesForNewSetup()

    def reloadTablesForNewSetup(self):
        # Reset water usage table
        self.df_waterUsage = pd.DataFrame({"Water bottle names" : [f"Bottle {i}" for i in range(1,7)], "Initial mass" : ["" for i in range(1,7)], "Final mass" : ["" for i in range(1,7)]})
        TabViewInformation.updateTableWidgetFromDataframe(self.df_waterUsage, self.table_waterusage)            
        # reinstantiate flotation products table
        col_list = [f"Conc{i}" for i in range(1, self.taskModel.nconc + 1)] + ["Tails"]
        self.df_flotationProducts = pd.DataFrame({"Tray mass" : col_list, "Filter mass" : col_list, "Mass: sample+tray+water" : col_list, "Mass: filter+sample" : col_list})
        #delete original table
        self.flotation_products_layout.removeWidget(self.table_floationProducts)
        self.table_floationProducts = TabViewInformation.generateTableWidgetFromDataframe(self.df_flotationProducts)
        self.flotation_products_layout.addWidget(self.table_floationProducts)

    def exportInformation(self):
        def showWarningPopup(msg):
            msg_box = QMessageBox()
            msg_box.setText(msg)
            msg_box.setWindowTitle("Warning")
            msg_box.setStandardButtons(QMessageBox.Cancel)
            msg_box.exec_()
        try:
            if self.taskModel.samplefolder is None or self.taskModel.selectedSample is None: #this is to avoid cases in which the student has not yet selected a sample and try to export data
                raise Exception
        except:
            success = False
            showWarningPopup('You have to first define a work folder, select a sample, and click -OK- before trying to export data')        
        else: 
            success = True
            Initialdata = pd.DataFrame({ #collect general data
                "SampleMass":[self.sample_mass.text()],
                "CellWeight":[self.flotation_cell_weight.text()],
                "Cell+Sample+Water":[self.flotation_cell_water_sample.text()],
                "LidarToCell":[self.lidar_distance.text()],
                "Observations":[self.observations.text()]
            })    

            # offline storage 
            Initialdata = Initialdata.replace(",",".",regex = True)
            Initialdata.to_csv(self.taskModel.samplefolder / (self.taskModel.selectedSample + "INIT.csv"), index=False)
            
            TabViewInformation.loadDataIntoDataFrameFromTableWidget(self.table_floationProducts, self.df_flotationProducts)
            productsdata = self.df_flotationProducts
            productsdata = productsdata.replace(",",".",regex = True) #substitute all commas by points to avoid breaking CSVs
            productsdata.to_csv(self.taskModel.samplefolder / (self.taskModel.selectedSample + "PRODS.csv"), index=False) # save CSVs
            
            TabViewInformation.loadDataIntoDataFrameFromTableWidget(self.table_waterusage, self.df_waterUsage)
            waterdata = self.df_waterUsage
            waterdata = waterdata.replace(",",".",regex = True)
            waterdata.to_csv(self.taskModel.samplefolder / (self.taskModel.selectedSample + "WATER.csv" ), index=False)

            # online storage
            ret = {}
            ret["InitialData"] = Initialdata.to_dict('split')
            ret["ProductsData"] = productsdata.to_dict('split') 
            ret["WaterData"] = waterdata.to_dict('split') 

            #get the timestamp
            unix_timestamp_sec = time.time()
            datetime_obj = datetime.fromtimestamp(unix_timestamp_sec).astimezone(timezone.utc)
            timestamp = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            #get the start timestamp
            timestamp_start = self.taskModel.getStartTimestamp()
            
            #get the project id
            conf = configurationManager.getConfig("MainWindow")
            project = conf["project"]
            #get the run id
            run = self.taskModel.selectedSample

            #Order relevant data (as a string) in a list
            data_spark = [timestamp, timestamp_start, project, run, json.dumps(ret)]
            #Concatenate list to a spark readable string
            spark_str = '&'.join(data_spark)

            configuration = configurationManager.getConfig("TabViewInformation")
            mqttInterface = TabViewInformation.connectToMqtt(**configuration)
            if mqttInterface is not None:
                mqttInterface.publish(spark_str)
                TabViewInformation.disconnectFromMqtt(mqttInterface)

        return success

    @staticmethod
    def connectToMqtt(broker, port, topic_sub, topic_pub, username, password, **kwargs):
        try:
            mqttInterface = MqttInterface(broker, port, topic_sub, topic_pub, username, password)
            mqttInterface.connectMqtt()
            mqttInterface.client.loop_start()
        except:
            mqttInterface = None
            logger.error(f"Error when connecting to mqtt broker. Passed values: {broker}, {port}, {topic_sub}, {topic_pub}, {username}, {password}, {kwargs}")
        return mqttInterface

    @staticmethod
    def disconnectFromMqtt(mqttInterface):
        try:
            mqttInterface.client.loop_stop()
            mqttInterface.client.disconnect()
        except:
            logger.error("Error when disconnecting from mqtt broker.")
