import logging
logger = logging.getLogger(__name__)

import time
try:
    from PIL import Image
except:
    Image = None
    logger.error("Probably the PyQt installation is broken, or PIL is not installed.")
#import cv2
from datetime import datetime
import numpy as np

def storePicture(image, stagename, fmt, samplefolder, imgRaw, **kwargs):
        curr = datetime.now()
        imgname = str(curr.strftime("%Y%m%d-%H.%M.%S.%f")) + "_" + stagename
        
        def saveImg(SF, IN,image,doRaw):
            bildname = SF+ "/"+IN
            print(bildname)
            #image.save(bildname + '.' + fmt, fmt)
            if isinstance(image, np.ndarray):
                image_pil = Image.fromarray(image)
                image_pil.save(bildname + '.' + fmt, format=fmt)
                if doRaw:
                    image_pil.save(bildname + '.tiff', format="TIFF")
                #cv2.imwrite(bildname + '.' + fmt,image)
                #if (doRaw):
                #    np.save(bildname,image)
            else:
                image.save(bildname + '.' + fmt, fmt)
                if (doRaw):
                    image.save(bildname + '.tiff', 'tiff')

        saveImg(str(samplefolder), imgname, image, imgRaw)      

def evaluateRequest(message_queue, has_finished):
    #Default case
    if message_queue.empty():
        return has_finished
    else:
        message = message_queue.get()
        print("message:", message)
        if message == "START":
            pass
        elif message == "STOP":
            pass
        elif message == "LOAD":
            pass
        elif message == "FINISH":
            has_finished = True
        return has_finished

def startOfflineImageStorageLoop(image_dict_queue, image_array, imageHeight, imageWidth, nof_pixel_values, message_queue):
    has_finished = False
    while not has_finished:
        if not image_dict_queue.empty():
            dct = image_dict_queue.get()
            with image_array.get_lock():
                # then in each new process create a new numpy array using:
                image = np.frombuffer(image_array.get_obj(), dtype=np.uint8).reshape((imageHeight, imageWidth, nof_pixel_values)).copy()
            dct["image"] = image
            storePicture(**dct)

        time.sleep(1e-3)

        #  Check for next request from client
        has_finished = evaluateRequest(message_queue, has_finished)

    closeQueue(message_queue, "CLOSE_MESSAGE_QUEUE")
    closeQueue(image_dict_queue, "CLOSE_IMAGE_QUEUE")

def closeQueue(queue, sentinel_message):
    message = None
    ts = time.time()
    #while not message_queue.empty():
    #    message_queue.get()    
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
    queue2 = mp.Queue()
    startOfflineImageStorageLoop(queue, queue2)

if __name__=="__main__":
    main()
