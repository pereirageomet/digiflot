from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QLineEdit, QSizePolicy, QPushButton)
import logging
logger = logging.getLogger(__name__)

import re
def is_positive_float(string):
    pattern = r"(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?"
    match = re.match(pattern, string)
    return bool(match)

class TabViewCalibSensors(QWidget):
    def __init__(self, atlasSensor, deviceDictionary):
        super().__init__()
        self.atlasSensor = atlasSensor
        self.deviceDictionary = deviceDictionary
        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QVBoxLayout()

        atlas_device_list = [dev for dev in self.deviceDictionary.keys() if dev != "LIDAR"]

        #Device selection
        deviceSelectionLayout = QHBoxLayout()
        devLabel = QLabel("Select Device: ")
        self.modules_list_combo = QComboBox()
        self.modules_list_combo.addItems(atlas_device_list)
        self.modules_list_combo.currentIndexChanged.connect(self.handleComboBoxChanged)
        self.modules_list_combo.currentTextChanged.connect(self.handleComboBoxChanged)

        deviceSelectionLayout.addWidget(devLabel)
        deviceSelectionLayout.addWidget(self.modules_list_combo)

        # Monitor for polled values
        sensorPollLayout = QHBoxLayout()
        sensorLabel = QLabel("Current Value: ")
        self.sensorOutputLabel = QLineEdit("-")
        self.sensorOutputLabel.setReadOnly(True)
        sensorPollLayout.addWidget(sensorLabel)
        sensorPollLayout.addWidget(self.sensorOutputLabel)

        # Buttons to set lower, middle and upper calibration point
        middleLayout = QHBoxLayout()
        self.pushMiddle = QPushButton("Set middle cal.")
        self.pushMiddle.clicked.connect(self.handleMiddleButtonPushed)
        middleTargetLabel = QLabel("Target: ")
        self.middleTargetLineEdit = QLineEdit()
        middleLabel = QLabel("Return value: ")
        self.middleLineEdit = QLineEdit("-")
        self.middleLineEdit.setReadOnly(True)
        middleLayout.addWidget(self.pushMiddle)
        middleLayout.addWidget(middleTargetLabel)
        middleLayout.addWidget(self.middleTargetLineEdit)
        middleLayout.addWidget(middleLabel)
        middleLayout.addWidget(self.middleLineEdit)

        lowerLayout = QHBoxLayout()
        self.pushLower = QPushButton("Set lower cal.")
        self.pushLower.setEnabled(False)
        self.pushLower.clicked.connect(self.handleLowerButtonPushed)
        lowerTargetLabel = QLabel("Target: ")
        self.lowerTargetLineEdit = QLineEdit()
        lowerLabel = QLabel("Return value: ")
        self.lowerLineEdit = QLineEdit("-")
        self.lowerLineEdit.setReadOnly(True)
        lowerLayout.addWidget(self.pushLower)
        lowerLayout.addWidget(lowerTargetLabel)
        lowerLayout.addWidget(self.lowerTargetLineEdit)
        lowerLayout.addWidget(lowerLabel)
        lowerLayout.addWidget(self.lowerLineEdit)

        upperLayout = QHBoxLayout()
        self.pushUpper = QPushButton("Set upper cal.")
        self.pushUpper.setEnabled(False)
        self.pushUpper.clicked.connect(self.handleUpperButtonPushed)
        upperTargetLabel = QLabel("Target: ")
        self.upperTargetLineEdit = QLineEdit()
        upperLabel = QLabel("Return value: ")
        self.upperLineEdit = QLineEdit("-")
        self.upperLineEdit.setReadOnly(True)
        upperLayout.addWidget(self.pushUpper)
        upperLayout.addWidget(upperTargetLabel)
        upperLayout.addWidget(self.upperTargetLineEdit)
        upperLayout.addWidget(upperLabel)
        upperLayout.addWidget(self.upperLineEdit)

        clearLayout = QHBoxLayout()
        self.pushClear = QPushButton("Clear callibration")
        self.pushClear.setEnabled(True)
        self.pushClear.clicked.connect(self.handleClearButtonPushed)
        self.clearLineEdit = QLineEdit("-")
        self.clearLineEdit.setReadOnly(True)
        clearLayout.addWidget(self.pushClear)
        clearLayout.addWidget(self.clearLineEdit)

        self.pushFactory = QPushButton("Factory reset")
        self.pushFactory.setEnabled(True)
        self.pushFactory.clicked.connect(self.handleFactoryButtonPushed)
        self.factoryLineEdit = QLineEdit("-")
        self.factoryLineEdit.setReadOnly(True)

        clearLayout.addWidget(self.pushFactory)
        clearLayout.addWidget(self.factoryLineEdit)

        # Add rows to main layout
        mainLayout.addLayout(deviceSelectionLayout)
        mainLayout.addLayout(sensorPollLayout)
        mainLayout.addLayout(lowerLayout)
        mainLayout.addLayout(middleLayout)
        mainLayout.addLayout(upperLayout)
        mainLayout.addLayout(clearLayout)

        if "pH" in atlas_device_list:
            self.modules_list_combo.setCurrentIndex(atlas_device_list.index("pH"))
            self.handleComboBoxChanged()
        else:
            self.modules_list_combo.setCurrentText("Select Device")

        self.setLayout(mainLayout)


    def handleClearButtonPushed(self):
        key = self.modules_list_combo.currentText()
        if key in self.deviceDictionary.keys():
            value_str = str(self.deviceDictionary[key].queryClear())
            if value_str is not None:
                self.clearLineEdit.setText(value_str)
            else:
                self.clearLineEdit.setText("x")

    def handleFactoryButtonPushed(self):
        key = self.modules_list_combo.currentText()
        if key in self.deviceDictionary.keys():
            value_str = str(self.deviceDictionary[key].queryFactory())
            if value_str is not None:
                self.factoryLineEdit.setText(value_str)
            else:
                self.factoryLineEdit.setText("x")

    def updateSensorOutputLabel(self):
        key = self.modules_list_combo.currentText()
        if key in self.deviceDictionary.keys():
            value_str = str(self.deviceDictionary[key].getMeasuredValue())
            self.sensorOutputLabel.setText(value_str)

    def handleLowerButtonPushed(self):
        key = self.modules_list_combo.currentText()
        target_str = self.lowerTargetLineEdit.text()
        if key in self.deviceDictionary.keys() and is_positive_float(target_str):
            target_value = float(target_str)
            value_str = str(self.deviceDictionary[key].queryLowAverage(target_value))
            if value_str is not None:
                self.lowerLineEdit.setText(value_str)
            else:
                self.lowerLineEdit.setText("x")

    def handleMiddleButtonPushed(self):
        key = self.modules_list_combo.currentText()
        target_str = self.middleTargetLineEdit.text()
        if key in self.deviceDictionary.keys() and is_positive_float(target_str):
            target_value = float(target_str)
            value_str = str(self.deviceDictionary[key].queryMidAverage(target_value))
            if value_str is not None:
                self.middleLineEdit.setText(value_str)
                self.pushUpper.setEnabled(True)
                self.pushLower.setEnabled(True)
            else:
                self.middleLineEdit.setText("x")

    def handleUpperButtonPushed(self):
        key = self.modules_list_combo.currentText()
        target_str = self.upperTargetLineEdit.text()
        if key in self.deviceDictionary.keys() and is_positive_float(target_str):
            target_value = float(target_str)
            value_str = str(self.deviceDictionary[key].queryHighAverage(target_value))
            if value_str is not None:
                self.upperLineEdit.setText(value_str)
            else:
                self.upperLineEdit.setText("x")

    def handleComboBoxChanged(self):
        self.pushUpper.setEnabled(False)
        self.pushLower.setEnabled(False)
        if self.modules_list_combo.currentText() == "pH":
            self.lowerTargetLineEdit.setText("4")
            self.middleTargetLineEdit.setText("7")
            self.upperTargetLineEdit.setText("10")
        else:
            self.lowerTargetLineEdit.setText("")
            self.middleTargetLineEdit.setText("")
            self.upperTargetLineEdit.setText("")
