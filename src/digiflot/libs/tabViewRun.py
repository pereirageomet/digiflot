from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QMessageBox, QSizePolicy, QGroupBox)
from PyQt5.QtCore import Qt

from .formalHardwareInterface import FormalHardwareInterface
try:
    from libs import vlcBeepAndSkim
except:
    from . import vlcBeepAndSkim

try:
    from libs import eventManager
except:
    from . import eventManager

class TabViewRun(QWidget):
    def __init__(self, taskModel):
        super().__init__()

        self.taskModel = taskModel

        self.initUI()

    def initUI(self):
        # Main layout
        mainLayout = QVBoxLayout()

        # layout for stage, type and status
        stage_type_status_layout = QHBoxLayout()

        # Stage and type
        stage_type_layout = QHBoxLayout()
        stage_type_layout.setAlignment(Qt.AlignLeft)
        stage_label = QLabel("Stage: ")
        self.stage_label = QLabel(self.taskModel.scheme.loc[self.taskModel.currentstage, "Stage"])
        type_label = QLabel("   Type: ")
        self.type_label = QLabel(self.taskModel.scheme.loc[self.taskModel.currentstage, "Type"])
        stage_type_layout.addWidget(stage_label)
        stage_type_layout.addWidget(self.stage_label)
        stage_type_layout.addWidget(type_label)
        stage_type_layout.addWidget(self.type_label)
        stage_type_status_layout.addLayout(stage_type_layout)

        # Status
        status_layout = QHBoxLayout()
        status_layout.setAlignment(Qt.AlignRight)
        self.status_text = QLabel("Status: ")
        self.status_label = QLabel(self.taskModel.status)
        status_layout.addWidget(self.status_text)
        status_layout.addWidget(self.status_label)
        stage_type_status_layout.addLayout(status_layout)

        # add layout to mainLayout
        mainLayout.addLayout(stage_type_status_layout)

        # Cell operation conditions
        cell_op_group = QGroupBox("Cell operation conditions")
        cell_op_layout = QHBoxLayout()

        ## define subgroups ...
        air_flow_rate_group = QGroupBox("Air Flow Rate")
        air_flow_rate_layout = QHBoxLayout()
        self.air_flow_rate = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Air flow rate']))
        air_flow_rate_layout.addWidget(self.air_flow_rate)
        air_flow_rate_group.setLayout(air_flow_rate_layout)
        
        rotor_speed_group = QGroupBox("Rotor Speed")
        rotor_speed_layout = QHBoxLayout()
        self.rotor_speed = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Rotor speed']))
        rotor_speed_layout.addWidget(self.rotor_speed)
        rotor_speed_group.setLayout(rotor_speed_layout)        
        
        ## add subgroups to grouplayout
        cell_op_layout.addWidget(air_flow_rate_group)
        cell_op_layout.addWidget(rotor_speed_group)

        cell_op_group.setLayout(cell_op_layout)
        mainLayout.addWidget(cell_op_group)
        
        # Reagent Table
        self.reagent_layout = QGridLayout()
        self.reagent_name = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Reagent']))
        self.reagent_concentration = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Concentration']))
        self.reagent_volume = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Volume']))
        self.target_ph = QLabel(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Target pH']))
        
        self.reagent_layout.addWidget(QLabel("Reagent:"), 0, 0)
        self.reagent_layout.addWidget(self.reagent_name, 0, 1)
        self.reagent_layout.addWidget(QLabel("Concentration:"), 1, 0)
        self.reagent_layout.addWidget(self.reagent_concentration, 1, 1)
        self.reagent_layout.addWidget(QLabel("Volume:"), 2, 0)
        self.reagent_layout.addWidget(self.reagent_volume, 2, 1)
        self.reagent_layout.addWidget(QLabel("Target pH:"), 3, 0)
        self.reagent_layout.addWidget(self.target_ph, 3, 1)
        
        mainLayout.addLayout(self.reagent_layout)

        # Time
        time_layout = QHBoxLayout()
        self.time_label = QLabel(f"Remaining time: {self.taskModel.targett} seconds")
        self.time_label.setStyleSheet("font-size: 50pt;")#; color: black
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        mainLayout.addLayout(time_layout)

        # Measurements
        measurements_layout = QHBoxLayout()
        self.ph_label = QLabel("pH: -")
        self.ec_label = QLabel("EC: -")
        self.orp_label = QLabel("ORP: -")
        self.lidar_label = QLabel("Pulp height: -")
        self.temp_label = QLabel("- °C")
        
        measurements_layout.addWidget(self.ph_label)
        measurements_layout.addWidget(self.ec_label)
        measurements_layout.addWidget(self.orp_label)
        measurements_layout.addWidget(self.lidar_label)
        measurements_layout.addWidget(self.temp_label)
        mainLayout.addLayout(measurements_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        eventManager.registerEvent("startButtonClicked", self.start_button.clicked)
        self.pause_button = QPushButton("Pause")
        eventManager.registerEvent("pauseButtonClicked", self.pause_button.clicked)        
        self.pause_button.setEnabled(False)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        mainLayout.addLayout(buttons_layout)

        # Stage Buttons
        stage_buttons_layout = QHBoxLayout()
        self.prev_stage_button = QPushButton("Previous stage")
        eventManager.registerEvent("previousStageButtonClicked", self.prev_stage_button.clicked)        
        self.prev_stage_button.setEnabled(False)
        self.next_stage_button = QPushButton("Next stage")
        eventManager.registerEvent("nextStageButtonClicked", self.next_stage_button.clicked)          
        stage_buttons_layout.addWidget(self.prev_stage_button)
        stage_buttons_layout.addWidget(self.next_stage_button)
        mainLayout.addLayout(stage_buttons_layout)

        # Next Stage Info
        next_stage_layout = QHBoxLayout()
        self.next_stage_title = "Next: " + self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"] + " - "+ self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"]
        self.next_stage_reagentName = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Reagent'])
        self.next_stage_reagentConc = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Concentration'])
        self.next_stage_reagentVol = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Volume'])
        self.next_stage_text = QLabel(self.next_stage_title+ " (Reagent: " + self.next_stage_reagentName + ", " + self.next_stage_reagentConc + ", " + self.next_stage_reagentVol+")")
        # self.next_stage_label = QLabel(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"])
        # self.next_stage_type = QLabel(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"])
       
        next_stage_layout.addWidget(self.next_stage_text)
        # next_stage_layout.addWidget(self.next_stage_label)
        # next_stage_layout.addWidget(self.next_stage_type)
        mainLayout.addLayout(next_stage_layout)

        self.setLayout(mainLayout)

                
    def get_PySimpleGui_tab(self):
        return self._tab_instance

    def expandWidgets(self):
        self._colStageC.expand(True, True)
        self._colStageN.expand(True, True)
        self._colTableReag.expand(True, True)
        self._colTime.expand(True, True)
        self._colpH.expand(True, True)
        self._colEC.expand(True, True)
        self._colORP.expand(True, True)
        self._colRTD.expand(True, True)
        self._colLIDAR.expand(True, True)
        self._colButtonsR.expand(True, True)
        self._colButtonsSTAGES.expand(True, True)
        self._colStatus.expand(True, True)

    def set_Window(self, window):
        self.window = window

    def displayRunningStatus(self):
        self.status_label.setText(self.taskModel.status)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)

    def displayTargetTimeAndStages(self):
        self.displayRemainingTime(self.taskModel.targett)
        self.type_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage, "Type"])
        self.stage_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage, "Stage"])
        self.next_stage_title = "Next: " + self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"] + " - "+ self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"]
        self.next_stage_reagentName = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Reagent'])
        self.next_stage_reagentConc = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Concentration'])
        self.next_stage_reagentVol = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Volume'])
        self.next_stage_text.setText(self.next_stage_title+ " (Reagent: " + self.next_stage_reagentName + ", " + self.next_stage_reagentConc + ", " + self.next_stage_reagentVol+")")
        # self.next_stage_type.setText(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"])
        # self.next_stage_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"])
        
    def updateToPausedStatus(self):
        self.status_label.setText(self.taskModel.status)
        self.start_button.setEnabled(True)        
        self.pause_button.setEnabled(False)

    def displayRemainingTime(self, remainingTimeInStage, beepFlag=False):
        if remainingTimeInStage < 10:
            text_color="red"
            self.time_label.setStyleSheet(f"font-size: 70pt; color: {text_color};")
            if beepFlag:
                vlcBeepAndSkim.beepOnce()
        else:
            # text_color="black"
            self.time_label.setStyleSheet(f"font-size: 50pt;")# color: {text_color};
        self.time_label.setText(str(round(remainingTimeInStage,1)))

    def displayMeasurementCompleted(self):
        # self.next_stage_type.setText("")
        # self.next_stage_label.setText("")
        self.next_stage_text.setText("")
        self.time_label.setText(" - - ")
        self.status_label.setText(self.taskModel.status)
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.next_stage_button.setEnabled(False)        
        self.prev_stage_button.setEnabled(False)                       

    def displayMeasurementParameters(self):
        self.air_flow_rate.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Air flow rate']))
        self.rotor_speed.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Rotor speed']))
        self.target_ph.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Target pH']))
        self.reagent_name.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Reagent']))
        self.reagent_concentration.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Concentration']))
        self.reagent_volume.setText(str(self.taskModel.schemesample.loc[self.taskModel.currentstage, 'Volume']))
        self.next_stage_title = "Next: " + self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"] + " - "+ self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"]
        self.next_stage_reagentName = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Reagent'])
        self.next_stage_reagentConc = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Concentration'])
        self.next_stage_reagentVol = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Volume'])
        self.next_stage_text.setText(self.next_stage_title+ " (Reagent: " + self.next_stage_reagentName + ", " + self.next_stage_reagentConc + ", " + self.next_stage_reagentVol+")")

    def updateWholeRunTabToCurrentStage(self):
        self.displayRemainingTime(self.taskModel.targett)
        self.type_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage, "Type"])
        self.stage_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage, "Stage"])
        self.displayMeasurementParameters()

        if self.taskModel.currentstage == 0:
            self.prev_stage_button.setEnabled(False)                            
        else:
            self.prev_stage_button.setEnabled(True)                            
            
        if self.taskModel.currentstage == self.taskModel.nstages:
            self.next_stage_button.setEnabled(False)
            self.next_stage_text.setText("Completed")    
            # self.next_stage_type.setText("Completed")
            # self.next_stage_label.setText("")
        else:
            self.next_stage_button.setEnabled(True)
            self.next_stage_title = "Next: " + self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"] + " - "+ self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"]
            self.next_stage_reagentName = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Reagent'])
            self.next_stage_reagentConc = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Concentration'])
            self.next_stage_reagentVol = str(self.taskModel.schemesample.loc[self.taskModel.currentstage+1, 'Volume'])
            self.next_stage_text.setText(self.next_stage_title+ " (Reagent: " + self.next_stage_reagentName + ", " + self.next_stage_reagentConc + ", " + self.next_stage_reagentVol+")")
            # self.next_stage_type.setText(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Type"])
            # self.next_stage_label.setText(self.taskModel.scheme.loc[self.taskModel.currentstage + 1, "Stage"])

    def startClicked(self):
        if self.taskModel.checkIfTargetPhIsSet:
            self.taskModel.initializeMeasurement()
            self.displayRunningStatus()
        else:
            QMessageBox.warning(self, "Warning", 'Please select a sample first.')
 
    def displayMeasuredValueAndCheckForTolerance(self, widget_identifier, deviceHandle: FormalHardwareInterface):
        identifierToWidgetMapping = {"-pH-": self.ph_label, "-EC-": self.ec_label, "-ORP-": self.orp_label, "-LIDAR-": self.lidar_label, "-RTD-": self.temp_label}
        identifierToWidgetMapping[widget_identifier].setText(str(deviceHandle.getDisplayValue()))
        if not deviceHandle.valueInTolerance():
            identifierToWidgetMapping[widget_identifier].setStyleSheet(f"color: red;")
        # else:
        #     identifierToWidgetMapping[widget_identifier].setStyleSheet(f"color: red;")

    def expandAirFlowRateLabel(self):
        self.air_flow_rate.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def expandReagentTable(self):

        self.reagent_layout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
