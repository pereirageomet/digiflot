import logging
logger = logging.getLogger(__name__)
import time
import pathlib
import numpy as np

try:
    from picamera2 import Picamera2
except:
    logger.error("Picamera2 is not installed.")
    Picamera2 = None

def adjustWidthAndHeightForAspectRatio(conf_dict, query_dict):
    NimageHeight = query_dict["imageHeight_query"]
    NimageWidth = query_dict["imageWidth_query"]

    aspect_ratio_of_camera = 640/480
    aspect_ratio = NimageWidth/NimageHeight
    if aspect_ratio < aspect_ratio_of_camera:
        height = 480
        width = round(480 * aspect_ratio)
    else:
        width = 640
        height = round(640 / aspect_ratio)

    conf_dict["imageHeight"] = height  
    conf_dict["imageWidth"] = width

def initCam(conf_dict):
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration())
        picam2.set_controls({"ExposureTime": int(conf_dict["exposure time"]*1000), 
                            "AnalogueGain": conf_dict["gain"],
                            "Brightness": conf_dict["brightness"],
                            "Contrast": conf_dict["contrast"],
                            "Saturation": conf_dict["saturation"],
                            "Sharpness": conf_dict["sharpness"]
                            })
        picam2.start()
        image = picam2.capture_array()
        if image is None:
            raise Exception("Camera connected? Correct settings?")
    except:
        successINIT = False
    else:
        successINIT = True

    if successINIT:
        return picam2, {"successINIT" : True, "colorCAM" : "green", "camCalib" : True}
    else:
        return None, {"successINIT" : False, "colorCAM" : "red", "camCalib" : False}

def updateCamSettings(picam2, conf_dict, query_dict):
    #normally it takes really long to update these values. therefore we should only update the camera settings if values have changed
    #set software interval
    intervalbild = query_dict["intervalbild_query"]
    gain = query_dict["gain_query"]
    exposureTime = query_dict["exposureTime_query"]
    NimageWidth = query_dict["imageWidth_query"]
    NimageHeight = query_dict["imageHeight_query"]
    NimageBrightness = query_dict["imageBrightness_query"]
    NimageContrast = query_dict["imageContrast_query"]
    NimageSaturation = query_dict["imageSaturation_query"]
    NimageSharpness = query_dict["imageSharpness_query"]

    controls_dict = {}

    if conf_dict["image interval"] != intervalbild:
        conf_dict["image interval"] = intervalbild

    if conf_dict["gain"] != gain:
        if gain < 1.0:
            conf_dict["gain"] = 1.0
            controls_dict["AnalogueGain"] = 1.0
        elif gain > 22.26086:
            conf_dict["gain"] = 22.26086
            controls_dict["AnalogueGain"] = 22.26086
        else:
            conf_dict["gain"] = gain
            controls_dict["AnalogueGain"] = gain

    #Software tracks ms, but actually µs are set
    if conf_dict["exposure time"] != exposureTime:
        if exposureTime < 60/1000:#ms
            exposureTime = 60/1000
        conf_dict["exposure time"] = round(exposureTime*1000)/1000
        controls_dict["ExposureTime"] = round(exposureTime*1000) #must be int and in µs

    # change of imageWidth and Height is not supported at the moment, because the nof pixels is fixed by the shared array
    ##check image width and height
    #if NimageWidth != conf_dict["imageWidth"] or NimageHeight != conf_dict["imageHeight"]: 
    #    adjustWidthAndHeightForAspectRatio(conf_dict, query_dict)

    #check image brigthness
    if NimageBrightness != conf_dict["brightness"]:
        if NimageBrightness < -1.0:
            NimageBrightness = -1.0
        elif NimageBrightness > 1.0:
            NimageBrightness = 1.0
        conf_dict["brightness"] = NimageBrightness
        controls_dict["Brightness"] = NimageBrightness

    #check image contrast
    if NimageContrast != conf_dict["contrast"]:
        if NimageContrast < 0.0:
            NimageContrast = 0.0
        elif NimageContrast > 32.0:
            NimageContrast = 32.0
        conf_dict["contrast"] = NimageContrast
        controls_dict["Contrast"] = NimageContrast

    #check image saturation
    if NimageSaturation != conf_dict["saturation"]:
        if NimageSaturation < 0.0:
            NimageSaturation = 0.0
        elif NimageSaturation > 32.0:
            NimageSaturation = 32.0
        conf_dict["saturation"] = NimageSaturation
        controls_dict["Saturation"] = NimageSaturation

    if NimageSharpness != conf_dict["sharpness"]:
        if NimageSharpness < 0.0:
            NimageSharpness = 0.0
        elif NimageSharpness > 16.0:
            NimageSharpness = 16.0
        conf_dict["sharpness"] = NimageSharpness
        controls_dict["Sharpness"] = NimageSharpness

    #check for entries into controls_dict and then set it
    if controls_dict != {}:
        picam2.set_controls(controls_dict)


