from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog)
from PyQt5.QtCore import Qt
import pathlib
import pandas as pd 
from kafka import KafkaProducer
import json
import datetime
from collections import defaultdict

try:
    from libs import configurationManager  
except:
    from . import configurationManager  

class ImportInputAnalysisWindow(QWidget):
    def __init__(self, taskModel):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Window for importing data about mass, water, process parameters, ... into Data Lake')
        self.taskModel = taskModel
        self.configuration = configurationManager.getConfig("MainWindow")
        self.df = None
        layout = QVBoxLayout()

        def addButton(layout, button_text, action, enabled=True):
            button = QPushButton(button_text)
            button.clicked.connect(action)
            button.setEnabled(enabled)
            layout.addWidget(button)
            return button

        disclaimer_label = QLabel("Make sure that the csv file containing the analysis data is structured into the following columns: \ntimestamp, timestamp_start, run, product, dry_solids_g, water_g, collect, frother, jg, vt, pyrite_norm, quartz_norm\ntimestamp and timestamp_start are optional and are set to current timestamp, if not given.\ncollect, frother, jg, vt, pyrite_norm, quartz_norm are optional.\nUpper case letters in the columns are replaced by lower case letters.")
        layout.addWidget(disclaimer_label)
        
        self.button_import = addButton(layout, "Generate template file for input analysis csv", self.handleGenerateTemplateFileButtonPushed)        
        
        addButton(layout, "Select analysis csv", self.tryToLoadCSVFile)
        self.button_import = addButton(layout, "Import into Data Lake", self.handleImportButtonPushed, enabled=False)
        addButton(layout, "Close window", self.close)

        self.setLayout(layout)

    def handleGenerateTemplateFileButtonPushed(self):
        path = pathlib.Path(
                QFileDialog.getExistingDirectory(None, "Select directory for template generation", str(self.taskModel.workingfolder))
                ).resolve()
        timestamp_lst = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") for i in range(10)]
        run_lst = [f"run_{i//5+1}" for i in range(10)]
        product_lst = ["C1", "C2", "C3", "C4", "tails", "C1", "C2", "C3", "C4", "tails"]
        template_df = pd.DataFrame({"timestamp": timestamp_lst, "timestamp_start": timestamp_lst, "run": run_lst, "product": product_lst})
        template_df["dry_solids_g"] = ""
        template_df["water_g"] = ""
        template_df["collect"] = ""
        template_df["frother"] = ""
        template_df["jg"] = ""
        template_df["vt"] = ""
        template_df["pyrite_norm"] = ""
        template_df["quartz_norm"] = ""
        try:
            if path.is_file():
                with open(path.parent/"template.csv", "w") as file:
                    template_df.to_csv(file, quotechar="'", lineterminator='\n', index=False)
            elif path.is_dir():
                with open(path/"template.csv", "w") as file:
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

        # make the columns labels lower cap
        df.columns = [col.lower() for col in list(df.columns)]

        col_lst = ["run","product","dry_solids_g", "water_g"]
        if not set(col_lst).issubset(list(df.columns)):
            msg = 'The selected file has not the required columns "run","product","dry_solids_g" and "water_g"'
            self.button_import.setEnabled(False)
            self.df = None
            return msg, None
        
        for col in ["timestamp_start", "timestamp"]:
            col_lst = [col] + col_lst
            if col not in list(df.columns):
                df[col] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    msg = 'The column created at does not contain a datetime a la yyyy-mm-dd HH:MM:SS'
                    self.button_import.setEnabled(False)
                    self.df = None
                    return msg, None

        for col in ["collect", "frother", "jg", "vt", "pyrite_norm", "quartz_norm"]:
            if col in df.columns:
                col_lst.append(col)

        self.button_import.setEnabled(True)
        self.df = df[col_lst]
        return None, df[col_lst]

    def handleImportButtonPushed(self):
        self.df["project"] = self.configuration["project"]

        data_lst = []
        for (key1, key2, key3, key4), sub_df in self.df.groupby(["timestamp", "timestamp_start", "project", "run"]):  
            sub_df.drop(columns=["timestamp", "timestamp_start", "project", "run"], inplace=True)
            data_lst.append([key1, key2, key3, key4, sub_df.to_json(orient="records")])
        formatted_df = pd.DataFrame(data_lst, columns=["timestamp", "timestamp_start", "project", "run", "data"])

        try:
            producer = KafkaProducer(bootstrap_servers='fwgserv02a:9091')
            for row in formatted_df.itertuples(index=False):
                producer.send("lab_assistant_additional_data", '&'.join(row).encode())
        except:
            #no broker available
            pass