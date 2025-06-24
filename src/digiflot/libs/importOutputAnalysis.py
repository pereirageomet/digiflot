from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt
import pathlib
import pandas as pd 
from kafka import KafkaProducer
import json
import csv
class ImportOutputAnalysisWindow(QWidget):
    def __init__(self, taskModel):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Window for importing analysis data into Data Lake')
        self.taskModel = taskModel
        self.df = None
        layout = QVBoxLayout()

        def addButton(layout, button_text, action, enabled=True):
            button = QPushButton(button_text)
            button.clicked.connect(action)
            button.setEnabled(enabled)
            layout.addWidget(button)
            return button

        disclaimer_label = QLabel("Make sure that the csv file containing the analysis data is structured into the following columns: \nrun, stage_name, material_composition, project, created_at")
        layout.addWidget(disclaimer_label)
        
        self.button_import = addButton(layout, "Generate template file for analysis csv", self.handleGenerateTemplateFileButtonPushed)        
        
        addButton(layout, "Select analysis csv", self.tryToLoadCSVFile)
        self.button_import = addButton(layout, "Import into Data Lake", self.handleImportButtonPushed, enabled=False)
        addButton(layout, "Close window", self.close)

        self.setLayout(layout)

    def handleGenerateTemplateFileButtonPushed(self):
        path = pathlib.Path(
                QFileDialog.getExistingDirectory(None, "Select directory for template generation", str(self.taskModel.workingfolder))
                ).resolve()
        try:
            if path.is_file():
                with open(path.parent/"template.csv", "w") as file:
                    template_df = pd.DataFrame({"run": [f"run_{i}" for i in range(8)], "stage_name": ["pH", "x", "y" ,"C1", "C2", "C3", "C4", "C5"], "material_composition": [json.dumps({"C": 0.3, "Fe": 0.4, "Si": 0.3}) for _ in range(8)], "project": ["my_project" for _ in range(8)], "created_at" : ["2012-10-10" for _ in range(8)]})
                    template_df.to_csv(file, quotechar="'", lineterminator='\n', index=False)
            elif path.is_dir():
                with open(path/"template.csv", "w") as file:
                    template_df = pd.DataFrame({"run": [f"run_{i}" for i in range(8)], "stage_name": ["pH", "x", "y" ,"C1", "C2", "C3", "C4", "C5"], "material_composition": [json.dumps({"C": 0.3, "Fe": 0.4, "Si": 0.3}) for _ in range(8)], "project": ["my_project" for _ in range(8)], "created_at" : ["2012-10-10" for _ in range(8)]})
                    template_df.to_csv(file, quotechar="'", lineterminator='\n',  index=False)        
        except:
            pass

    def tryToLoadCSVFile(self):
        file_path_str, _ = QFileDialog.getOpenFileName(None, "Select CSV file for import", str(self.taskModel.workingfolder))
        file_path = pathlib.Path(file_path_str).resolve()
        try:
            with open(file_path) as file:
                df = pd.read_csv(file)
        except:
            msg = 'The selected file is not a valid comma-separated file. Please check.'
            self.button_import.setEnabled(False)
            self.df = None
            return msg, None

        try:
            df = df[["run", "stage_name", "material_composition", "project", "created_at"]]
        except:
            msg = 'The selected file has not the required columns "run", "stage_name", "material_composition", "project" and "created_at"'
            self.button_import.setEnabled(False)
            self.df = None
            return msg, None
        
        try:
            df["created_at"] = pd.to_datetime(df["created_at"])
        except:
            msg = 'The column created at does not contain a datetime a la yyyy-mm-dd'
            self.button_import.setEnabled(False)
            self.df = None
            return msg, None

        self.button_import.setEnabled(True)
        self.df = df
        return None, df

    def handleImportButtonPushed(self):
        producer = KafkaProducer(bootstrap_servers='fwgserv02a:9091')
        csv_str = self.df.to_csv(header=False, index=False, sep=";", quotechar="'", lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")
        producer.send("lab_assistant_output_analysis_data", csv_str.encode())