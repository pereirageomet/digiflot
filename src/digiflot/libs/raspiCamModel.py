import logging
logger = logging.getLogger(__name__)
import cv2
from PIL import Image
import io
import numpy as np

#image functions
def variance_of_laplacian(imgbytes):
    # compute the Laplacian of the image and then return the focus
    # measure, which is simply the variance of the Laplacian
    return cv2.Laplacian(imgbytes, cv2.CV_64F).var()

class RaspiCamModel():
    def __init__(self, configuration, taskModel, message_queue, image_array, imageHeight, imageWidth, nof_pixel_values):
        self.configuration = configuration

        self.taskModel = taskModel
        self.message_queue = message_queue
        self.image_array = image_array        
                
        self.colorCAM = "red"
        self.imageHeight = imageHeight
        self.imageWidth = imageWidth
        self.nof_pixel_values = nof_pixel_values
        self.camCalib = False
        self.successINIT = False

        self.last_fetched_image = None

    def getImageParameters(self):
        return self.imageHeight, self.imageWidth, self.nof_pixel_values

    def get_taskModel(self):
        return self.taskModel

    def set_taskModel(self, value):
        self.taskModel = value

    def get_gain(self):
        return self.configuration["gain"]

    def set_gain(self, value):
        self.configuration["gain"] = value

    def get_exposureTime(self):
        return self.configuration["exposure time"]

    def set_exposureTime(self, value):
        self.configuration["exposure time"] = value

    def get_intervalbild(self):
        return self.configuration["image interval"]

    def set_intervalbild(self, value):
        self.configuration["image interval"] = value

    def get_imgB(self):
        return self.configuration["brightness"]

    def set_imgB(self, value):
        self.configuration["brightness"] = value

    def get_imgC(self):
        return self.configuration["contrast"]

    def set_imgC(self, value):
        self.configuration["contrast"] = value

    def get_imgS(self):
        return self.configuration["saturation"]

    def set_imgS(self, value):
        self.configuration["saturation"] = value

    def get_imageSharpness(self):
        return self.configuration["sharpness"]

    def set_imageSharpness(self, value):
        self.configuration["sharpness"] = value

    def get_imgNorm(self):
        return self.configuration["normalize image"]

    def set_imgNorm(self, value):
        self.configuration["normalize image"] = value

    def get_imgRaw(self):
        return self.configuration["output raw image"]

    def set_imgRaw(self, value):
        self.configuration["output raw image"] = value

    def get_fmt(self):
        return self.configuration["image format"]

    def set_fmt(self, value):
        self.configuration["image format"] = value

    def get_colorCAM(self):
        return self.colorCAM

    def set_colorCAM(self, value):
        self.colorCAM = value

    def get_camCalib(self):
        return self.camCalib

    def set_camCalib(self, value):
        self.camCalib = value

    def get_successINIT(self):
        return self.successINIT

    def set_successINIT(self, value):
        self.successINIT = value

    def get_image(self):
        return self.last_fetched_image

    def set_image(self, value):
        self.last_fetched_image = value

    def getImageWidth(self):
        return self.imageWidth
    
    def getImageHeight(self):
        return self.imageHeight

    def connectedSuccessfully(self):
        return self.successINIT

    def getLatestUnformattedImage(self):
            m, n, o = self.getImageParameters()
            # then in each new process create a new numpy array using:
            with self.image_array.get_lock():
                self.last_fetched_image = np.frombuffer(self.image_array.get_obj(), dtype=np.uint8).reshape((m,n,o)).copy()
            return True, self.last_fetched_image

    def getLatestImage(self, image_format=""):
        if not self.connectedSuccessfully():
            return False, None

        image_updated, image = self.getLatestUnformattedImage()            
        
        if image is None:
            return False, self.last_fetched_image

        #if self.configuration["normalize image"]:
        #    image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        #cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if image_format == "GRAY":
            imgbytes=cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))[1].tobytes()
        elif image_format == "HSV":
            imgbytes=cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_BGR2HSV))[1].tobytes()
        elif image_format == "RGB":
            imgbytes=cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_BGR2RGB))[1].tobytes()
        elif image_format == "TIFF":
            # Image is fetched, converted to tiff, written into a buffer for finally forwarding it to a online storage system
            image_pil = Image.fromarray(image)
            with io.BytesIO() as byte_buffer:
                image_pil.save(byte_buffer, format="TIFF")
                imgbytes = byte_buffer.getvalue()
        else:
            imgbytes=cv2.imencode('.png', image)[1].tobytes()
        return image_updated, imgbytes

    def getImageDictForSavingOffline(self):
        self.getLatestUnformattedImage()
        #dct = {"image" : self.last_fetched_image, "stagename" : self.taskModel.currentstagename, "fmt" : self.configuration["image format"], "samplefolder" : str(self.taskModel.samplefolder), "imgRaw" : self.configuration["output raw image"]}
        dct = {"stagename" : self.taskModel.currentstagename, "fmt" : self.configuration["image format"], "samplefolder" : str(self.taskModel.samplefolder), "imgRaw" : self.configuration["output raw image"]}
        return dct

    def queryUpdateCamSettings(self, intervalbild, gain, exposureTime, NimageWidth, NimageHeight, NimageBrightness, NimageContrast, NimageSaturation, NimageSharpness):
        if self.configuration["image interval"] != intervalbild or self.configuration["gain"] != gain or self.configuration["exposure time"] != exposureTime or NimageWidth != self.imageWidth or NimageHeight != self.imageHeight or NimageBrightness != self.configuration["brightness"] or NimageContrast != self.configuration["contrast"] or NimageSaturation != self.configuration["saturation"] or NimageSharpness != self.configuration["sharpness"]:
            dct = {}
            dct["intervalbild_query"] = intervalbild
            dct["gain_query"] = gain
            dct["exposureTime_query"] = exposureTime
            dct["imageHeight_query"] = NimageHeight
            dct["imageWidth_query"] = NimageWidth
            dct["imageBrightness_query"] = NimageBrightness
            dct["imageContrast_query"] = NimageContrast
            dct["imageSaturation_query"] = NimageSaturation
            dct["imageSharpness_query"] = NimageSharpness
            dct["message"] = "LOAD"
            self.message_queue.put(dct)