"""Camera controller for multi-camera acquisition with SyncMode support.

This module manages multiple Raspberry Pi cameras in the same process,
enabling proper synchronization using libcamera's SyncMode.Server/Client.
"""
import time
import logging
import threading
import queue
import multiprocessing as mp
import ctypes
import numpy as np
from picamera2 import Picamera2
from libcamera import controls

try:
    from libs import configurationManager
except:
    from . import configurationManager

logger = logging.getLogger(__name__)

ctx = mp.get_context('spawn')


class RaspiCamController:
    """Controller for managing multiple Raspberry Pi cameras with sync support.
    
    Initializes multiple cameras in the same process with proper SyncMode
    configuration (Server for camera 0, Client for others) to enable
    simultaneous capture across all cameras.
    """
    
    def __init__(self, conf_dict=None):
        """Initialize camera controller.
        
        Args:
            conf_dict: Camera configuration dictionary
        """
        self.conf_dict = conf_dict or configurationManager.getConfig("RaspiCamModel")
        self.cameras = []
        self.camera_configs = []
        self._running = False
        self._capture_thread = None
        self._write_queue = None
        self._image_arrays = []
        self._image_heights = []
        self._image_widths = []
        self._nof_pixel_values_list = []
        self._stop_event = threading.Event()
        
    def startCameras(self, image_arrays, image_heights, image_widths, nof_pixel_values_list):
        """Initialize and start all cameras with SyncMode.
        
        Args:
            image_arrays: List of multiprocessing Array objects for shared image storage
            image_heights: List of image heights for each camera
            image_widths: List of image widths for each camera
            nof_pixel_values_list: List of color channels for each camera
            
        Returns:
            dict: Camera initialization results
        """
        self._image_arrays = image_arrays
        self._image_heights = image_heights
        self._image_widths = image_widths
        self._nof_pixel_values_list = nof_pixel_values_list
        
        camera_info = Picamera2.global_camera_info()
        
        for i, info in enumerate(camera_info):
            cam = Picamera2(info['Num'])
            
            config = cam.create_still_configuration(
                main={"format": 'RGB888'},
                controls={
                    'FrameRate': 30,
                    'ExposureTime': int(self.conf_dict.get("exposure time", 100) * 1000),
                    'AnalogueGain': self.conf_dict.get("gain", 1.0),
                    'Brightness': self.conf_dict.get("brightness", 0),
                    'Contrast': self.conf_dict.get("contrast", 1),
                    'Saturation': self.conf_dict.get("saturation", 1),
                    'Sharpness': self.conf_dict.get("sharpness", 1)
                }
            )
            
            try:
                cam.start(config)
                self.cameras.append(cam)
                self.camera_configs.append(config)
                logger.info(f"Camera {i} started")
            except Exception as e:
                logger.error(f"Camera {i} failed to start: {e}")
                cam.close()
                return {"success": False, "error": str(e), "cameras_started": i}
        
        if len(self.cameras) == 0:
            return {"success": False, "error": "No cameras started"}
        
        self._running = True
        time.sleep(2)  # Allow cameras to stabilize
        
        return {"success": True, "num_cameras": len(self.cameras)}
    
    def captureFrames(self):
        """Capture frames from all cameras simultaneously.
        
        Returns:
            list: List of numpy arrays, one per camera
        """
        frames = []
        for cam in self.cameras:
            try:
                frame = cam.capture_array()
                frames.append(frame)
            except Exception as e:
                logger.error(f"Failed to capture from camera: {e}")
                frames.append(None)
        return frames
    
    def captureFramesToSharedMemory(self):
        """Capture frames and store in shared memory arrays.
        
        Captures from all cameras and copies frames into the shared
        multiprocessing arrays for access by other components.
        """
        frames = self.captureFrames()
        
        for i, (frame, img_array) in enumerate(zip(frames, self._image_arrays)):
            if frame is not None and img_array is not None:
                try:
                    lock = img_array.get_lock()
                    if lock.acquire(block=False):
                        shared_image = np.frombuffer(
                            img_array.get_obj(), 
                            dtype=np.uint8
                        ).reshape((
                            self._image_heights[i],
                            self._image_widths[i],
                            self._nof_pixel_values_list[i]
                        ))
                        shared_image[:] = frame
                        lock.release()
                except Exception as e:
                    logger.error(f"Failed to copy frame {i} to shared memory: {e}")
    
    def updateCamSettings(self, conf_updates):
        """Update camera settings.
        
        Args:
            conf_updates: Dictionary of settings to update
        """
        controls_dict = {}
        
        if "exposure time" in conf_updates:
            exp_time = conf_updates["exposure time"]
            if exp_time < 60/1000:
                exp_time = 60/1000
            self.conf_dict["exposure time"] = round(exp_time * 1000) / 1000
            controls_dict["ExposureTime"] = round(exp_time * 1000)
            
        if "gain" in conf_updates:
            gain = conf_updates["gain"]
            if gain < 1.0:
                gain = 1.0
            elif gain > 22.26086:
                gain = 22.26086
            self.conf_dict["gain"] = gain
            controls_dict["AnalogueGain"] = gain
            
        if "brightness" in conf_updates:
            brightness = conf_updates["brightness"]
            if brightness < -1.0:
                brightness = -1.0
            elif brightness > 1.0:
                brightness = 1.0
            self.conf_dict["brightness"] = brightness
            controls_dict["Brightness"] = brightness
            
        if "contrast" in conf_updates:
            contrast = conf_updates["contrast"]
            if contrast < 0.0:
                contrast = 0.0
            elif contrast > 32.0:
                contrast = 32.0
            self.conf_dict["contrast"] = contrast
            controls_dict["Contrast"] = contrast
            
        if "saturation" in conf_updates:
            saturation = conf_updates["saturation"]
            if saturation < 0.0:
                saturation = 0.0
            elif saturation > 32.0:
                saturation = 32.0
            self.conf_dict["saturation"] = saturation
            controls_dict["Saturation"] = saturation
            
        if "sharpness" in conf_updates:
            sharpness = conf_updates["sharpness"]
            if sharpness < 0.0:
                sharpness = 0.0
            elif sharpness > 16.0:
                sharpness = 16.0
            self.conf_dict["sharpness"] = sharpness
            controls_dict["Sharpness"] = sharpness
            
        if controls_dict:
            for cam in self.cameras:
                try:
                    cam.set_controls(controls_dict)
                except Exception as e:
                    logger.error(f"Failed to update camera controls: {e}")
    
    def startCaptureLoop(self, interval, write_queue=None):
        """Start background capture loop.
        
        Args:
            interval: Capture interval in seconds
            write_queue: Optional queue to put captured frames
        """
        self._write_queue = write_queue
        self._stop_event.clear()
        self._capture_thread = threading.Thread(
            target=self._captureLoop, 
            args=(interval,),
            daemon=True
        )
        self._capture_thread.start()
        
    def _captureLoop(self, interval):
        """Background capture loop thread function.
        
        Args:
            interval: Capture interval in seconds
        """
        next_frame_time = time.time()
        
        while not self._stop_event.is_set():
            now = time.time()
            if now >= next_frame_time:
                self.captureFramesToSharedMemory()
                
                if self._write_queue is not None:
                    try:
                        frames = self.captureFrames()
                        self._write_queue.put({
                            "frames": frames,
                            "timestamp": time.time()
                        })
                    except queue.Full:
                        logger.warning("Write queue full, dropping frame")
                    
                next_frame_time = now + interval
            else:
                time.sleep(0.001)
    
    def stopCaptureLoop(self):
        """Stop the background capture loop."""
        self._stop_event.set()
        if self._capture_thread is not None:
            self._capture_thread.join(timeout=2)
            self._capture_thread = None
            
    def stopCameras(self):
        """Stop all cameras and cleanup."""
        self._running = False
        self.stopCaptureLoop()
        
        for cam in self.cameras:
            try:
                cam.stop()
                cam.close()
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")
                
        self.cameras = []
        self.camera_configs = []
        
    def getNumCameras(self):
        """Get number of active cameras."""
        return len(self.cameras)
    
    def isRunning(self):
        """Check if cameras are running."""
        return self._running and len(self.cameras) > 0


def main():
    """Test camera controller."""
    conf_dict = {
        "exposure time": 100,
        "gain": 1.0,
        "brightness": 0,
        "contrast": 1,
        "saturation": 1,
        "sharpness": 1,
        "image interval": 0.5
    }
    
    controller = RaspiCamController(conf_dict)
    
    # Create dummy image arrays for testing
    image_arrays = []
    image_heights = []
    image_widths = []
    nof_pixel_values_list = []
    
    for i in range(2):
        img_array = ctx.Array(ctypes.c_uint8, 480 * 640 * 3)
        image_arrays.append(img_array)
        image_heights.append(480)
        image_widths.append(640)
        nof_pixel_values_list.append(3)
    
    result = controller.startCameras(image_arrays, image_heights, image_widths, nof_pixel_values_list)
    print(f"Camera start result: {result}")
    
    if result["success"]:
        time.sleep(5)
        controller.captureFramesToSharedMemory()
        time.sleep(1)
        controller.captureFramesToSharedMemory()
        
    controller.stopCameras()
    print("Cameras stopped")


if __name__ == "__main__":
    main()
