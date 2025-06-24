from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QAction,QWidgetAction, QLineEdit)
import logging
logger = logging.getLogger(__name__)

try:
    from libs.importTrackedDataWindow import ImportTrackedDataWindow    
    from libs.importInputAnalysis import ImportInputAnalysisWindow 
    from libs.importOutputAnalysis import ImportOutputAnalysisWindow 
except:
    from .importTrackedDataWindow import ImportTrackedDataWindow    
    from .importInputAnalysis import ImportInputAnalysisWindow    
    from .importOutputAnalysis import ImportOutputAnalysisWindow    

class DropDownMenu:
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow
        self.make_the_menu_bar()

    def make_the_menu_bar(self):
        # Menu bar
        menu_bar = self.mainWindow.menuBar()

        # Add menu Settings
        settings_menu = menu_bar.addMenu('Settings')

        # Add submenu aquisition mode
        aquisition_menu = settings_menu.addMenu('Aquisition mode')

        # Aktionen erstellen
        self.offline_action = ColoredMenuItem('Offline', self.mainWindow)
        self.online_action = ColoredMenuItem('Online', self.mainWindow)

        if self.mainWindow.offline_image_storage:
            self.offline_action.set_color("green")
        else:
            self.offline_action.set_color("red")

        if self.mainWindow.nodered_in_network:
            self.online_action.set_color("green")
        else:
            self.online_action.set_color("red")

        # Add trigger
        self.offline_action.triggered.connect(self.handle_offline_aquisition_action)
        self.online_action.triggered.connect(self.handle_online_aquisition_action)

        # Aktionen zum Menü hinzufügen
        aquisition_menu.addAction(self.offline_action)
        aquisition_menu.addAction(self.online_action)

        # Add separator
        settings_menu.addSeparator()  

        # Add online configuration 
        online_configuration_action = QAction('Online configuration', self.mainWindow)
        online_configuration_action.triggered.connect(self.openOnlineConfigWindow)
        settings_menu.addAction(online_configuration_action)

        # Add separator
        settings_menu.addSeparator()  

        # Add import of input analysis
        import_input_analysis_data_action = QAction('Import analysis of input', self.mainWindow)
        import_input_analysis_data_action.triggered.connect(self.openImportInputAnalysisWindow)
        settings_menu.addAction(import_input_analysis_data_action)

        # Add import tracked data 
        import_tracked_data_action = QAction('Import tracked data', self.mainWindow)
        import_tracked_data_action.triggered.connect(self.openImportTrackedDataWindow)
        settings_menu.addAction(import_tracked_data_action)
        
        # Add import of output analysis
        import_output_analysis_data_action = QAction('Import analysis of output', self.mainWindow)
        import_output_analysis_data_action.triggered.connect(self.openImportOutputAnalysisWindow)
        settings_menu.addAction(import_output_analysis_data_action)



        """
        # Add separator
        settings_menu.addSeparator()  
        
        # Add submenu camera
        camera_menu = settings_menu.addMenu('Camera selection')

        # Aktionen erstellen
        galaxy_action = QAction('Galaxy camera', self.mainWindow)
        raspi_action = QAction('Raspi camera', self.mainWindow)

        # Aktionen zum Menü hinzufügen
        camera_menu.addAction(galaxy_action)
        camera_menu.addAction(raspi_action)
        """

    def openOnlineConfigWindow(self):
        window = OnlineConfigWindow(self.mainWindow.dataForwarder)
        window.show()
        self.mainWindow.openWindows.append(window)

    def openImportTrackedDataWindow(self):
        window = ImportTrackedDataWindow(self.mainWindow.controller.taskModel)
        window.show()
        self.mainWindow.openWindows.append(window)

    def openImportInputAnalysisWindow(self):
        window = ImportInputAnalysisWindow(self.mainWindow.controller.taskModel)
        window.show()
        self.mainWindow.openWindows.append(window)

    def openImportOutputAnalysisWindow(self):
        window = ImportOutputAnalysisWindow(self.mainWindow.controller.taskModel)
        window.show()
        self.mainWindow.openWindows.append(window)

    def handle_offline_aquisition_action(self):
        if self.mainWindow.offline_image_storage:
            self.mainWindow.offline_image_storage = False
            self.mainWindow.imageStorage.finishProcessesAndQueues()
            self.offline_action.set_color("red")
        else:
            self.mainWindow.offline_image_storage = True
            self.mainWindow.imageStorage.startOfflineStorageService()
            self.offline_action.set_color("green")

    def handle_online_aquisition_action(self):
        if self.mainWindow.nodered_in_network:
            self.mainWindow.nodered_in_network = False
            self.online_action.set_color("red")
            try:
                self.mainWindow.dataForwarder.finishProcessesAndQueues()
            except:
                self.mainWindow.dataForwarder = None
        else:
            try:
                self.mainWindow.dataForwarder.startDataForwarderService()
            except:
                self.mainWindow.nodered_in_network = False
                self.online_action.set_color("red")
                self.mainWindow.dataForwarder = None
            else:
                self.mainWindow.nodered_in_network = True
                self.online_action.set_color("green")

class ColoredMenuItem(QWidgetAction):
    def __init__(self, text, parent=None):
        super().__init__(parent)

        # Create a widget to act as the menu item
        self.widget = QWidget(parent)
        self.layout = QHBoxLayout(self.widget)
        self.layout.setContentsMargins(20, 5, 20, 5)

        # Create a label to display the text
        self.label = QLabel(text, self.widget)

        # Add the label to the layout
        self.layout.addWidget(self.label)

        # Set the widget as the default widget for this action
        self.setDefaultWidget(self.widget)

    def set_color(self, bg_color, text_color='black'):
        # Apply styles to the widget and label
        self.widget.setStyleSheet(f"background-color: {bg_color};")
        self.label.setStyleSheet(f"color: {text_color};")

class OnlineConfigWindow(QWidget):
    def __init__(self, dataForwarder):
        super().__init__()
        self.dataForwarder = dataForwarder
        self.setWindowTitle('Online configuration')
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

        self.lineEdit_mqttDomain = addLabelAndLineEdit(layout, 'Mqtt-broker domain: ', dataForwarder.getBroker())
        self.lineEdit_port = addLabelAndLineEdit(layout, 'Port: ', dataForwarder.getPort())   
        self.lineEdit_mqttUser = addLabelAndLineEdit(layout, 'Mqtt user: ', dataForwarder.getUsername())   
        self.lineEdit_mqttPassword = addLabelAndLineEdit(layout, 'Mqtt password: ', dataForwarder.getPassword())   
        self.lineEdit_mqttPassword.setEchoMode(QLineEdit.Password)
        self.lineEdit_topic_pub = addLabelAndLineEdit(layout, 'Publish topic: ', dataForwarder.getTopic_pub()) 

        button_set = QPushButton("Set")
        button_set.clicked.connect(self.handleSetButtonPushed)
        layout.addWidget(button_set)
        self.setLayout(layout)

    def handleSetButtonPushed(self):
        try:
            broker = self.lineEdit_mqttDomain.text()
            port = int(self.lineEdit_port.text())
            topic_pub = self.lineEdit_topic_pub.text()
            username = self.lineEdit_mqttUser.text()
            password = self.lineEdit_mqttPassword.text()
        except ValueError:
            pass
        else:
            self.dataForwarder.reconnectStreamToMqttBroker(broker=broker, port=port, topic_pub=topic_pub, username=username, password=password)
            self.close()
def main():
    pass

if __name__=="__main__":
    main()
