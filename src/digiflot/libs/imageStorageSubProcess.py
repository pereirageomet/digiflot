"""Module providing offline image storage subprocess functionality.

This module handles saving images to disk in a separate process, supporting
both compressed and raw formats. It manages image queues and file storage
with timestamps and stage names.
"""
import logging
logger = logging.getLogger(__name__)

import tifffile

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
    """Store an image to disk with timestamp and stage name.

    :param image: Image data (PIL Image or numpy array)
    :param stagename: Name of the current stage for filename
    :param fmt: Image format (e.g., 'jpg', 'png')
    :param samplefolder: Folder path for saving images
    :param imgRaw: Whether to also save raw TIFF version
    :param kwargs: Additional keyword arguments
    """
    curr = datetime.now()
    imgname = str(curr.strftime("%Y%m%d-%H.%M.%S.%f")) + "_" + stagename
    
    def saveImg(SF, IN, image, doRaw):
        """Save image to file, optionally with raw TIFF version.

        :param SF: Sample folder path
        :param IN: Image name (without extension)
        :param image: Image data to save
        :param doRaw: Whether to save raw TIFF version
        """
        bildname = SF + "/" + IN
        # print(bildname)
        if isinstance(image, np.ndarray):
            if fmt == "tiff":
                if doRaw: # sem compressao
                    tifffile.imwrite(f"{bildname}.tiff", image, compression=None)
                else: #com compressao
                    tifffile.imwrite(f"{bildname}.tiff", image, compression="zstd") #! zstd REQUER O PACOTE IMAGECONDECAS: pip install imagecodecs
                    # tifffile.imwrite(f"{bildname}.tiff", image, compression="lzw") #! LZW - codec mais antigo

            else:
                image_pil = Image.fromarray(image)
                image_pil.save(bildname + '.' + fmt, format=fmt)
        else:
            image.save(bildname + '.' + fmt, fmt)
            if doRaw:
                image.save(bildname + '.tiff', 'tiff')

    saveImg(str(samplefolder), imgname, image, imgRaw)      

def evaluateRequest(message_queue, has_finished):
    """Process control messages from the queue.

    :param message_queue: Queue for receiving control messages
    :param has_finished: Flag indicating if the process should finish
    :return: Updated has_finished flag
    """
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
                image = np.frombuffer(image_array.get_obj(), dtype=np.uint8).reshape((imageHeight, imageWidth, nof_pixel_values)).copy()
            dct["image"] = image
            storePicture(**dct)

        time.sleep(5e-3)
        has_finished = evaluateRequest(message_queue, has_finished)

def closeQueue(queue, sentinel_message):
    """Close a multiprocessing queue and join its thread.

    :param queue: Queue to close
    :param sentinel_message: Message sentinel to stop draining the queue
    """
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

def main():
    """Entry point for testing the subprocess module."""
    import multiprocessing as mp
    queue = mp.Queue()
    queue2 = mp.Queue()
    startOfflineImageStorageLoop(queue, queue2, 480, 640, 4, queue2)
