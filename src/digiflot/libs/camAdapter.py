import time
import multiprocessing as mp
import ctypes

try:
    from libs.raspiCamModel import RaspiCamModel
    from libs.tabViewCalibCamRaspi import TabViewCalibCamRaspi
    from libs.dahengCamModel import DahengCamModel
    from libs import raspiCamSubProcess    
    from libs import dahengCamSubProcess
    from libs.tabViewCalibCamDaheng import TabViewCalibCamDaheng
    from libs import configurationManager  
except:
    from .raspiCamModel import RaspiCamModel
    from .tabViewCalibCamRaspi import TabViewCalibCamRaspi
    from .dahengCamModel import DahengCamModel
    from . import raspiCamSubProcess    
    from . import dahengCamSubProcess
    from .tabViewCalibCamDaheng import TabViewCalibCamDaheng
    from . import configurationManager  
class CamAdapter:
    def __init__(self, taskModel, className="RaspiCamModel"):      
        self.className = className

        self._process_handle = None
        self._message_queue = None  
        self._image_array = None

        #factory pattern for image aquisition model and corresponding view class
        self._cam_handle = self.instantiateObject(taskModel)
        self._tabViewCalibCamRaspi = self.instantiateTabViewCalibCam()        

    def __del__(self):
        if self._process_handle is not None:
            self._process_handle.join(timeout=1)  # Wait for 1 second
            if self._process_handle.is_alive():
                print("Process is taking too long. Terminating...")
                self._process_handle.terminate()
                self._process_handle.join()

    def getCamInstance(self):
        return self._cam_handle

    def getCalibCamInstance(self):
        return self._tabViewCalibCamRaspi

    def instantiateTabViewCalibCam(self):
        if self.className == "RaspiCamModel":
            return TabViewCalibCamRaspi(self._cam_handle)
        else:
            return TabViewCalibCamDaheng(self._cam_handle)

    def instantiateObject(self, taskModel):
        self._message_queue = mp.Queue()          
        if self.className == "RaspiCamModel":
            imageHeight, imageWidth, nof_pixel_values = 480, 640, 4
            self._image_array = mp.Array(ctypes.c_uint8, imageHeight*imageWidth*nof_pixel_values)
            return RaspiCamModel(configurationManager.getConfig("RaspiCamModel"), taskModel, self._message_queue, self._image_array, imageHeight, imageWidth, nof_pixel_values)
        else:
            imageHeight, imageWidth, nof_pixel_values = 540, 720, 1
            self._image_array = mp.Array(ctypes.c_uint8, imageHeight*imageWidth*nof_pixel_values)            
            return DahengCamModel(configurationManager.getConfig("DahengCamModel"), taskModel, self._message_queue, self._image_array, imageHeight, imageWidth, nof_pixel_values)

    def startStream(self):
        if self.className == "RaspiCamModel":
            imageHeight, imageWidth, nof_pixel_values = self._cam_handle.getImageParameters()
            self._process_handle = mp.Process(target=raspiCamSubProcess.startImageAquisitionLoop, args=(configurationManager.getConfig("RaspiCamModel"), self._message_queue, self._image_array, imageHeight, imageWidth, nof_pixel_values))
        else:
            imageHeight, imageWidth, nof_pixel_values = self._cam_handle.getImageParameters()
            self._process_handle = mp.Process(target=dahengCamSubProcess.startImageAquisitionLoop, args=(configurationManager.getConfig("DahengCamModel"), self._message_queue, self._image_array, imageHeight, imageWidth, nof_pixel_values))
        self._process_handle.start()
        #wait until result dictionary is returned
        ret_dct = self._message_queue.get()
        # pass the result of the initialization on to the model class object ...
        self._cam_handle.set_colorCAM(ret_dct["colorCAM"])
        self._cam_handle.set_successINIT(ret_dct["successINIT"])
        self._cam_handle.set_camCalib(ret_dct["camCalib"])

    def continueStream(self):
        self._message_queue.put("START")
    
    def pauseStream(self):
        self._message_queue.put("STOP")

    def finishProcessesAndQueues(self):
        if self.isRunning():
            time.sleep(0.2)
            self._message_queue.put("FINISH") 
            time.sleep(0.2)
            CamAdapter.requestQueueClosure(self._message_queue, "CLOSE_MESSAGE_QUEUE")
            
            if self._process_handle is not None:
                self._process_handle.join(timeout=10)  # Wait for 10 second
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
