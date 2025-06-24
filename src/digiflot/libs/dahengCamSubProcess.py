import logging
logger = logging.getLogger(__name__)

try:
    import gxipy as gx
except:
    gx = None
    logger.error("Gxipy module is not installed.")
import time
import numpy as np

def acq_mono(cam, conf_dict):
    """
        :brief      acquisition function of mono device
    """
    # send software trigger command
    cam.TriggerSoftware.send_command()

    # get raw image
    raw_image = cam.data_stream[0].get_image()
    if raw_image is None:
        print("Getting image failed.")
        return False, None
    
    # create numpy array with data from raw image
    numpy_image = raw_image.get_numpy_array()
    return numpy_image is not None, numpy_image

    """
    if numpy_image is not None:
        return False, None

    h = conf_dict["imgH"]  
    w = conf_dict["imgW"]

    margin_h = (540 - h) // 2
    margin_w = (720 - w) // 2

    # show acquired image
    img = Image.fromarray(numpy_image[margin_h:540-margin_h, margin_w:720-margin_w], 'L')
    #img.show()

    # print height, width, and frame ID of the acquisition image
    print("Frame ID: %d   Height: %d   Width: %d"
        % (raw_image.get_frame_id(), raw_image.get_height(), raw_image.get_width()))
    return True, img
    """

#only applicable if stream is set to off
def setWidth(cam, width):
    #round it to multiples of 8
    if width < 64:
        width = 64
    elif width > 720:
        width = 720
    else:
        width = round(width/8.0)*8
    print("Set width to", width)
    cam.Width.set(width)
    return cam.Width.get()

#only applicable if stream is set to off
def setHeight(cam, height):
    #round it to multiples of 8
    if height < 4:
        height = 4
    elif height > 540:
        height = 540
    else:
        height = round(height/2.0)*2
    print("Set heigth to", height)
    cam.Height.set(height)
    return cam.Height.get()

def initCam(conf_dict):
#Picture variables
    # create a device manager
    deviceManager = gx.DeviceManager()
    dev_num, dev_info_list = deviceManager.update_device_list()
    if dev_num == 0:
        print("Number of enumerated devices is 0")
        return
    # open the first device
    try:
        cam = deviceManager.open_device_by_index(1)
        #setWidth(cam, 720)
        #setHeight(cam, 540)
        adjustWidthAndHeightForAspectRatio(conf_dict)
        cam.ExposureTime.set(conf_dict["exposureTime"])
        cam.Gain.set(conf_dict["gain"])
        print("Maximum width: ", cam.Width.get_range())
        print("Maximum height: ", cam.Height.get_range())
        if dev_info_list[0].get("device_class") == gx.GxDeviceClassList.USB2:
            # set trigger mode
            cam.TriggerMode.set(gx.GxSwitchEntry.ON)
        else:
            # set trigger mode and trigger source
            cam.TriggerMode.set(gx.GxSwitchEntry.ON)
            cam.TriggerSource.set(gx.GxTriggerSourceEntry.SOFTWARE)
        # start data acquisition
        cam.stream_on()
        time.sleep(0.1)
        success, image = acq_mono(cam, conf_dict)
        if not success:
            raise Exception
    except:
        return None, None, {"successINIT" : False, "colorCAM" : "red", "camCalib" : False}
    else:
        return deviceManager, cam, {"successINIT" : True, "colorCAM" : "green", "camCalib" : True}


def adjustWidthAndHeightForAspectRatio(conf_dict):
    NimgH = conf_dict["imgH_query"]
    NimgW =conf_dict["imgW_query"]

    aspect_ratio_of_camera = 720/540
    aspect_ratio = NimgW/NimgH
    if aspect_ratio < aspect_ratio_of_camera:
        height = 540
        width = round(540 * aspect_ratio)
    else:
        width = 720
        height = round(720 / aspect_ratio)

    conf_dict["imgH"] = height  
    conf_dict["imgH_query"] = height
    conf_dict["imgW"] = width
    conf_dict["imgW_query"] = width

