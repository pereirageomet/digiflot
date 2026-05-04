"""Module docstring."""
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
    def __init__(self, configuration, taskModel, image_array, imageHeight, imageWidth, nof_pixel_values, camera_index=None):
        self.configuration = configuration

        self.taskModel = taskModel
        self.image_array = image_array        
                
        self.colorCAM = "red"
        self.imageHeight = imageHeight
        self.imageWidth = imageWidth
        self.nof_pixel_values = nof_pixel_values
        self.camCalib = False
        self.successINIT = False
        # Store camera index
        self.camera_index = camera_index if camera_index is not None else 0
        # Ensure per‑camera configuration exists in the shared config
        cams_cfg = self.configuration.get("cameras")
        if cams_cfg is None:
            cams_cfg = {}
            self.configuration["cameras"] = cams_cfg
        # Support dict or list storage for per‑camera configs
        if isinstance(cams_cfg, dict):
            cam_cfg = cams_cfg.get(self.camera_index, {})
        elif isinstance(cams_cfg, list):
            # Extend list if needed
            while len(cams_cfg) <= self.camera_index:
                cams_cfg.append({})
            cam_cfg = cams_cfg[self.camera_index]
        else:
            cam_cfg = {}
        # Populate defaults if missing
        defaults = {
            "image interval": self.configuration.get("image interval", 0.5),
            "gain": self.configuration.get("gain", 1.0),
            "exposure time": self.configuration.get("exposure time", 200),
            "brightness": self.configuration.get("brightness", 0),
            "contrast": self.configuration.get("contrast", 1),
            "saturation": self.configuration.get("saturation", 1),
            "sharpness": self.configuration.get("sharpness", 1),
            "normalize image": self.configuration.get("normalize image", False),
            "output raw image": self.configuration.get("output raw image", False),
            "image format": self.configuration.get("image format", "png"),
            "name": self.configuration.get("name", f"Camera_{self.camera_index}"),
        }
        cam_cfg = {**defaults, **cam_cfg}
        # Store back depending on container type
        if isinstance(cams_cfg, dict):
            cams_cfg[self.camera_index] = cam_cfg
        elif isinstance(cams_cfg, list):
            cams_cfg[self.camera_index] = cam_cfg
        # Alias to per‑camera config for easy access
        self.camera_config = cam_cfg

        self.last_fetched_image = None

    def getImageParameters(self):
        return self.imageHeight, self.imageWidth, self.nof_pixel_values

    def get_taskModel(self):
        return self.taskModel

    def set_taskModel(self, value):
        self.taskModel = value

    def get_gain(self):
        return self.camera_config["gain"]

    def set_gain(self, value):
        self.camera_config["gain"] = value

    def get_exposureTime(self):
        return self.camera_config["exposure time"]

    def set_exposureTime(self, value):
        self.camera_config["exposure time"] = value

    def get_intervalbild(self):
        return self.camera_config["image interval"]

    def set_intervalbild(self, value):
        self.camera_config["image interval"] = value

    def get_imgB(self):
        return self.camera_config["brightness"]

    def set_imgB(self, value):
        self.camera_config["brightness"] = value

    def get_imgC(self):
        return self.camera_config["contrast"]

    def set_imgC(self, value):
        self.camera_config["contrast"] = value

    def get_imgS(self):
        return self.camera_config["saturation"]

    def set_imgS(self, value):
        self.camera_config["saturation"] = value

    def get_imageSharpness(self):
        return self.camera_config["sharpness"]

    def set_imageSharpness(self, value):
        self.camera_config["sharpness"] = value

    def get_imgNorm(self):
        return self.camera_config["normalize image"]

    def set_imgNorm(self, value):
        self.camera_config["normalize image"] = value

    def get_imgRaw(self):
        return self.camera_config["output raw image"]

    def set_imgRaw(self, value):
        self.camera_config["output raw image"] = value

    def get_fmt(self):
        return self.camera_config["image format"]

    def set_fmt(self, value):
        self.camera_config["image format"] = value

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
                self.last_fetched_image = np.frombuffer(self.image_array.get_obj(), dtype=np.uint8).reshape((int(m), int(n), int(o))).copy()
            return True, self.last_fetched_image

    def getLatestImage(self, image_format="", scale_pct=100):
        if not self.connectedSuccessfully():
            return False, None

        image_updated, image = self.getLatestUnformattedImage()            
        
        if image is None:
            return False, self.last_fetched_image

        # Downscale if requested
        if scale_pct < 100:
            target_w = max(1, round(self.imageWidth * scale_pct / 100))
            target_h = max(1, round(self.imageHeight * scale_pct / 100))
            image = cv2.resize(image, (target_w, target_h), interpolation=cv2.INTER_AREA)

        #if self.configuration["normalize image"]:
        #    image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        #cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        if image_format == "GRAY":
            imgbytes=cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_RGB2GRAY))[1].tobytes()
        elif image_format == "HSV":
            imgbytes=cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_RGB2HSV))[1].tobytes()
        elif image_format == "RGB":
            imgbytes=cv2.imencode('.png', image)[1].tobytes()
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
        dct = {"stagename" : self.taskModel.currentstagename, "fmt" : self.camera_config["image format"], "samplefolder" : str(self.taskModel.samplefolder), "imgRaw" : self.camera_config["output raw image"], "camera_name" : self.camera_config.get("name", f"Camera_{self.camera_index}") }
        return dct

    def queryUpdateCamSettings(self, intervalbild, gain, exposureTime, NimageWidth, NimageHeight, NimageBrightness, NimageContrast, NimageSaturation, NimageSharpness):
        """Update per‑camera settings if they differ from current values.
        Returns a dict of changed settings (keys match controller expectations).
        """
        changed = {}
        cfg = self.camera_config
        # interval
        if cfg.get("image interval") != intervalbild:
            cfg["image interval"] = intervalbild
            changed["image interval"] = intervalbild
        # gain
        if cfg.get("gain") != gain:
            cfg["gain"] = gain
            changed["gain"] = gain
        # exposure time
        if cfg.get("exposure time") != exposureTime:
            cfg["exposure time"] = exposureTime
            changed["exposure time"] = exposureTime
        # brightness
        if cfg.get("brightness") != NimageBrightness:
            cfg["brightness"] = NimageBrightness
            changed["brightness"] = NimageBrightness
        # contrast
        if cfg.get("contrast") != NimageContrast:
            cfg["contrast"] = NimageContrast
            changed["contrast"] = NimageContrast
        # saturation
        if cfg.get("saturation") != NimageSaturation:
            cfg["saturation"] = NimageSaturation
            changed["saturation"] = NimageSaturation
        # sharpness
        if cfg.get("sharpness") != NimageSharpness:
            cfg["sharpness"] = NimageSharpness
            changed["sharpness"] = NimageSharpness
        return changed
