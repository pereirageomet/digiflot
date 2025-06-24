import time
import multiprocessing as mp

try:
    from libs import imageStorageSubProcess
except:
    from . import imageStorageSubProcess

class ImageStorage:
    def __init__(self, cam_handle):      
        self._cam_handle = cam_handle
        self._process_handle = None

        self.image_dict_queue = mp.Queue()      
        self.message_queue = mp.Queue()         

    def __del__(self):
        if self._process_handle is not None:
            self._process_handle.join(timeout=1)  # Wait for 1 second
            if self._process_handle.is_alive():
                print("Process 2 is taking too long. Terminating...")
                self._process_handle.terminate()
                self._process_handle.join()    

    def startOfflineStorageService(self):
        imageHeight, imageWidth, nof_pixel_values = self._cam_handle.getImageParameters()
        self._process_handle = mp.Process(target=imageStorageSubProcess.startOfflineImageStorageLoop, args=(self.image_dict_queue, self._cam_handle.image_array, imageHeight, imageWidth, nof_pixel_values, self.message_queue))
        self._process_handle.start()

    def stopOfflineStorageService(self):
        if self.isRunning():
            self._process_handle.terminate()
            self._process_handle.join()    

    def saveImageOffline(self):
        if self.isRunning():
            dct = self._cam_handle.getImageDictForSavingOffline()
            self.image_dict_queue.put(dct)

    def finishProcessesAndQueues(self):
        if self.isRunning():        
            time.sleep(0.2)        
            self.message_queue.put("FINISH")
            time.sleep(0.2)
            ImageStorage.requestQueueClosure(self.message_queue, "CLOSE_MESSAGE_QUEUE")
            time.sleep(0.2)
            ImageStorage.requestQueueClosure(self.image_dict_queue, "CLOSE_IMAGE_QUEUE")

            self._process_handle.join(timeout=10)  # Wait for 10 seconds
            if self._process_handle.is_alive():
                print("Process is taking too long. Terminating...")
                self._process_handle.terminate()
                self._process_handle.join()   
            self._process_handle = None

    @staticmethod
    def requestQueueClosure(queue, sentinel_message):
        queue.put(sentinel_message)
        queue.close()
        queue.join_thread()
        
    def isRunning(self):
        return self._process_handle is not None and self._process_handle.is_alive()