#limits for inputs are still missing
def updateCamSettings(cam, conf_dict, query_dict):
    #load the following parameters only in query parameters for subsequent case control
    gain = query_dict["gain_query"]
    exposure_time = query_dict["exposureTime_query"]
    NimgH = query_dict["imageHeight_query"]
    NimgW =query_dict["imageWidth_query"]
    intervalbild = query_dict["intervalbild_query"]
    #normally it takes really long to update these values. therefore we should only update the camera settings if values have changed
    #set software interval
    if conf_dict["intervalbild"] != intervalbild:
        conf_dict["intervalbild"] = intervalbild
    
    # disabled at the moment, but works
    ##check image width and height
    ##if NimgH != conf_dict["imgH"] or NimgW != conf_dict["imgW"]: 
    ##    adjustWidthAndHeightForAspectRatio(conf_dict)

    #check image width and height
    #if(NimgW != conf_dict["imgW"]): 
        #cam.stream_off()
        #width_from_cam = setWidth(cam, NimgW)
        #conf_dict["imgW"] = width_from_cam
        #conf_dict["imgW_query"] = width_from_cam
        #cam.stream_on()

    #if(NimgH != conf_dict["imgH"]): 
    #    cam.stream_off()
    #    height_from_cam = setHeight(cam, NimgH)
    #    conf_dict["imgH"] = height_from_cam  
    #    conf_dict["imgH_query"] = height_from_cam
    #    cam.stream_on()

    #if(NimgW != conf_dict["imgW"]): 
        #width is not writable => update image by cutting it
        #width_from_cam = setWidth(cam, NimgW)
        #conf_dict["imgW"] = width_from_cam
        #conf_dict["imgW_query"] = width_from_cam

    if(conf_dict["gain"] != gain):
        cam.Gain.set(gain)        
        conf_dict["gain"] = gain

    if( conf_dict["exposureTime"] != exposure_time ):
        cam.ExposureTime.set(exposure_time)
        conf_dict["exposureTime"] = conf_dict["exposureTime_query"]

def takePicture(cam, image_array, conf_dict, imageHeight, imageWidth, nof_pixel_values):
    image = acq_mono(cam, conf_dict) 
    lock = image_array.get_lock()
    # if another access occurs
    if lock.acquire(block=False):
        # then in each new process create a new numpy array using:
        shared_image = np.frombuffer(image_array.get_obj(), dtype=np.uint8).reshape((imageHeight, imageWidth, nof_pixel_values))
        shared_image[:] = image
        lock.release()

def evaluateRequest(message_queue, cam, conf_dict, streaming_enabled, has_finished):
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
                    updateCamSettings(cam, conf_dict, query_dict)
        elif message == "FINISH":
            has_finished = True
            streaming_enabled = False
            # stop acquisition
            cam.stream_off()
            # close device
            cam.close_device()
        return streaming_enabled, has_finished

def startImageAquisitionLoop(conf_dict, message_queue, image_array, imageHeight, imageWidth, nof_pixel_values):
    deviceManger, cam, ret_dct = initCam(conf_dict)
    message_queue.put(ret_dct)
    
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
                ts = time.time() + conf_dict["intervalbild"]
                takePicture(cam, image_array, conf_dict, imageHeight, imageWidth, nof_pixel_values)
            else:
                time.sleep(1e-3)
        
        #  Check for next request from client
        streaming_enabled, has_finished = evaluateRequest(message_queue, cam, conf_dict, streaming_enabled, has_finished)

    closeQueue(message_queue, "CLOSE_MESSAGE_QUEUE")

def closeQueue(queue, sentinel_message):
    message = None
    ts = time.time()
    #while not message_queue.empty():
    #    message_queue.get()    
    while message != sentinel_message:
        if not queue.empty():
            message = queue.get()
        time.sleep(1e-3)
        if ts - time.time() > 1.0:
            break
    queue.close()
    queue.join_thread()

#for testing locally
def main():
    import multiprocessing as mp
    queue = mp.Queue()
    queue2 = mp.Queue()
    startImageAquisitionLoop(queue, queue2)

if __name__=="__main__":
    main()
