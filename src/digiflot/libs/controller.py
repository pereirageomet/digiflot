import time
import logging
logger = logging.getLogger(__name__)

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

try:
    from libs import vlcBeepAndSkim
    from libs import eventManager
    ##ConfigurationManager
    from libs import configurationManager  
except:
    from . import vlcBeepAndSkim
    from . import eventManager
    ##ConfigurationManager
    from . import configurationManager  
class Controller():
    def __init__(self, tabWidget, camAdapter, atlasSensor, lidar, bronkhorstFlowControlModel, taskModel, deviceDictionary, tabViewSetup, tabViewRun, tabViewInformation, tabViewRestartExit, tabViewCalibCam, tabViewCalibLidar, tabViewCalibSensors, tabViewBronkhorstFlowControl, imageStorage, dataForwarder): #sewControl,  removed due to issues
        self.configuration = configurationManager.getConfig("Controller")
        #mainWindow in the role of a tabWidget
        self.tabWidget = tabWidget        
        #device interfaces
        self.camAdapter = camAdapter
        self.atlasSensor = atlasSensor
        self.lidar = lidar
        self.bronkhorstFlowControlModel = bronkhorstFlowControlModel
        # self.sewControl = sewControl # removed for now
        #Model
        self.taskModel = taskModel
        #device dictionary for querying devices via wrapper
        self.deviceDictionary = deviceDictionary
        #tab views
        self.tabViewSetup = tabViewSetup
        self.tabViewRun = tabViewRun
        self.tabViewInformation = tabViewInformation
        self.tabViewRestartExit = tabViewRestartExit
        self.tabViewCalibCam = tabViewCalibCam
        self.tabViewCalibLidar = tabViewCalibLidar
        self.tabViewCalibSensors = tabViewCalibSensors
        self.tabViewBronkhorstFlowControl = tabViewBronkhorstFlowControl
        #offline acquisition
        self.imageStorage = imageStorage        
        #online acquisition
        self.dataForwarder = dataForwarder
        #Timing objects
        self.run_timer = QTimer()
        self.run_timer.timeout.connect(self.handleRunningStatus)
        self.fetch_measurement_timer = QTimer()
        self.fetch_measurement_timer.timeout.connect(self.handleFetchMeasurementEvent)
        self.fetch_measurement_timer.start(self.configuration["measurement timer"]) #ms
        self.calib_cam_timer = QTimer()
        self.calib_cam_timer.timeout.connect(self.handleUpdateCalibCamEvent)                        

        # Connect controller methods to tab view events
        eventManager.connectToEvent("okButtonClicked", self.handleOkButtonPressed)        
        eventManager.connectToEvent("workingFolderButtonClicked", self.handleWorkingFolderButtonClicked)        
        eventManager.connectToEvent("startButtonClicked", self.handleStartButtonClicked)        
        eventManager.connectToEvent("pauseButtonClicked", self.handlePauseButtonClicked)        
        eventManager.connectToEvent("nextStageButtonClicked", self.handleNextStageButtonClicked)        
        eventManager.connectToEvent("previousStageButtonClicked", self.handlePreviousStageButtonClicked)        
        eventManager.connectToEvent("restartButtonClicked", self.handleRestartButtonClicked)        
        eventManager.connectToEvent("taskModelStatusHasChanged", self.handleTaskModelStatusHasChanged)
        eventManager.connectToEvent("tabChanged", self.handleTabHasChanged)        
        eventManager.connectToEvent("exportButtonClicked", self.handleExportInformationEvent)        

    def showWarningPopup(self, msg):
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle("Warning")
        msg_box.setStandardButtons(QMessageBox.Cancel)
        msg_box.exec_()

    def handleOkButtonPressed(self):
        currentRowIndex = self.tabViewSetup.sampleList.currentRow()
        self.taskModel.selectedSample = self.tabViewSetup.sampleList.item(currentRowIndex).text()
        msg = self.taskModel.tryToLoadSchemeSampleAndCreateSampleFolder()
        if msg is not None:
            logger.warning(msg)
            self.showWarningPopup(msg)
        else:
            #No error msg => Display
            self.taskModel.markStart()
            self.tabWidget.setTabVisible(1, True)
            self.tabViewSetup.okButton.setEnabled(False)     
            self.tabViewSetup.displaySampleScheme()
            self.tabViewRun.displayMeasurementParameters()
            self.tabViewInformation.reloadTablesForNewSetup()

    def handleWorkingFolderButtonClicked(self):
        #Issue: Reset of runTask at this point?
        self.tabViewSetup.workingFolderButtonClicked()
        self.tabViewRun.displayTargetTimeAndStages()

        # update configuration after path has been updated/initialized
        configurationManager.updateSharedConfiguration(self.taskModel.workingfolder)
        self.tabViewCalibCam.resetTabWidgets()

    def handleStartButtonClicked(self):
        self.tabViewRun.startClicked()
        self.activateCalibrationTabs(False)

    def handlePauseButtonClicked(self):
        self.taskModel.status = "PAUSED"
        self.taskModel.adjustForTimeSpentInCurrentStage()
        self.tabViewRun.updateToPausedStatus()
        vlcBeepAndSkim.interruptSkim()

    def handleNextStageButtonClicked(self):
        response = QMessageBox.question(None, 'Confirmation', 'Are you sure?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:
            self.taskModel.status = "PAUSED"
            self.tabViewRun.updateToPausedStatus()
            self.taskModel.moveToNextStage()
            self.tabViewRun.updateWholeRunTabToCurrentStage()                

    def handlePreviousStageButtonClicked(self):
        response = QMessageBox.question(None, 'Confirmation', 'Are you sure?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:            
            self.taskModel.status = "PAUSED"
            self.tabViewRun.updateToPausedStatus()
            self.taskModel.moveToPreviousStage()
            self.tabViewRun.updateWholeRunTabToCurrentStage()

    def handleRestartButtonClicked(self):
        response = QMessageBox.question(None, 'Confirmation', 'Move on to the next run?',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if response == QMessageBox.StandardButton.Yes:            
            self.performRestart()

    def performRestart(self):
        # Restart reloads samples.csv, but stores the previously selected sample. The scheme.csv is not reloaded. It also does not clear the data of the info tab.
        self.taskModel.status = "PAUSED"
        #Stop all timers linked to the running status
        self.run_timer.stop()
        self.tabViewRun.updateToPausedStatus()
        self.taskModel.moveToFirstStage()
        self.tabViewRun.updateWholeRunTabToCurrentStage()
        
        #Reload samples.csv and display it
        msg = self.taskModel.tryToLoadSampleFile()
        if msg is not None:
            logger.warning(msg)
            self.showWarningPopup(msg)
        self.tabViewSetup.displaySchemeAndSamplenames()

        #bring back the okButton
        self.tabViewSetup.okButton.setEnabled(True)        
        #reset information tab
        self.tabViewInformation.resetInformationTab()

        #move to setup tab and show all the others except for the run tab
        self.tabWidget.setCurrentIndex(0)
        for index in range(self.tabWidget.count()):
            if self.tabWidget.tabText(index) != "Run":
                self.tabWidget.setTabVisible(index, True)
            else:
                self.tabWidget.setTabVisible(index, False)

        #Reset skim and beep handling
        vlcBeepAndSkim.interruptSkim()
        vlcBeepAndSkim.resetSkimAndBeep()

        #Reset pulp level
        self.lidar.pulp = 0

        # Bring back the tabs for the cam and the lidar
        self.activateCalibrationTabs(True)

    def activateCalibrationTabs(self, enabled):
            try:
                self.tabWidget.setTabEnabled(5, enabled)
            except:
                logger.error("Tab with index 5 does not exist.")
            else:
                try:
                    self.tabWidget.setTabEnabled(6, enabled)
                except:
                    logger.error(f"Tab with index 6 does not exist. Last defined tab is {self.tabWidget.tabText(5)}.")

    def handleFetchMeasurementEvent(self):
        ###DATA COLLECTON
        for dev_name, dev_handle in self.deviceDictionary.items():
            try:
                dev_handle.updateMeasuredValue()
            except ValueError:
                logger.error("Invalid value from atlas sensor.")

            self.tabViewRun.displayMeasuredValueAndCheckForTolerance('-'+dev_name+'-', dev_handle)                    
            if self.taskModel.status == "RUNNING":
                self.taskModel.dumpValue(dev_name, dev_handle.getMeasuredValue())

        # fetch value from Bronkhorst
        self.bronkhorstFlowControlModel.fetchAirFlow()

        # fetch value from Bronkhorst
        # self.sewControl.fetchRotorSpeed()  # removed for now

        # data storage
        if self.taskModel.status == "RUNNING":
            if self.taskModel.currentstagetype == 'Flotation':
                #Store last fetched image locally if stagetype is Flotation
                self.imageStorage.saveImageOffline()
                #Push data to datalake with image included
                self.dataForwarder.pushDataToDataLake(images_included=True)
            else:
                #Push data to datalake without any images
                self.dataForwarder.pushDataToDataLake(images_included=False)

        # update display of values (refresh of camera tab is handled by timer)
        self.tabViewCalibLidar.updateLidarDisplay()
        self.tabViewCalibSensors.updateSensorOutputLabel()
        self.tabViewBronkhorstFlowControl.updateAirFlowLabel()

    def handleRunningStatus(self):
        #Clocking the time spent in current stage
        self.taskModel.updateTimeSpentInCurrentStage()
        remainingTimeInStage = self.taskModel.calculateRemainingTimeInCurrentStage()
        self.tabViewRun.displayRemainingTime(remainingTimeInStage, beepFlag=True)

        #Clocking the time spent in stage flotation 
        if (self.taskModel.currentstagetype == 'Flotation'):
            self.taskModel.flotationtime = time.time() - self.taskModel.t1flot + self.taskModel.t2flot
            vlcBeepAndSkim.skimOnce(targett= int(self.taskModel.targett),scrapingFreq=5)

        #What to do when time in current stage is used up 
        if remainingTimeInStage <= 0.0:
            if (self.taskModel.currentstage + 1) <= self.taskModel.nstages:
                self.taskModel.moveToNextStage()
                target_air_flow = self.taskModel.getTargetAirFlowRate()
                self.bronkhorstFlowControlModel.setAirFlow(target_air_flow)
                vlcBeepAndSkim.resetSkimAndBeep()
                if self.taskModel.stageTypeHasChanged():
                    self.taskModel.status = "PAUSED"
                    self.tabViewRun.updateToPausedStatus()
                self.tabViewRun.updateWholeRunTabToCurrentStage()
            else:
                self.taskModel.status = "Completed"
                self.taskModel.updateSamplesFile()
                self.tabViewRun.displayMeasurementCompleted()
                vlcBeepAndSkim.playFinish()
                #store config to samplefolder
                try:
                    configurationManager.storeJsonToPath(self.taskModel.samplefolder)
                except:
                    logger.error(f"Could not write to {str(self.taskModel.samplefolder/'configuration.json')}, probably because the file was in use or the sample folder not existent.")            
                #move to information tab and hide all the others
                self.tabWidget.setCurrentIndex(2)
                for index in range(self.tabWidget.count()):
                    if self.tabWidget.tabText(index) != "Information":
                        self.tabWidget.setTabVisible(index, False)

    def handleTabHasChanged(self, index):
        if self.tabWidget.tabText(index) == "Calibrate camera":
            self.calib_cam_timer.start(self.configuration["camera tab timer"]) #ms        
        else:
            self.calib_cam_timer.stop()      

    def handleTaskModelStatusHasChanged(self):
        if self.taskModel.status == "RUNNING":
            self.run_timer.start(self.configuration["run tab timer"]) #ms
            target_air_flow = self.taskModel.getTargetAirFlowRate()
            self.bronkhorstFlowControlModel.setAirFlow(target_air_flow)
        else:
            self.run_timer.stop()
            self.bronkhorstFlowControlModel.setAirFlow(0.0)

    def handleUpdateCalibCamEvent(self):
        self.tabViewCalibCam.updateCalibCamImage()

    def handleExportInformationEvent(self):
        success = self.tabViewInformation.exportInformation()
        # Restart if export information button has been successfully used after successfull run
        if success and self.taskModel.status == "Completed":
            self.performRestart()
