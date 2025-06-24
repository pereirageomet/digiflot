import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QLabel, QListWidget, QMessageBox, QSizePolicy)

try:
    from libs import eventManager
except:
    from . import eventManager

logger = logging.getLogger(__name__)

class TabViewSetup(QWidget):
    def __init__(self, taskModel, camInstance, atlasSensor, lidar):
        super().__init__()

        self.taskModel = taskModel
        self.camInstance = camInstance
        self.atlasSensor = atlasSensor
        self.lidar = lidar

        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QVBoxLayout()

        # Table for scheme
        self.tableScheme = TabViewSetup.generateTableWidgetFromDataframe(self.taskModel.scheme)

        # Table for schemesample
        self.tableSchemeSample = TabViewSetup.generateTableWidgetFromDataframe(self.taskModel.schemesample)
        
        # Column for buttons and sample list
        self.workFolderButton = QPushButton('Define work folder')
        eventManager.registerEvent("workingFolderButtonClicked", self.workFolderButton.clicked)        
        self.sampleLabel = QLabel('Choose the sample:')
        self.sampleList = QListWidget()
        self.okButton = QPushButton('OK')
        eventManager.registerEvent("okButtonClicked", self.okButton.clicked)

        # Column for connected devices
        self.devicesLabel = QLabel('Devices connected: ')
        self.cameraLabel = QLabel('Camera')
        self.cameraLabel.setStyleSheet(f'color: {self.camInstance.get_colorCAM()}')
        self.lidarLabel = QLabel('LIDAR')
        self.lidarLabel.setStyleSheet(f'color: {self.lidar.colorLIDAR}')
        self.phLabel = QLabel('pH')
        self.phLabel.setStyleSheet(f'color: {self.atlasSensor.colorpH}')
        self.tempLabel = QLabel('Temperature')
        self.tempLabel.setStyleSheet(f'color: {self.atlasSensor.colorT}')
        self.condLabel = QLabel('Conductivity')
        self.condLabel.setStyleSheet(f'color: {self.atlasSensor.colorCond}')
        self.orLabel = QLabel('OxiRedox potential')
        self.orLabel.setStyleSheet(f'color: {self.atlasSensor.colorOR}')

        # Layout for buttons and sample list
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.workFolderButton)
        buttonLayout.addWidget(self.sampleLabel)
        buttonLayout.addWidget(self.sampleList)
        buttonLayout.addWidget(self.okButton)

        # Layout for connected devices
        devicesLayout_hbox = QHBoxLayout()
        devicesLayout_hbox.addWidget(self.cameraLabel)
        devicesLayout_hbox.addWidget(self.lidarLabel)
        devicesLayout_hbox.addWidget(self.phLabel)
        devicesLayout_hbox.addWidget(self.tempLabel)
        devicesLayout_hbox.addWidget(self.condLabel)
        devicesLayout_hbox.addWidget(self.orLabel)
        devicesLayout = QVBoxLayout()
        devicesLayout.addWidget(self.devicesLabel)
        devicesLayout.addLayout(devicesLayout_hbox)
        
        # Add widgets to main layout
        mainLayout.addWidget(self.tableScheme)
        mainLayout.addWidget(self.tableSchemeSample)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(devicesLayout)

        self.setLayout(mainLayout)

        self.setWindowTitle('Setup Tab')
        self.show()

    def expandWidgets(self):
        self.tableScheme.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tableSchemeSample.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.workFolderButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sampleList.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.okButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def displaySchemeAndSamplenames(self):
        self.tableScheme.clearContents()
        self.tableScheme.setRowCount(len(self.taskModel.scheme))
        for i, row in enumerate(self.taskModel.scheme.values):
            for j, val in enumerate(row):
                self.tableScheme.setItem(i, j, QTableWidgetItem(str(val)))
        self.sampleList.clear()
        self.sampleList.addItems(self.taskModel.getListOfRemainingSamples())

    def displaySampleScheme(self):
        self.tableSchemeSample.clearContents()
        self.tableSchemeSample.setRowCount(len(self.taskModel.schemesample))
        for i, row in enumerate(self.taskModel.schemesample.values):
            for j, val in enumerate(row):
                self.tableSchemeSample.setItem(i, j, QTableWidgetItem(str(val)))

    def workingFolderButtonClicked(self):        
        msg = self.taskModel.tryToLoadSchemeFile(self)
        if msg is not None:
            logger.warning(msg)
            QMessageBox.warning(self, "Warning", msg)
        
        msg = self.taskModel.tryToLoadSampleFile()
        if msg is not None:
            logger.warning(msg)
            QMessageBox.warning(self, "Warning", msg)

        self.displaySchemeAndSamplenames()

    @staticmethod
    def generateTableWidgetFromDataframe(df):
        tableWidget = QTableWidget()
        tableWidget.setColumnCount(len(df.columns))
        tableWidget.setHorizontalHeaderLabels(df.columns)
        tableWidget.setRowCount(len(df))
        TabViewSetup.updateTableWidgetFromDataframe(df, tableWidget)
        return tableWidget
    
    @staticmethod
    def updateTableWidgetFromDataframe(df, tableWidget_target):
        for i, row in enumerate(df.values):
            for j, val in enumerate(row):
                tableWidget_target.setItem(i, j, QTableWidgetItem(str(val)))
        #Strech the columns
        header=tableWidget_target.horizontalHeader()
        for j, _ in enumerate(df.columns):
            header.setSectionResizeMode(j, QHeaderView.Stretch)
        #Strech the rows
        header = tableWidget_target.verticalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
