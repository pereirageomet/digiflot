from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton)
from PyQt5.QtCore import Qt

try:
    from libs import configurationManager  
except:
    from . import configurationManager  

class EnterProjectWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.configuration = configurationManager.getConfig("MainWindow")
        self.setWindowTitle('Please enter the project id.')
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

        self.lineEdit_project = addLabelAndLineEdit(layout, 'Project id: ', self.configuration["project"])

        button_set = QPushButton("Set")
        button_set.clicked.connect(self.handleSetButtonPushed)
        self.lineEdit_project.returnPressed.connect(self.handleSetButtonPushed)
        layout.addWidget(button_set)
        self.setLayout(layout)

    def handleSetButtonPushed(self):
        self.configuration["project"] = self.lineEdit_project.text()
        configurationManager.storeToJson()
        self.close()
