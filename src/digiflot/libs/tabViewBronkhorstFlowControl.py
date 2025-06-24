from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QLineEdit, QSizePolicy, QPushButton)
import logging
logger = logging.getLogger(__name__)

import re
def is_positive_float(string):
    pattern = r"(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    match = re.match(pattern, string)
    return bool(match)

class TabViewBronkhorstFlowControl(QWidget):
    def __init__(self, bronkhorstFlowControlModel):
        super().__init__()
        self.bronkhorstFlowControlModel = bronkhorstFlowControlModel
        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QVBoxLayout()

        # Monitor for polled values
        sensorPollLayout = QHBoxLayout()
        airFlowLabel_pre = QLabel("Currently measured air flow: ")
        self.airFlowLabel = QLineEdit("-")
        self.airFlowLabel.setReadOnly(True)
        sensorPollLayout.addWidget(airFlowLabel_pre)
        sensorPollLayout.addWidget(self.airFlowLabel)

        sensorPollLayout2 = QHBoxLayout()
        airFlowLabel_pre2 = QLabel("Currently set air flow: ")
        self.airFlowLabel2 = QLineEdit("-")
        self.airFlowLabel2.setReadOnly(True)
        sensorPollLayout2.addWidget(airFlowLabel_pre2)
        sensorPollLayout2.addWidget(self.airFlowLabel2)

        setLayout = QHBoxLayout()
        self.pushButton = QPushButton("Set air flow")
        self.pushButton.clicked.connect(self.handleSetAirFlowButtonPushed)
        targetLabel = QLabel("Target: ")
        self.targetLineEdit = QLineEdit()

        setLayout.addWidget(self.pushButton)
        setLayout.addWidget(targetLabel)
        setLayout.addWidget(self.targetLineEdit)

        # Add rows to main layout
        mainLayout.addLayout(sensorPollLayout)
        mainLayout.addLayout(sensorPollLayout2)
        mainLayout.addLayout(setLayout)

        self.setLayout(mainLayout)

    def updateAirFlowLabel(self):
        value_str = str(self.bronkhorstFlowControlModel.getAirFlow())
        self.airFlowLabel.setText(value_str)
        value_str2 = str(self.bronkhorstFlowControlModel.getSetAirFlow())
        self.airFlowLabel2.setText(value_str2)

    def handleSetAirFlowButtonPushed(self):
        target_str = self.targetLineEdit.text()
        if is_positive_float(target_str):
            target_value = float(target_str)
            self.bronkhorstFlowControlModel.setAirFlow(target_value)