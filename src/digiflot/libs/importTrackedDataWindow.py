from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt
import pathlib
import pandas as pd

try:
    from libs.importToDataLakeManager import ImportToDataLakeManager
    from libs import configurationManager  
except:
    from .importToDataLakeManager import ImportToDataLakeManager
    from . import configurationManager  

class ImportTrackedDataWindow(QWidget):
    def __init__(self, taskModel):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Window for importing data tracked with the DigiFlot software into the Data Lake')
        layout = QVBoxLayout()

        def addLabelAndLineEdit(layout, label_text, lineEdit_text=""):
            layout_level_2_mqtt = QHBoxLayout()
            label = QLabel(label_text)
            layout_level_2_mqtt.addWidget(label)
            lineEdit = QLineEdit()
            lineEdit.setText(str(lineEdit_text))
            layout_level_2_mqtt.addWidget(lineEdit)       
            layout.addLayout(layout_level_2_mqtt)        
            return lineEdit

        configuration = configurationManager.getConfig("MainWindow")
        self.lineEdit_project = addLabelAndLineEdit(layout, 'Project: ', configuration["project"])
        self.lineEdit_directory = addLabelAndLineEdit(layout, 'Import directory: ', "")
        self.lineEdit_scheme = addLabelAndLineEdit(layout, 'scheme.csv: ', "")
        self.lineEdit_samples = addLabelAndLineEdit(layout, 'samples.csv: ', "")
        self.lineEdit_run_files = addLabelAndLineEdit(layout, 'run files:', "")
        self.lineEdit_run_directories = addLabelAndLineEdit(layout, 'run directories:', "")

        self.button_import = QPushButton("Import into Data Lake")
        self.button_import.clicked.connect(self.handleImportButtonPushed)
        self.button_import.setEnabled(False)
        layout.addWidget(self.button_import)

        button_close = QPushButton("Close window")
        button_close.clicked.connect(self.close)
        layout.addWidget(button_close)
        
        self.setLayout(layout)
        
        # dynamic behavior on update of lineEdit about import directory
        self.lineEdit_directory.textChanged.connect(self.handleDirectoryChanged)
        self.lineEdit_directory.setText(str(taskModel.workingfolder))
    
    def handleDirectoryChanged(self):
        path_workdir = pathlib.Path(self.lineEdit_directory.text())
        result, scheme_str = ImportTrackedDataWindow.findSchemeCSV(path_workdir)
        self.lineEdit_scheme.setText(scheme_str)
        result, samples_str = ImportTrackedDataWindow.findSamplesCSV(path_workdir)
        self.lineEdit_samples.setText(samples_str)
        result, run_files_str = ImportTrackedDataWindow.findRunFiles(path_workdir, result)
        self.lineEdit_run_files.setText(run_files_str)
        result, run_directories_str = ImportTrackedDataWindow.findRunDirectories(path_workdir, result)
        self.lineEdit_run_directories.setText(run_directories_str)
        
        # if scheme.csv, samples.csv, at least one run file and at least one run directory is found, enable the import button
        if len(result) > 0 :
            self.button_import.setEnabled(True)
        else:
            self.button_import.setEnabled(False)

    @staticmethod
    def findSchemeCSV(path):
        lst = list(path.glob("scheme.csv"))
        if len(lst) > 0:
            return lst, str(lst[0])
        else:
            return [], "No scheme.csv found."

    @staticmethod    
    def findSamplesCSV(path):
        lst = list(path.glob("samples.csv"))
        if len(lst) > 0:
            return lst, str(lst[0])
        else:
            return lst, "No samples.csv found."    

    @staticmethod
    def findRunFiles(path, lst_samples):
        if len(lst_samples) == 0:
            return [], ""  

        try:
            samples_df = pd.read_csv(lst_samples[0])
        except:
            return [], "Samples.csv is ill-structured." 

        lst = []
        for run in samples_df["Samples"]:
            globlst = list(path.glob(run+".csv"))
            if len(globlst) > 0:
               lst.append(globlst[0]) 

        if len(lst) == 0:
            return [], "No run files found." 

        return lst, ', '.join([str(el.name) for el in lst]) 
    
    @staticmethod
    def findRunDirectories(path, lst_run_files):
        if len(lst_run_files) == 0:
            return [], ""  

        lst = []
        for run_file_path in lst_run_files:
            globlst = list(path.glob(run_file_path.stem+"/"))
            if len(globlst) > 0:
               lst.append(globlst[0]) 

        if len(lst) == 0:
            return [], "No run directories found."

        return lst, ', '.join([str(el.name) for el in lst]) 
    
    def handleImportButtonPushed(self):
        importToDataLakeManager = ImportToDataLakeManager()
        importToDataLakeManager.collectAndSendData(project=self.lineEdit_project.text(), working_directory_path=pathlib.Path(self.lineEdit_directory.text()), protocol="kafka")
    