"""Adapter for camera acquisition systems supporting Raspberry Pi and Daheng cameras.

This module provides a unified interface to manage camera acquisition through
different camera models (Raspberry Pi Camera or Daheng camera). It uses a factory
pattern to instantiate the appropriate camera model and calibration view.
"""
import time
import logging
import multiprocessing as mp
import ctypes
import threading
from picamera2 import Picamera2

try:
    from libs.raspiCamModel import RaspiCamModel
    from libs.tabViewCalibCamRaspi import TabViewCalibCamRaspi
    from libs import raspiCamController
    from libs import configurationManager
except:
    from .raspiCamModel import RaspiCamModel
    from .tabViewCalibCamRaspi import TabViewCalibCamRaspi
    from . import raspiCamController
    from . import configurationManager

logger = logging.getLogger(__name__)
ctx = mp.get_context('spawn')

class CamAdapter:
    """Adapter for managing one or more Raspberry Pi cameras.

    Supports automatic discovery of all connected Pi cameras, creates a
    RaspiCamModel instance per camera and provides a single calibration tab
    with a drop‑down selector to choose which camera to adjust.
    """
    def __init__(self, taskModel, className="RaspiCamModel"):
        """Initialize CamAdapter.

        Args:
            taskModel: TaskModel instance.
            className: Currently only "RaspiCamModel" is supported.
        """
        self.className = className
        self._controller = None
        self._image_arrays = []
        self._cam_handles = []
        self._active_index = 0
        self._initialized = False

        self._create_cameras(taskModel)
        self._tabViewCalibCamRaspi = self._create_calib_tab()

    def cleanup(self):
        """Explicit cleanup method - call before adapter destruction."""
        self.finishProcessesAndQueues()

    def _create_cameras(self, taskModel):
        """Discover Raspberry Pi cameras and instantiate RaspiCamModel for each.

        Populates ``self._cam_handles`` and ``self._image_arrays``.
        """
        cam_infos = Picamera2.global_camera_info()
        
        for idx, info in enumerate(cam_infos):
            picam2 = Picamera2(idx)
            config = picam2.create_still_configuration(main={"format": 'RGB888'})
            imageWidth = config["main"]["size"][0]
            imageHeight = config["main"]["size"][1]
            nof_pixel_values = 3
            picam2.close()
            
            img_array = ctx.Array(ctypes.c_uint8, imageHeight * imageWidth * nof_pixel_values)
            cam_handle = RaspiCamModel(
                configurationManager.getConfig("RaspiCamModel"),
                taskModel,
                img_array,
                imageHeight,
                imageWidth,
                nof_pixel_values,
                idx,
            )
            self._cam_handles.append(cam_handle)
            self._image_arrays.append(img_array)

    def _create_calib_tab(self):
        """Create the calibration UI tab linked to this adapter."""
        return TabViewCalibCamRaspi(self)

    def getCamInstance(self):
        """Return the currently active camera model instance."""
        if self._cam_handles:
            return self._cam_handles[self._active_index]
        return None

    def getCalibCamInstance(self):
        """Return the calibration view instance (shared for all cameras)."""
        return self._tabViewCalibCamRaspi

    def instantiateTabViewCalibCam(self):
        """Create the calibration view (used only during init)."""
        return TabViewCalibCamRaspi(self)

    def startStream(self):
        """Start acquisition for all cameras in main process.

        Initializes all cameras with proper SyncMode (Server for camera 0, Client for others)
        and starts a background capture loop. Cameras run in the same process to enable
        proper synchronization.
        """
        conf_dict = configurationManager.getConfig("RaspiCamModel")
        image_heights = []
        image_widths = []
        nof_pixel_values_list = []
        
        for cam_handle in self._cam_handles:
            h, w, n = cam_handle.getImageParameters()
            image_heights.append(h)
            image_widths.append(w)
            nof_pixel_values_list.append(n)
        
        self._controller = raspiCamController.RaspiCamController(conf_dict)
        result = self._controller.startCameras(
            self._image_arrays,
            image_heights,
            image_widths,
            nof_pixel_values_list
        )
        
        if result["success"]:
            interval = conf_dict.get("image interval", 0.5)
            self._controller.startCaptureLoop(interval)
            
            for cam_handle in self._cam_handles:
                cam_handle.set_successINIT(True)
                cam_handle.set_colorCAM("green")
                cam_handle.set_camCalib(True)
        else:
            logger.error(f"Camera initialization failed: {result.get('error', 'Unknown error')}")
            for cam_handle in self._cam_handles:
                cam_handle.set_successINIT(False)
                cam_handle.set_colorCAM("red")
                cam_handle.set_camCalib(False)
        
        self._initialized = True

    def continueStream(self):
        """Resume acquisition for all cameras."""
        if hasattr(self, '_controller') and self._controller.isRunning():
            conf_dict = configurationManager.getConfig("RaspiCamModel")
            interval = conf_dict.get("image interval", 0.5)
            self._controller.startCaptureLoop(interval)

    def pauseStream(self):
        """Pause acquisition for all cameras."""
        if hasattr(self, '_controller'):
            self._controller.stopCaptureLoop()

    def finishProcessesAndQueues(self):
        """Stop cameras and cleanup."""
        if not self._initialized:
            return

        if hasattr(self, '_controller'):
            self._controller.stopCameras()
            delattr(self, '_controller')

        self._initialized = False

    def isRunning(self):
        return hasattr(self, '_controller') and self._controller.isRunning()
