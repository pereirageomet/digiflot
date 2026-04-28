"""Module providing the calibration UI widget for Raspberry Pi cameras.

This module defines the TabViewCalibCamRaspi class, a QWidget that displays
live camera feed and controls for image acquisition settings (gain, exposure,
brightness, etc.) and supports multi‑camera selection via a dropdown.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QLineEdit, QSizePolicy)
from PyQt5.QtGui import QPixmap
import logging
logger = logging.getLogger(__name__)


class TabViewCalibCamRaspi(QWidget):
    """Calibration tab for Raspberry Pi cameras with multi‑camera selector."""
    def __init__(self, camAdapter):
        super().__init__()
        self.camAdapter = camAdapter  # holds list of RaspiCamModel instances
        self._active_index = 0  # track active camera index locally
        self.initUI()


    def initUI(self):
        """Initialize the user interface layout and widgets."""
        # Create main layout
        mainLayout = QHBoxLayout()
        # Camera selector (if multiple cameras)
        if len(self.camAdapter._cam_handles) > 1:
            selectorLayout = QVBoxLayout()
            selectorLabel = QLabel("Select Camera")
            self.camera_selector = QComboBox()
            for idx, cam in enumerate(self.camAdapter._cam_handles):
                self.camera_selector.addItem(f"Camera {idx}")
            self.camera_selector.setCurrentIndex(self._active_index)
            self.camera_selector.currentIndexChanged.connect(self.changeCamera)
            selectorLayout.addWidget(selectorLabel)
            selectorLayout.addWidget(self.camera_selector)
            mainLayout.addLayout(selectorLayout)

        # Column for image calibration
        imageCalibLayout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setPixmap(QPixmap(''))
        imageCalibLayout.addWidget(self.image_label)

        color_space_group = QGroupBox("Color space")
        color_space_layout = QVBoxLayout()
        self.color_space_combo = QComboBox()
        self.color_space_combo.addItems(["GRAY", "HSV", "RGB"])
        self.color_space_combo.setCurrentText("RGB")
        color_space_layout.addWidget(self.color_space_combo)
        color_space_group.setLayout(color_space_layout)
        imageCalibLayout.addWidget(color_space_group)
        
        resolution_group = QGroupBox("Camera Resolution")
        resolution_layout = QVBoxLayout()
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["25%", "33%", "50%", "75%", "100%"])
        self.resolution_combo.setCurrentIndex(1)
        self._resolution_pct = 33
        self.resolution_combo.currentIndexChanged.connect(self.handleResolutionChanged)
        resolution_layout.addWidget(self.resolution_combo)
        resolution_group.setLayout(resolution_layout)
        imageCalibLayout.addWidget(resolution_group)
        
        imageCalibLayout.addStretch()
        
        # Column for image settings
        imageSettingsLayout = QVBoxLayout()
        
        self.image_height_label = QLabel("Image height (px):")
        self.image_height_label.setVisible(False)
        self.image_height_input = QLineEdit("480")
        self.image_height_input.setVisible(False)
        imageSettingsLayout.addWidget(self.image_height_label)
        imageSettingsLayout.addWidget(self.image_height_input)
        
        aspect_ratio_layout = QHBoxLayout()
        self.aspect_ratio_label = QLabel("Aspect ratio: ")
        self.aspect_ratio_label.setVisible(False)
        self.aspect_ratio_spin = QSpinBox()
        self.aspect_ratio_spin.setRange(4, 20)  # Equivalent to 0.4 to 2 in steps of 0.2
        self.aspect_ratio_spin.setSingleStep(2)
        self.aspect_ratio_spin.setValue(10)  # Equivalent to 1.0
        self.aspect_ratio_spin.setVisible(False)
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
        self.interval_spin.setRange(0.01, 2.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(self.camAdapter._cam_handles[self._active_index].get_intervalbild()) 
        self.interval_unit_label = QLabel("s")
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(self.interval_unit_label)
        imageSettingsLayout.addLayout(interval_layout)
        
        self.save_raw_checkbox = QCheckBox("Save raw image?")
        self.save_raw_checkbox.setChecked(self.camAdapter._cam_handles[self._active_index].get_imgRaw())
        self.save_raw_checkbox.stateChanged.connect(self.handleSaveRawCheckboxStateChanged)        
        imageSettingsLayout.addWidget(self.save_raw_checkbox)
        
        self.normalize_checkbox = QCheckBox("Normalize image?")
        self.normalize_checkbox.setChecked(self.camAdapter._cam_handles[self._active_index].get_imgNorm())
        self.normalize_checkbox.stateChanged.connect(self.handleNormalizeCheckboxStateChanged)
        self.normalize_checkbox.setVisible(False)
        imageSettingsLayout.addWidget(self.normalize_checkbox)
        
        gain_layout = QHBoxLayout()
        self.gain_label = QLabel("Gain: ")
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(1.0, 22.0)
        self.gain_spin.setSingleStep(0.1)
        self.gain_spin.setValue(self.camAdapter._cam_handles[self._active_index].get_gain()) 
        gain_layout.addWidget(self.gain_label)
        gain_layout.addWidget(self.gain_spin)
        imageSettingsLayout.addLayout(gain_layout)

        exposure_time_layout = QHBoxLayout()
        self.exposure_time_label = QLabel("Exposure Time: ")
        self.exposure_time_spin = QDoubleSpinBox()
        self.exposure_time_spin.setRange(0.06, 10000.0)
        self.exposure_time_spin.setSingleStep(10.0)
        self.exposure_time_spin.setValue(self.camAdapter._cam_handles[self._active_index].get_exposureTime()) 
        self.exposure_time_unit_label = QLabel("ms")
        exposure_time_layout.addWidget(self.exposure_time_label)
        exposure_time_layout.addWidget(self.exposure_time_spin)
        exposure_time_layout.addWidget(self.exposure_time_unit_label)
        imageSettingsLayout.addLayout(exposure_time_layout)

        brightness_layout = QHBoxLayout()
        self.brightness_label = QLabel("Image brightness")
        self.brightness_spin = QDoubleSpinBox()
        self.brightness_spin.setRange(-1, 1)
        self.brightness_spin.setSingleStep(0.1)
        self.brightness_spin.setValue(self.camAdapter._cam_handles[self._active_index].get_imgB())
        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_spin)
        brightness_layout.addWidget(QLabel("[-1:1]"))
        imageSettingsLayout.addLayout(brightness_layout)
        
        contrast_layout = QHBoxLayout()
        self.contrast_label = QLabel("Image contrast")
        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(0, 32)
        self.contrast_spin.setValue(int(self.camAdapter._cam_handles[self._active_index].get_imgC()))
        contrast_layout.addWidget(self.contrast_label)
        contrast_layout.addWidget(self.contrast_spin)
        contrast_layout.addWidget(QLabel("[0:32]"))
        imageSettingsLayout.addLayout(contrast_layout)
        
        saturation_layout = QHBoxLayout()
        self.saturation_label = QLabel("Image saturation")
        self.saturation_spin = QSpinBox()
        self.saturation_spin.setRange(0, 32)
        self.saturation_spin.setValue(int(self.camAdapter._cam_handles[self._active_index].get_imgS()))
        saturation_layout.addWidget(self.saturation_label)
        saturation_layout.addWidget(self.saturation_spin)
        saturation_layout.addWidget(QLabel("[0:32]"))
        imageSettingsLayout.addLayout(saturation_layout)

        sharpness_layout = QHBoxLayout()
        self.sharpness_label = QLabel("Image sharpness")
        self.sharpness_spin = QSpinBox()
        self.sharpness_spin.setRange(0, 16)
        self.sharpness_spin.setValue(int(self.camAdapter._cam_handles[self._active_index].get_imageSharpness()))
        sharpness_layout.addWidget(self.sharpness_label)
        sharpness_layout.addWidget(self.sharpness_spin)
        sharpness_layout.addWidget(QLabel("[0:16]"))
        imageSettingsLayout.addLayout(sharpness_layout)

        imageSettingsLayout.addStretch()
        
        # Add columns to main layout
        mainLayout.addLayout(imageCalibLayout)
        mainLayout.addLayout(imageSettingsLayout)

        self.setLayout(mainLayout)

    def resetTabWidgets(self):
        """Reset all UI widget values to match the active camera's current settings."""
        cam = self.camAdapter._cam_handles[self._active_index]
        # Column for image settings
        self.interval_spin.setValue(cam.get_intervalbild()) 
        self.save_raw_checkbox.setChecked(cam.get_imgRaw())
        self.normalize_checkbox.setChecked(cam.get_imgNorm())
        self.gain_spin.setValue(cam.get_gain()) 
        self.exposure_time_spin.setValue(cam.get_exposureTime()) 
        self.brightness_spin.setValue(cam.get_imgB())
        self.contrast_spin.setValue(int(cam.get_imgC()))
        self.saturation_spin.setValue(int(cam.get_imgS()))
        self.sharpness_spin.setValue(int(cam.get_imageSharpness()))

    def expandWidgets(self):
        """Set the image label to expand and fill available space."""
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def changeCamera(self, index):
        """Switch active camera and refresh UI widgets."""
        self._active_index = index
        self.camAdapter._active_index = index
        self.resetTabWidgets()

    def handleResolutionChanged(self, index):
        """Update resolution percentage based on combo box selection."""
        resolution_values = [25, 33, 50, 75, 100]
        self._resolution_pct = resolution_values[index]

    def handleNormalizeCheckboxStateChanged(self):
        """Update the active camera's normalization setting based on checkbox state."""
        self.camAdapter._cam_handles[self._active_index].set_imgNorm(self.normalize_checkbox.isChecked())
        
    def handleSaveRawCheckboxStateChanged(self):
        """Update the active camera's raw image saving setting based on checkbox state."""
        self.camAdapter._cam_handles[self._active_index].set_imgRaw(self.save_raw_checkbox.isChecked())

    def updateCalibCamImage(self):
        """Fetch and display the latest image from the active camera, applying current color space and settings."""
        if self.camAdapter._cam_handles[self._active_index].get_successINIT():
            cam = self.camAdapter._cam_handles[self._active_index]
            # get image height
            try:
                imgH = round(float(self.image_height_input.text()),0)
            except (TypeError,ValueError):
                NimgH = 480
            else:
                if(imgH > 480):
                    NimgH = 480
                else:
                    NimgH = imgH

            # get image width
            try:
                NimgW = round(self.aspect_ratio_spin.value()/10*640/480*NimgH, 0)
            except (TypeError,ValueError):
                NimgW = 640
            
            # get image brightness, contrast and saturation
            NimgB = self.brightness_spin.value()
            NimgC = self.contrast_spin.value()
            NimgS = self.saturation_spin.value()
            new_image_sharpness = self.sharpness_spin.value()

            #analogue gain
            gain = self.gain_spin.value()
            
            #exposure time
            exposure_time = self.exposure_time_spin.value()

            #get repetition interval
            intervalbild = self.interval_spin.value()

            #update settings of camera, if necessary
            cam.queryUpdateCamSettings(intervalbild, gain, exposure_time, NimgW, NimgH, NimgB, NimgC, NimgS, new_image_sharpness)

            #get image
            image_format = self.color_space_combo.currentText()
            image_updated, imgbytes = cam.getLatestImage(image_format, self._resolution_pct)

            if image_updated:
                # Create QPixmap instance (use scaled dimensions)
                target_w = max(1, round(cam.getImageWidth() * self._resolution_pct / 100))
                target_h = max(1, round(cam.getImageHeight() * self._resolution_pct / 100))
                pixmap = QPixmap(target_w, target_h)

                # Put bytes of example.bmp into it
                pixmap.loadFromData(imgbytes)

                # Update image by applying the pixmap to the label
                self.image_label.setPixmap(pixmap)