"""
def takePicture(picam2, image_queue, conf_dict):
    image = picam2.capture_array()
        
    h = conf_dict["imageHeight"]  
    w = conf_dict["imageWidth"]

    margin_h = (480 - h) // 2
    margin_w = (640 - w) // 2

    image[margin_h:480-margin_h, margin_w:640-margin_w, :]
"""

def takePicture(picam2, image_array, conf_dict, imageHeight, imageWidth, nof_pixel_values):
    image = picam2.capture_array()
    lock = image_array.get_lock()
    # if another access occurs
    if lock.acquire(block=False):
        # then in each new process create a new numpy array using:
        shared_image = np.frombuffer(image_array.get_obj(), dtype=np.uint8).reshape((imageHeight, imageWidth, nof_pixel_values))
        shared_image[:] = image
        lock.release()

def evaluateRequest(message_queue, picam2, conf_dict, streaming_enabled, has_finished):
    #Default case
    if message_queue.empty():
        #print("no message!?")
        return streaming_enabled, has_finished
    else:
        message = message_queue.get()
        print("message:", message)
        if message == "START":
            streaming_enabled = True
        elif message == "STOP":
            streaming_enabled = False
        elif isinstance(message, dict):
                query_dict = message
                message = query_dict.pop("message")
                if message == "LOAD":
                    updateCamSettings(picam2, conf_dict, query_dict)
        elif message == "FINISH":
            has_finished = True
            streaming_enabled = False
        return streaming_enabled, has_finished
    
def startImageAquisitionLoop(conf_dict, message_queue, image_array, imageHeight, imageWidth, nof_pixel_values):
    picam2, ret_dct = initCam(conf_dict)
    message_queue.put(ret_dct) #INIT COMPLETED

    if not ret_dct["successINIT"]:
        return    

    streaming_enabled = True
    has_finished = False
    ts = time.time()
    while not has_finished:
        if not streaming_enabled:
            time.sleep(0.1)
        else:
            if ts < time.time():
                ts = time.time() + conf_dict["image interval"]
                takePicture(picam2, image_array, conf_dict, imageHeight, imageWidth, nof_pixel_values)
            else:
                time.sleep(1e-3)

        #  Check for next request from client
        streaming_enabled, has_finished = evaluateRequest(message_queue, picam2, conf_dict, streaming_enabled, has_finished)

    closeQueue(message_queue, "CLOSE_MESSAGE_QUEUE")

def requestQueueClosure(queue, sentinel_message):
    queue.put(sentinel_message)
    queue.close()
    queue.join_thread()
    
def closeQueue(queue, sentinel_message):
    message = None
    ts = time.time()  
    while message != sentinel_message:
        if not queue.empty():
            message = queue.get()
        time.sleep(1e-3)
        if ts - time.time() > 10.0:
            break
    queue.close()
    queue.join_thread()

#for testing locally
def main():
    import multiprocessing as mp
    queue = mp.Queue()
    m, n, o = 480, 640, 4
    import ctypes
    image_array = mp.Array(ctypes.c_uint8, m*n*o)        
    startImageAquisitionLoop(queue, image_array, pathlib.Path.home()/'.local'/'share'/'DigiFlot')

if __name__=="__main__":
    main()
