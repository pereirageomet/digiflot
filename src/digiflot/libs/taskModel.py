from datetime import datetime, timezone
import time
from io import StringIO
import pathlib
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
try:
    from libs.taskModelEncoder import TaskModelEncoder
    from libs import vlcBeepAndSkim
    from libs import eventManager        
except:
    from .taskModelEncoder import TaskModelEncoder
    from . import vlcBeepAndSkim
    from . import eventManager   
import json
import logging
logger = logging.getLogger(__name__)

import re
def is_float(string):
    pattern = r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    match = re.match(pattern, string)
    return bool(match)

class TaskModel(QObject):
    statusHasChanged = pyqtSignal()
    def __init__(self, camera, atlasSensor, lidar):
        super(TaskModel, self).__init__()
        eventManager.registerEvent("taskModelStatusHasChanged", self.statusHasChanged)    
        
        #Hardware Interface Classes
        self.camera = camera
        self.atlasSensor = atlasSensor
        self.lidar = lidar

        #Variables
        # these variables are used for the software to work in its 0 state
        self._status = "PAUSED" # experiments must be started in PAUSE
        self.currentstage = 0 #a blank experimental design to feed the interface
        # Path to default files, i.e., sample_default.csv, scheme_default.csv
        self.defaultFilePath = pathlib.Path(vlcBeepAndSkim.__file__).parent.parent.resolve()
        # Path to config files
        self.workingfolder = pathlib.Path.cwd().resolve()
        # Path to output files
        self.samplefolder = None
        self.samplenames = None
        self.scheme = pd.DataFrame({
                "Stage": ["",""],
                "Time(s)": ["",""],
                "Type": ["Conditioning","Flotation"]
        })
        self.schemesample = pd.DataFrame({
            'Air flow rate': ["",""],
            'Rotor speed': ["",""],#this dataframe must have at least two rows because the interface always try to check what is coming after the current stage
            'Target pH': ["",""],
            'Reagent': ["",""],
            'Concentration': ["",""],
            'Volume': ["",""],
            'Stage': ["",""]
        })
        self.selectedSample = None       

        #time variables
        #t0 ... timestamp set when pressing the ok button
        #t1 ... timestamp for the beginning of the current stage
        #t2 ... time span in the current stage
        #targett ... time to be spent in current stage
        #times_list of atlasSensor ... time span to be spent before fetching new data
        #flotationtime ... time spent in current flotation stage
        #t1flot ... timestamp for the beginning of flotation stage
        #t2flot ... time span spent in flotation stage before pausing
        self.t_0, self.t1,self.t2,self.flotationtime,self.t1flot,self.t2flot = 0,0,0,0,0,0 #these variables are used to update the timer
        #Target time span for current stage
        self.targett = 0

    def getCurrentTargetValue(self, column="Target pH"):
        return float(self.schemesample.loc[self.currentstage, column])

    def provideSemiStructuredData(self):
        return json.dumps(self, cls=TaskModelEncoder, separators=(',', ':'))

    def setCamera(self, cam):
        self.camera = cam

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self.statusHasChanged.emit()

    def markStart(self):
        self.t0 = time.time()

    def getStartTimestamp(self):
        datetime_obj = datetime.fromtimestamp(self.t0).astimezone(timezone.utc)
        timestamp = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]                
        return timestamp

    def initializeMeasurement(self):
        self.status = "RUNNING"
        self.t1 = time.time()
        vlcBeepAndSkim.skimbeeps = True # for the case in which the skimming notification was paused
        if (self.currentstagetype == 'Flotation'):
            self.t1flot = time.time()

    def checkIfTargetPhIsSet(self):
        return self.schemesample.loc[0,"Target pH"] != ""

    @property
    def nstages(self):
        #total number of stages
        if self.scheme is not None:
            return len(self.scheme)-1
        else:
            return -1

    @property
    def nconc(self):
        #number of stages of type flotation, i.e. the number of concentrates
        if self.scheme is not None:
            return sum(self.scheme["Type"]=="Flotation") 
        else:
            return 0

    @property
    def currentstagetype(self):
        if self.scheme is not None:
            return self.scheme.loc[self.currentstage, "Type"]
        else:
            return ""

    @property
    def currentstagename(self):
        if self.scheme is not None:
            return self.scheme.loc[self.currentstage, "Stage"]
        else:
            return ""

    def getTargetAirFlowRate(self):
        value_str = str(self.schemesample.loc[self.currentstage, "Air flow rate"])
        if is_float(value_str):
            value = float(value_str)
        else:
            value = 0.0
        return value

    def updateTimeSpentInCurrentStage(self):
        self.t2 = time.time() - self.t1

    def calculateRemainingTimeInCurrentStage(self):
        return self.targett - self.t2

    @staticmethod
    def openStrippedFile(path):
        #read the file
        with open(path, "r") as file:
            file_str = file.read()
        #remove all whitespaces and tabs
        file_str_stripped = file_str.replace(' ', '').replace('\t', '')
        #generate a new readstream from the corrected file_str
        file_stripped = StringIO(file_str_stripped)
        return file_stripped

    def tryToLoadSchemeFile(self, parent_view):
        try:
            msg = None
            workingfolder = pathlib.Path(
                QFileDialog.getExistingDirectory(parent_view, "Select Work Folder", str(self.workingfolder))
                ).resolve()
            #read stripped version of the file into a dataframe
            with TaskModel.openStrippedFile(workingfolder / "scheme.csv") as file_stripped:
                new_scheme = pd.read_csv(file_stripped)
        except (TypeError,FileNotFoundError):
            msg = 'There is no \"scheme.csv\" file in the selected folder. Demo mode is started and load scheme_default.csv is loaded instead.'
            with TaskModel.openStrippedFile(self.defaultFilePath / "scheme_default.csv") as file_stripped:
                new_scheme = pd.read_csv(file_stripped)
        else:
            self.workingfolder = workingfolder
            
        #Apply default column labels from former scheme pandas dataframe to new one
        columnLabels = self.scheme.columns
        self.scheme = new_scheme
        self.scheme.columns = columnLabels
    
        self.targett = self.scheme.loc[self.currentstage, "Time(s)"]
        return msg

    def tryToLoadSampleFile(self):
        try:
            msg = None
            with TaskModel.openStrippedFile(self.workingfolder / "samples.csv") as file_stripped:
                self.samplenames = pd.read_csv(file_stripped)            
        except FileNotFoundError:
            msg = 'There is no -samples.csv- file in this folder, please fix that. Demo mode is started and samples_default.csv is loaded instead.'
            with TaskModel.openStrippedFile(self.defaultFilePath / "samples_default.csv") as file_stripped:
                self.samplenames = pd.read_csv(file_stripped)            
        return msg        

    def tryToLoadSchemeSampleAndCreateSampleFolder(self):
        msg = None
        try:
            with TaskModel.openStrippedFile(self.workingfolder / (self.selectedSample + ".csv" )) as file_stripped:
                newschemesample = pd.read_csv(file_stripped)
        except FileNotFoundError:
            msg = 'There is no ' + self.selectedSample + ".csv"+' file in the folder ' + str(self.workingfolder) + ', please fix that'
        else:
            if len(self.scheme) != len(newschemesample): #make sure that the scheme used for the sample is the same as that defined for the project
                msg ='The experimental procedure of the sample seems to not fit that of the project. Please check the content of files: -scheme.csv- and -' + self.selectedSample + '.csv-'
            else:
                #Apply default column labels from former scheme pandas dataframe to new one
                columnLabels = self.schemesample.columns
                self.schemesample = newschemesample
                self.schemesample.columns = columnLabels
                
                self.samplefolder = self.workingfolder / self.selectedSample
                if not pathlib.Path.exists(self.samplefolder):
                    pathlib.Path.mkdir(self.samplefolder)
                else:
                    # delete old content, if there is any
                    for file in self.samplefolder.glob('*.png'):
                        file.unlink(missing_ok=True)
                    for file in self.samplefolder.glob('*.tiff'):
                        file.unlink(missing_ok=True)
                    for file in self.samplefolder.glob('*.csv'):
                        file.unlink(missing_ok=True)
                    for file in self.samplefolder.glob('*.json'):
                        file.unlink(missing_ok=True)
                # Generate the files and overwrite old ones, if there are some
                for DEV in self.atlasSensor.modules_list:        
                    outputStr =  "Date,Time,FlotationTime,StageType,StageName"+"," + DEV
                    with open(self.samplefolder / ( DEV + ".csv" ), "w") as fileoutput:
                        print(outputStr, file=fileoutput)                        
        return msg
    
    def moveToNextStage(self):
        self.currentstage += 1
        self.targett = self.scheme.loc[self.currentstage, "Time(s)"]
        self.t1 = time.time()
        self.t2 = 0
        self.t2flot = 0

    def moveToPreviousStage(self):
        self.currentstage -= 1
        self.targett = self.scheme.loc[self.currentstage, "Time(s)"]
        self.t1 = time.time()
        self.t2 = 0
        self.t2flot = 0

    def moveToFirstStage(self):
        self.currentstage = 0
        self.targett = self.scheme.loc[self.currentstage, "Time(s)"]
        self.t1 = time.time()
        self.t2 = 0
        self.t2flot = 0

    def stageTypeHasChanged(self):
        if self.currentstage > 0:
            return self.currentstagetype != self.scheme.loc[self.currentstage-1, "Type"]
        else:
            return False

    def dumpValue(self, MOD, measuredValue):
        today = datetime.now()
        outputStr = f'{today.strftime("%Y%m%d, %H.%M.%S.%f")}, {self.flotationtime}, {self.scheme.loc[self.currentstage, "Type"]}, {self.scheme.loc[self.currentstage, "Stage"]}, {measuredValue}'
        with open(self.samplefolder / ( MOD + ".csv" ), "a") as fileoutput:
            print(outputStr, file=fileoutput)

    def updateSamplesFile(self):
        self.samplenames.loc[self.samplenames.Samples==self.selectedSample,"Executed"]="Y"
        self.samplenames.to_csv(self.workingfolder / "samples.csv", index=False)

    def adjustForTimeSpentInCurrentStage(self):
        #reduce remaining target time by time already spent in this stage
        self.targett -= self.t2
        #sum up time already spent for flotation
        self.t2flot += self.flotationtime

    def getListOfRemainingSamples(self):
        return list(self.samplenames["Samples"][self.samplenames["Executed"] == "N"])