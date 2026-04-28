"""Module providing the Daheng camera model.

This module defines the DahengCamModel class for managing Daheng camera
configuration, image acquisition parameters, and communication with the
subprocess handling camera operations.
"""
import logging
logger = logging.getLogger(__name__)
import io
import numpy as np
import cv2
from PIL import Image

class DahengCamModel():
    """Model class for Daheng camera configuration and image handling."""
    def __init__(self, configuration, taskModel, message_queue, image_array, imageHeight, imageWidth, nof_pixel_values):
        """Initialize the Daheng camera model with configuration and shared resources.

        :param configuration: Dictionary storing camera settings
        :param taskModel: Reference to the main task model
        :param message_queue: Queue for communicating with the camera subprocess
        :param image_array: Shared memory array for image data
        :param imageHeight: Height of images in pixels
        :param imageWidth: Width of images in pixels
        :param nof_pixel_values: Number of color channels
        """
        self.configuration = configuration
        self.camera_trademark = "Daheng"

        self.taskModel = taskModel

        self.image_array = image_array
        self.message_queue = message_queue

        #configuration
        self.colorCAM = "red"
        self.configuration["image format"] = "png"
        self.imgW = imageWidth
        self.imgH = imageHeight
        self.nof_pixel_values = nof_pixel_values

        self.successINIT = False 
        self.camCalib = False   

        self.last_fetched_image = None

    def getImageParameters(self):
        """Return image dimensions and channel count.

        :return: Tuple of (height, width, channels)
        """
        return self.imgH, self.imgW, self.nof_pixel_values

    def get_taskModel(self):
        """Get the task model reference.

        :return: taskModel instance
        """
        return self.taskModel

    def set_taskModel(self, value):
        """Set the task model reference.

        :param value: taskModel instance to set
        """
        self.taskModel = value

    def get_colorCAM(self):
        """Get the camera color mode.

        :return: Color mode string (e.g., "red")
        """
        return self.colorCAM

    def set_colorCAM(self, value):
        """Set the camera color mode.

        :param value: Color mode string to set
        """
        self.colorCAM = value

    def get_intervalbild(self):
        """Get the image capture interval.

        :return: Image interval value
        """
        return self.configuration["image interval"]

    def set_intervalbild(self, value):
        """Set the image capture interval.

        :param value: Image interval value to set
        """
        self.configuration["image interval"] = value

    def get_exposureTime(self):
        """Get the camera exposure time.

        :return: Exposure time value
        """
        return self.configuration["exposure time"]

    def set_exposureTime(self, value):
        """Set the camera exposure time.

        :param value: Exposure time value to set
        """
        self.configuration["exposure time"] = value

    def get_gain(self):
        """Get the camera gain setting.

        :return: Gain value
        """
        return self.configuration["gain"]

    def set_gain(self, value):
        """Set the camera gain setting.

        :param value: Gain value to set
        """
        self.configuration["gain"] = value

    def get_imgNorm(self):
        """Get the image normalization setting.

        :return: Normalization setting
        """
        return self.configuration["normalize image"]

    def set_imgNorm(self, value):
        """Set the image normalization setting.

        :param value: Normalization setting to set
        """
        self.configuration["normalize image"] = value

    def get_imgRaw(self):
        """Get the raw image output setting.

        :return: Raw output setting
        """
        return self.configuration["output raw image"]

    def set_imgRaw(self, value):
        """Set the raw image output setting.

        :param value: Raw output setting to set
        """
        self.configuration["output raw image"] = value

    def get_successINIT(self):
        """Get the initialization success status.

        :return: Boolean indicating successful initialization
        """
        return self.successINIT

    def set_successINIT(self, value):
        """Set the initialization success status.

        :param value: Boolean value to set
        """
        self.successINIT = value

    def get_fmt(self):
        """Get the image format setting.

        :return: Image format string (e.g., "png")
        """
        return self.configuration["image format"]

    def set_fmt(self, value):
        """Set the image format setting.

        :param value: Image format string to set
        """
        self.configuration["image format"] = value

    def get_imgW(self):
        """Get the image width.

        :return: Image width in pixels
        """
        return self.imgW

    def set_imgW(self, value):
        """Set the image width.

        :param value: Image width in pixels to set
        """
        self.imgW = value

    def get_imgH(self):
        """Get the image height.

        :return: Image height in pixels
        """
        return self.imgH

    def set_imgH(self, value):
        """Set the image height.

        :param value: Image height in pixels to set
        """
        self.imgH = value

    def get_camCalib(self):
        """Get the camera calibration status.

        :return: Boolean indicating calibration status
        """
        return self.camCalib

    def set_camCalib(self, value):
        """Set the camera calibration status.

        :param value: Boolean value to set
        """
        self.camCalib = value

    def connectedSuccessfully(self):
        """Check if the camera connected successfully.

        :return: Boolean indicating successful connection
        """
        return self.successINIT

    def getLatestImage(self, image_format=""):
        """Fetch the latest image from shared memory and encode it.

        :param image_format: Format to encode the image ("TIFF" or default PNG)
        :return: Tuple of (success: bool, image_bytes: bytes or None)
        """
        if not self.connectedSuccessfully():
            return False, None

        m, n, o = self.getImageParameters()
        # then in each new process create a new numpy array using:
        with self.image_array.get_lock():
            self.last_fetched_image = np.frombuffer(self.image_array.get_obj(), dtype=np.uint8).reshape((m,n,o)).copy()

        if image_format == "TIFF":
            # Image is fetched, converted to tiff, written into a buffer for finally forwarding it to a online storage system
            image_pil = Image.fromarray(self.last_fetched_image)
            with io.BytesIO() as byte_buffer:
                image_pil.save(byte_buffer, format="TIFF")
                imgbytes = byte_buffer.getvalue()
        else:
            imgbytes = cv2.imencode('.png', self.last_fetched_image)[1].tobytes()

        return True, imgbytes

    def getImageDictForSavingOffline(self):
        """Create a dictionary with image data for offline storage.

        :return: Dictionary containing image, filename, format, and save settings
        """
        self.getLatestImage()
        dct = {"image" : self.last_fetched_image, "stagename" : self.taskModel.currentstagename, "fmt" : self.configuration["image format"], "samplefolder" : str(self.taskModel.samplefolder), "imgRaw" : self.configuration["output raw image"]}
        return dct

    def queryUpdateCamSettings(self, gain, exposureTime, intervalbild, NimageWidth, NimageHeight):
        """Send a message to update camera settings if any have changed.

        :param gain: New gain value
        :param exposureTime: New exposure time
        :param intervalbild: New image interval
        :param NimageWidth: New image width
        :param NimageHeight: New image height
        """
        if self.configuration["gain"] != gain or self.configuration["exposure time"] != exposureTime or self.configuration["image interval"] != intervalbild or NimageWidth != self.imgW or NimageHeight != self.imgH:
            dct = {}
            dct["intervalbild_query"] = intervalbild
            dct["gain_query"] = gain
            dct["exposureTime_query"] = exposureTime
            dct["imageHeight_query"] = NimageHeight
            dct["imageWidth_query"] = NimageWidth
            dct["message"] = "LOAD"            
            self.message_queue.put(dct)
