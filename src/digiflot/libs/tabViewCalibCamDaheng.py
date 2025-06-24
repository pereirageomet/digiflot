import logging
logger = logging.getLogger(__name__)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QCheckBox, QGroupBox, QLineEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap
try:
    from PIL.ImageQt import ImageQt
except:
    ImageQt = None
    logger.error("Probably the PyQt installation is broken, or PIL is not installed.")

class TabViewCalibCamDaheng(QWidget):
    def __init__(self, dahengCamModel):
        super().__init__()

        self.dahengCamModel = dahengCamModel
        self.initUI()

    def initUI(self):
        # Create main layout
        mainLayout = QHBoxLayout()

        # Column for image calibration
        imageCalibLayout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap(''))
        imageCalibLayout.addWidget(self.image_label)

        file_format_group = QGroupBox("Color space")
        file_format_layout = QVBoxLayout()
        self.file_format_combo = QComboBox()
        self.file_format_combo.addItems(["jpg", "png"])
        self.file_format_combo.setCurrentText("png")
        file_format_layout.addWidget(self.file_format_combo)
        file_format_group.setLayout(file_format_layout)
        imageCalibLayout.addWidget(file_format_group)
        imageCalibLayout.addStretch()
        
        # Column for image settings
        imageSettingsLayout = QVBoxLayout()
        
        self.image_height_label = QLabel("Image height (px):")
        self.image_height_label.setVisible(True)
        self.image_height_input = QLineEdit(f"{self.dahengCamModel.get_imgH()}")
        self.image_height_input.setVisible(True)
        imageSettingsLayout.addWidget(self.image_height_label)
        imageSettingsLayout.addWidget(self.image_height_input)
        
        self.error_img_height = QLabel("Please use values between 640 and 1280 px")
        self.error_img_height.setStyleSheet("color: red")
        self.error_img_height.setVisible(False)
        imageSettingsLayout.addWidget(self.error_img_height)
        
        self.error_img_height_2 = QLabel("This value seems odd - changed it to 800")
        self.error_img_height_2.setStyleSheet("color: red")
        self.error_img_height_2.setVisible(False)
        imageSettingsLayout.addWidget(self.error_img_height_2)
        
        aspect_ratio_layout = QHBoxLayout()
        self.aspect_ratio_label = QLabel("Aspect ratio: ")
        self.aspect_ratio_spin = QDoubleSpinBox()
        self.aspect_ratio_spin.setRange(0.1, 10)  # Equivalent to 0.4 to 2 in steps of 0.2
        self.aspect_ratio_spin.setSingleStep(0.1)
        self.aspect_ratio_spin.setValue(self.dahengCamModel.get_imgW()/self.dahengCamModel.get_imgH())
        aspect_ratio_layout.addWidget(self.aspect_ratio_label)
        aspect_ratio_layout.addWidget(self.aspect_ratio_spin)
        imageSettingsLayout.addLayout(aspect_ratio_layout)
        
        self.error_aspect_ratio = QLabel("This aspect ratio seems odd - set it to 1")
        self.error_aspect_ratio.setStyleSheet("color: red")
        self.error_aspect_ratio.setVisible(False)
        imageSettingsLayout.addWidget(self.error_aspect_ratio)
        
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("Interval between pictures: ")
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.1, 1.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(self.dahengCamModel.get_intervalbild()) 
        self.interval_unit_label = QLabel("s")
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(self.interval_unit_label)
        imageSettingsLayout.addLayout(interval_layout)

        self.save_raw_checkbox = QCheckBox("Save raw image?")
        self.save_raw_checkbox.setChecked(self.dahengCamModel.get_imgRaw())
        self.save_raw_checkbox.stateChanged.connect(self.handleSaveRawCheckboxStateChanged)        
        imageSettingsLayout.addWidget(self.save_raw_checkbox)
        
        self.normalize_checkbox = QCheckBox("Normalize image?")
        self.normalize_checkbox.setChecked(self.dahengCamModel.get_imgNorm())
        self.normalize_checkbox.stateChanged.connect(self.handleNormalizeCheckboxStateChanged)
        imageSettingsLayout.addWidget(self.normalize_checkbox)

        gain_layout = QHBoxLayout()
        self.gain_label = QLabel("Gain: ")
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0.1, 16.0)
        self.gain_spin.setSingleStep(0.1)
        self.gain_spin.setValue(self.dahengCamModel.get_gain()) 
        gain_layout.addWidget(self.gain_label)
        gain_layout.addWidget(self.gain_spin)
        imageSettingsLayout.addLayout(gain_layout)

        exposure_time_layout = QHBoxLayout()
        self.exposure_time_label = QLabel("Exposure Time: ")
        self.exposure_time_spin = QDoubleSpinBox()
        self.exposure_time_spin.setRange(1.0, 1000.0)
        self.exposure_time_spin.setSingleStep(10.0)
        self.exposure_time_spin.setValue(self.dahengCamModel.get_exposureTime()) 
        self.exposure_time_unit_label = QLabel("ms")
        exposure_time_layout.addWidget(self.exposure_time_label)
        exposure_time_layout.addWidget(self.exposure_time_spin)
        exposure_time_layout.addWidget(self.exposure_time_unit_label)

        imageSettingsLayout.addLayout(exposure_time_layout)

        imageSettingsLayout.addStretch()
        
        # Add columns to main layout
        mainLayout.addLayout(imageCalibLayout)
        mainLayout.addLayout(imageSettingsLayout)

        self.setLayout(mainLayout)

    def resetTabWidgets(self):
        # Column for image settings
        self.interval_spin.setValue(self.dahengCamModel.get_intervalbild()) 
        self.save_raw_checkbox.setChecked(self.dahengCamModel.get_imgRaw())
        self.normalize_checkbox.setChecked(self.dahengCamModel.get_imgNorm())
        self.gain_spin.setValue(self.dahengCamModel.get_gain()) 
        self.exposure_time_spin.setValue(self.dahengCamModel.get_exposureTime()) 

    def expandWidgets(self):
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def handleNormalizeCheckboxStateChanged(self):
        self.dahengCamModel.set_imgNorm(self.normalize_checkbox.isChecked())

    def handleSaveRawCheckboxStateChanged(self):
        self.dahengCamModel.set_imgRaw(self.save_raw_checkbox.isChecked())

    def updateCalibCamImage(self):
        if self.dahengCamModel.get_successINIT():
            # get image height
            try:
                imgH = round(float(self.image_height_input.text()),0)
                self.error_img_height_2.setVisible(False)
            except (TypeError,ValueError):
                NimgH = 540
                self.error_img_height_2.setVisible(True)
            else:
                if(imgH > 540):
                    NimgH = 540
                    self.error_img_height.setVisible(True)
                elif(imgH < 300):
                    NimgH = 300
                    self.error_img_height.setVisible(True)
                else:
                    NimgH = imgH
                    self.error_img_height.setVisible(False)

            # get image width
            try:
                NimgW = round(self.aspect_ratio_spin.value()*NimgH, -1)
                self.error_aspect_ratio.setVisible(False)
            except (TypeError,ValueError):
                NimgW = NimgH
                self.error_aspect_ratio.setVisible(True)

            gain = self.gain_spin.value()
            
            exposure_time = self.exposure_time_spin.value()

            #get repetition interval
            intervalbild = self.interval_spin.value()

            self.dahengCamModel.set_fmt(self.file_format_combo.currentText())

            #update settings of camera, if necessary
            self.dahengCamModel.queryUpdateCamSettings(gain, exposure_time, intervalbild, NimgW, NimgH)

            self.image_height_input.setText(f"{self.dahengCamModel.get_imgH()}")

            #get image
            #img = self.dahengCamModel.getImage(image_format)
            image_updated, img = self.dahengCamModel.getLatestImage()
            
            if image_updated:
                im = ImageQt(img).copy()
                pixmap = QPixmap.fromImage(im)
                """
                imgbytes = self.dahengCamModel.getImage(image_format)

                # Create QPixmap instance
                pixmap = QPixmap(self.dahengCamModel.get_imgW(), self.dahengCamModel.get_imgH())

                # Put bytes of example.bmp into it
                pixmap.loadFromData(imgbytes)
                """

                # Update image by applying the pixmap to the label
                self.image_label.setPixmap(pixmap) 
