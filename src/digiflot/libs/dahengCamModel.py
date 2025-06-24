import logging
logger = logging.getLogger(__name__)
import io
import numpy as np
import cv2
from PIL import Image
class DahengCamModel():
    def __init__(self, configuration, taskModel, message_queue, image_array, imageHeight, imageWidth, nof_pixel_values):
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
        return self.imgH, self.imgW, self.nof_pixel_values

    def get_taskModel(self):
        return self.taskModel

    def set_taskModel(self, value):
        self.taskModel = value

    def get_colorCAM(self):
        return self.colorCAM

    def set_colorCAM(self, value):
        self.colorCAM = value

    def get_intervalbild(self):
        return self.configuration["image interval"]

    def set_intervalbild(self, value):
        self.configuration["image interval"] = value

    def get_exposureTime(self):
        return self.configuration["exposure time"]

    def set_exposureTime(self, value):
        self.configuration["exposure time"] = value

    def get_gain(self):
        return self.configuration["gain"]

    def set_gain(self, value):
        self.configuration["gain"] = value

    def get_imgNorm(self):
        return self.configuration["normalize image"]

    def set_imgNorm(self, value):
        self.configuration["normalize image"] = value

    def get_imgRaw(self):
        return self.configuration["output raw image"]

    def set_imgRaw(self, value):
        self.configuration["output raw image"] = value

    def get_successINIT(self):
        return self.successINIT

    def set_successINIT(self, value):
        self.successINIT = value

    def get_fmt(self):
        return self.configuration["image format"]

    def set_fmt(self, value):
        self.configuration["image format"] = value

    def get_imgW(self):
        return self.imgW

    def set_imgW(self, value):
        self.imgW = value

    def get_imgH(self):
        return self.imgH

    def set_imgH(self, value):
        self.imgH = value

    def get_camCalib(self):
        return self.camCalib

    def set_camCalib(self, value):
        self.camCalib = value

    def connectedSuccessfully(self):
        return self.successINIT

    def getLatestImage(self, image_format=""):
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
        self.getLatestImage()
        dct = {"image" : self.last_fetched_image, "stagename" : self.taskModel.currentstagename, "fmt" : self.configuration["image format"], "samplefolder" : str(self.taskModel.samplefolder), "imgRaw" : self.configuration["output raw image"]}
        return dct

    def queryUpdateCamSettings(self, gain, exposureTime, intervalbild, NimageWidth, NimageHeight):
        if self.configuration["gain"] != gain or self.configuration["exposure time"] != exposureTime or self.configuration["image interval"] != intervalbild or NimageWidth != self.imgW or NimageHeight != self.imgH:
            dct = {}
            dct["intervalbild_query"] = intervalbild
            dct["gain_query"] = gain
            dct["exposureTime_query"] = exposureTime
            dct["imageHeight_query"] = NimageHeight
            dct["imageWidth_query"] = NimageWidth
            dct["message"] = "LOAD"            
            self.message_queue.put(dct)