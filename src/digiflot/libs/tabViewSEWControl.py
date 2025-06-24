from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QLineEdit, QSizePolicy, QPushButton)
import logging
logger = logging.getLogger(__name__)

import re
def is_positive_float(string):
    pattern = r"(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    match = re.match(pattern, string)
    return bool(match)

class TabViewSEWControl(QWidget):
    def __init__(self, sewControlModel):
        super().__init__()
        self.sewControlModel = sewControlModel
        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QVBoxLayout()

        # Monitor for polled values
        sewControlLayout = QHBoxLayout()
        rotorSpeedLabel_pre = QLabel("Currently measured rotor speed: ")
        self.rotorSpeedLabel = QLineEdit("-")
        self.rotorSpeedLabel.setReadOnly(True)
        sewControlLayout.addWidget(rotorSpeedLabel_pre)
        sewControlLayout.addWidget(self.rotorSpeedLabel)

        sewControlLayout2 = QHBoxLayout()
        rotorSpeedLabel_pre2 = QLabel("Currently set rotor speed: ")
        self.rotorSpeedLabel2 = QLineEdit("-")
        self.rotorSpeedLabel2.setReadOnly(True)
        sewControlLayout2.addWidget(rotorSpeedLabel_pre2)
        sewControlLayout2.addWidget(self.rotorSpeedLabel2)

        setLayout = QHBoxLayout()
        self.pushButton = QPushButton("Set rotor speed")
        self.pushButton.clicked.connect(self.handleSetRotorSpeedButtonPushed)
        targetLabel = QLabel("Target: ")
        self.targetLineEdit = QLineEdit()

        setLayout.addWidget(self.pushButton)
        setLayout.addWidget(targetLabel)
        setLayout.addWidget(self.targetLineEdit)

        # Add rows to main layout
        mainLayout.addLayout(sewControlLayout)
        mainLayout.addLayout(sewControlLayout2)
        mainLayout.addLayout(setLayout)

        self.setLayout(mainLayout)

    def updateRotorSpeedLabel(self):
        value_str = str(self.sewControlModel.getRotorSpeed())
        self.rotorSpeedLabel.setText(value_str)
        value_str2 = str(self.sewControlModel.getSetRotorSpeed())
        self.rotorSpeedLabel2.setText(value_str2)

    def handleSetRotorSpeedButtonPushed(self):
        target_str = self.targetLineEdit.text()
        if is_positive_float(target_str):
            target_value = float(target_str)
            self.sewControlModel.setRotorSpeed(target_value)