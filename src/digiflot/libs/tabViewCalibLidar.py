from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QProgressDialog, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
import numpy as np
import time

class TabViewCalibLidar(QWidget):
    def __init__(self, mainWindow, lidar, atlasSensor):
        super().__init__()

        self.mainWindow = mainWindow
        self.lidar = lidar
        self.atlasSensor = atlasSensor

        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QVBoxLayout()

        # Title
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("Distance LIDAR <-> pulp"), 0, Qt.AlignmentFlag.AlignCenter)
        mainLayout.addLayout(title_layout)

        # Live distance column
        live_distance_layout = QVBoxLayout()
        live_distance_layout.addStretch()
        live_distance_label = QLabel("Live distance")
        live_distance_label.setStyleSheet("color: white;")
        live_distance_label.setFont(QFont(*self.mainWindow.dfont))
        live_distance_layout.addWidget(live_distance_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.live_distance_value = QLabel("-")
        self.live_distance_value.setStyleSheet("color: white;")
        self.live_distance_value.setFont(QFont(*self.mainWindow.dfont))
        live_distance_layout.addWidget(self.live_distance_value, 0, Qt.AlignmentFlag.AlignCenter)
        live_distance_layout.addStretch()

        live_distance_widget = QWidget()
        live_distance_widget.setLayout(live_distance_layout)

        # Defined level column
        defined_level_layout = QVBoxLayout()
        defined_level_layout.addStretch()
        defined_level_label = QLabel("Defined level")
        defined_level_label.setStyleSheet("color: white;")
        defined_level_label.setFont(QFont(*self.mainWindow.dfont))
        defined_level_layout.addWidget(defined_level_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.defined_level_value = QLabel(str(self.lidar.pulplevel))
        self.defined_level_value.setStyleSheet("color: white;")
        self.defined_level_value.setFont(QFont(*self.mainWindow.dfont))
        defined_level_layout.addWidget(self.defined_level_value, 0, Qt.AlignmentFlag.AlignCenter)
        defined_level_layout.addStretch()

        defined_level_widget = QWidget()
        defined_level_widget.setLayout(defined_level_layout)

        # Distance columns layout
        distance_layout = QHBoxLayout()
        distance_layout.addWidget(live_distance_widget)
        distance_layout.addWidget(defined_level_widget)
        mainLayout.addLayout(distance_layout)

        # Define pulp level button
        button_layout = QHBoxLayout()
        self.define_button = QPushButton("Define pulp level")
        self.define_button.clicked.connect(self.definePulpLevel)
        button_layout.addStretch()
        button_layout.addWidget(self.define_button)
        button_layout.addStretch()
        mainLayout.addLayout(button_layout)

        self.setLayout(mainLayout)

    def expandWidgets(self):
        self.live_distance_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.defined_level_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_Window(self, window):
        self.window = window

    def updateLidarDisplay(self):
        measuredLIDAR = self.lidar.updateMeasuredValue()
        self.live_distance_value.setText(str(measuredLIDAR))
        if self.lidar.valueInTolerance():
            self.defined_level_value.setStyleSheet("color: green;")
            self.live_distance_value.setStyleSheet("color: green;")
        else:
            self.defined_level_value.setStyleSheet("color: red;")
            self.live_distance_value.setStyleSheet("color: red;")

    def definePulpLevel(self):
        nmeasurements = 30
        progress = QProgressDialog("Calculating distance to the pulp...", "Cancel", 0, nmeasurements, self)
        progress.setWindowTitle("Calculating")
        progress.setMinimumDuration(0)
        QApplication.processEvents()
        def measure():
            measuredLIDAR_C = []
            for i in range(nmeasurements):
                progress.setValue(i + 1)
                QApplication.processEvents()
                if progress.wasCanceled():
                    break
                time.sleep(self.atlasSensor.times_list["LIDAR"])
                measuredLIDAR_C.append(self.lidar.updateMeasuredValue())
                QApplication.processEvents()

            progress.setValue(nmeasurements)
            QApplication.processEvents()
            if not progress.wasCanceled():
                measuredLIDAR_C = [i for i in measuredLIDAR_C if i != 'none']
                self.lidar.pulplevel = np.mean(measuredLIDAR_C)
                self.defined_level_value.setText(str(round(self.lidar.pulplevel, 1)))
                self.updateLidarDisplay()
            QApplication.processEvents()

        QTimer.singleShot(0, measure)