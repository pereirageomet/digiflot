"""
Controller module for the Digiflot process monitoring system.

This module provides the central Controller class that manages the interaction
between all hardware components (cameras, sensors, flow controllers), the task model,
and the UI tabs. It handles data acquisition timing, stage transitions, and system
state management.
"""
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
    """
    Central controller managing hardware components and process state.

    This class acts as the central coordination point between all hardware interfaces,
    the task model (process flow), and UI tab views. It manages timing for data
    acquisition, handles stage transitions, and coordinates the flow of the
    flotation experiment.

    Attributes:
        configuration: Controller configuration from shared configuration
        tabWidget: Main window tab widget for UI navigation
        camAdapter: Camera adapter instance for image acquisition
        atlasSensor: Atlas sensor interface for pH, EC, RTD, ORP measurements
        lidar: LIDAR sensor interface for pulp level measurement
        bronkhorstFlowControlModel: Bronkhorst flow controller interface
        taskModel: Process task model managing stages and timing
        deviceDictionary: Dictionary mapping device names to device handles
        tabViewSetup: Setup tab view instance
        tabViewRun: Run tab view instance
        tabViewInformation: Information tab view instance
        tabViewRestartExit: Restart/Exit tab view instance
        tabViewCalibCam: Camera calibration tab view instance
        tabViewCalibLidar: LIDAR calibration tab view instance
        tabViewCalibSensors: Sensor calibration tab view instance
        tabViewBronkhorstFlowControl: Flow control tab view instance
        imageStorage: Offline image storage manager
        dataForwarder: Online data forwarding manager
        run_timer: Timer for running status updates
        fetch_measurement_timer: Timer for periodic measurement collection
        calib_cam_timer: Timer for camera calibration updates
    """
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
        """
        Display a warning message popup to the user.

        Args:
            msg (str): The warning message to display
        """
        msg_box = QMessageBox()
        msg_box.setText(msg)
        msg_box.setWindowTitle("Warning")
        msg_box.setStandardButtons(QMessageBox.Cancel)
        msg_box.exec_()

    def handleOkButtonPressed(self):
        """
        Handle OK button click to start a new measurement run.

        Loads the selected sample, creates the sample folder, and initializes
        the measurement run by updating UI visibility and displaying measurement
        parameters.
        """
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
        """
        Handle working folder button click to set the working directory.

        Updates the working folder configuration, resets calibration tabs,
        and updates the run tab display with target times and stages.
        """
        #Issue: Reset of runTask at this point?
        self.tabViewSetup.workingFolderButtonClicked()
        self.tabViewRun.displayTargetTimeAndStages()

        # update configuration after path has been updated/initialized
        configurationManager.updateSharedConfiguration(self.taskModel.workingfolder)
        self.tabViewCalibCam.resetTabWidgets()

    def handleStartButtonClicked(self):
        """
        Handle start button click to begin the measurement run.

        Triggers the run tab start action and disables calibration tabs.
        """
        self.tabViewRun.startClicked()
        self.activateCalibrationTabs(False)

    def handlePauseButtonClicked(self):
        """
        Handle pause button click to pause the current measurement stage.

        Updates task model status to PAUSED, adjusts time tracking, updates
        the run tab UI, and interrupts any audio prompts.
        """
        self.taskModel.status = "PAUSED"
        self.taskModel.adjustForTimeSpentInCurrentStage()
        self.tabViewRun.updateToPausedStatus()
        vlcBeepAndSkim.interruptSkim()

    def handleNextStageButtonClicked(self):
        """
        Handle next stage button click to advance to the next measurement stage.

        Shows confirmation dialog before proceeding. If confirmed, pauses the
        current stage, advances to the next stage in the run scheme, and updates
        the run tab display.
        """
        response = QMessageBox.question(None, 'Confirmation', 'Are you sure?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:
            self.taskModel.status = "PAUSED"
            self.tabViewRun.updateToPausedStatus()
            self.taskModel.moveToNextStage()
            self.tabViewRun.updateWholeRunTabToCurrentStage()                

    def handlePreviousStageButtonClicked(self):
        """
        Handle previous stage button click to return to the previous measurement stage.

        Shows confirmation dialog before proceeding. If confirmed, pauses the
        current stage, moves to the previous stage in the run scheme, and updates
        the run tab display.
        """
        response = QMessageBox.question(None, 'Confirmation', 'Are you sure?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:            
            self.taskModel.status = "PAUSED"
            self.tabViewRun.updateToPausedStatus()
            self.taskModel.moveToPreviousStage()
            self.tabViewRun.updateWholeRunTabToCurrentStage()

    def handleRestartButtonClicked(self):
        """
        Handle restart button click to restart the current sample measurement.

        Shows confirmation dialog before proceeding. If confirmed, performs a
        restart operation that reloads sample data and resets the run state.
        """
        response = QMessageBox.question(None, 'Confirmation', 'Move on to the next run?',
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if response == QMessageBox.StandardButton.Yes:            
            self.performRestart()

    def performRestart(self):
        """
        Perform the restart operation for the current sample.

        Reloads samples.csv, resets timing, updates UI visibility, resets
        skim and beep handling, and resets LIDAR pulp level measurement.
        """
        self.taskModel.status = "PAUSED"
        self.run_timer.stop()
        self.tabViewRun.updateToPausedStatus()
        self.taskModel.moveToFirstStage()
        self.tabViewRun.updateWholeRunTabToCurrentStage()
        
        msg = self.taskModel.tryToLoadSampleFile()
        if msg is not None:
            logger.warning(msg)
            self.showWarningPopup(msg)
        self.tabViewSetup.displaySchemeAndSamplenames()

        self.tabViewSetup.okButton.setEnabled(True)        
        self.tabViewInformation.resetInformationTab()

        self.tabWidget.setCurrentIndex(0)
        for index in range(self.tabWidget.count()):
            if self.tabWidget.tabText(index) != "Run":
                self.tabWidget.setTabVisible(index, True)
            else:
                self.tabWidget.setTabVisible(index, False)

        vlcBeepAndSkim.interruptSkim()
        vlcBeepAndSkim.resetSkimAndBeep()

        self.lidar.pulp = 0

        self.activateCalibrationTabs(True)

    def handleFetchMeasurementEvent(self):
        """
        Handle periodic measurement fetch events.

        Collects measurements from all connected devices, stores data in the
        task model, forwards data to the data lake (with or without images
        depending on stage type), and updates calibration tab displays.
        """
        for dev_name, dev_handle in self.deviceDictionary.items():
            try:
                dev_handle.updateMeasuredValue()
            except ValueError:
                logger.error("Invalid value from atlas sensor.")

            self.tabViewRun.displayMeasuredValueAndCheckForTolerance('-'+dev_name+'-', dev_handle)                    
            if self.taskModel.status == "RUNNING":
                self.taskModel.dumpValue(dev_name, dev_handle.getMeasuredValue())

        self.bronkhorstFlowControlModel.fetchAirFlow()

        if self.taskModel.status == "RUNNING":
            if self.taskModel.currentstagetype == 'Flotation':
                self.imageStorage.saveImageOffline()
                self.dataForwarder.pushDataToDataLake(images_included=True)
            else:
                self.dataForwarder.pushDataToDataLake(images_included=False)

        self.tabViewCalibLidar.updateLidarDisplay()
        self.tabViewCalibSensors.updateSensorOutputLabel()
        self.tabViewBronkhorstFlowControl.updateAirFlowLabel()

    def handleRunningStatus(self):
        """
        Handle running status timer events.

        Updates time spent in current stage, calculates remaining time, triggers
        audio/scraping for flotation stages, and handles automatic stage transitions
        when time expires.
        """
        self.taskModel.updateTimeSpentInCurrentStage()
        remainingTimeInStage = self.taskModel.calculateRemainingTimeInCurrentStage()
        self.tabViewRun.displayRemainingTime(remainingTimeInStage, beepFlag=True)

        if (self.taskModel.currentstagetype == 'Flotation'):
            self.taskModel.flotationtime = time.time() - self.taskModel.t1flot + self.taskModel.t2flot
            vlcBeepAndSkim.skimOnce(targett= int(self.taskModel.targett),scrapingFreq=5)

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
                try:
                    configurationManager.storeJsonToPath(self.taskModel.samplefolder)
                except:
                    logger.error(f"Could not write to {str(self.taskModel.samplefolder/'configuration.json')}, probably because the file was in use or the sample folder not existent.")            
                self.tabWidget.setCurrentIndex(2)
                for index in range(self.tabWidget.count()):
                    if self.tabWidget.tabText(index) != "Information":
                        self.tabWidget.setTabVisible(index, False)

    def handleTabHasChanged(self, index):
        """
        Handle tab change events for camera calibration updates.

        Args:
            index (int): Index of the newly selected tab
        """
        if self.tabWidget.tabText(index) == "Calibrate camera":
            self.calib_cam_timer.start(self.configuration["camera tab timer"]) #ms        
        else:
            self.calib_cam_timer.stop()      

    def handleTaskModelStatusHasChanged(self):
        """
        Handle task model status changes.

        Starts or stops the running timer based on task status and sets or
        clears the air flow setpoint on the Bronkhorst controller.
        """
        if self.taskModel.status == "RUNNING":
            self.run_timer.start(self.configuration["run tab timer"]) #ms
            target_air_flow = self.taskModel.getTargetAirFlowRate()
            self.bronkhorstFlowControlModel.setAirFlow(target_air_flow)
        else:
            self.run_timer.stop()
            self.bronkhorstFlowControlModel.setAirFlow(0.0)

    def handleUpdateCalibCamEvent(self):
        """
        Handle camera calibration image update events.

        Requests the current calibration image from the camera and updates
        the calibration tab display.
        """
        self.tabViewCalibCam.updateCalibCamImage()

    def handleExportInformationEvent(self):
        """
        Handle export information button click.

        Attempts to export information data. If successful and the run has
        completed, automatically performs a restart operation.
        """
        success = self.tabViewInformation.exportInformation()
        if success and self.taskModel.status == "Completed":
            self.performRestart()
