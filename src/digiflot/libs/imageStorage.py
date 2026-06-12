"""Module for offline image storage using threading."""
import time
import logging
import threading
import queue
import multiprocessing as mp
import ctypes
import numpy as np


try:
    from libs import imageStorageSubProcess
    from libs.devTools import *

except:
    from . import imageStorageSubProcess

logger = logging.getLogger(__name__)
ctx = mp.get_context('spawn')

class ImageStorage:
    def __init__(self, cam_handle):      
        self._cam_handle = cam_handle
        self._thread = None
        self._stop_event = None
        self._image_dict_queue = None
        self._running = False

    def cleanup(self):
        """Explicit cleanup method - call before destruction."""
        self.finishProcessesAndQueues()

    def __del__(self):
        self.cleanup()

    def startOfflineStorageService(self):
        if self.isRunning():
            logger.warning("Offline storage service already running; start request ignored.")
            return
        self._image_dict_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._storageLoop,
            daemon=True
        )
        self._running = True
        self._thread.start()

    def _storageLoop(self):
        """Background thread for saving images to disk."""
        while not self._stop_event.is_set():
            try:
                dct = self._image_dict_queue.get(timeout=0.1)
                self._saveImage(dct)
                self._image_dict_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in storage loop: {e}")

    def _saveImage(self, dct):
        """Save a single image to disk.

        Args:
            dct: Dictionary with image metadata and settings
        """
        try:
            with self._cam_handle.image_array.get_lock():
                image = np.frombuffer(
                    self._cam_handle.image_array.get_obj(),
                    dtype=np.uint8
                ).reshape(self._cam_handle.getImageParameters()).copy()

            dct = dict(dct)
            dct["image"] = image

            from pathlib import Path

            cam_name = dct.get("camera_name", "unknown")
            base_folder = Path(dct["samplefolder"]).expanduser()
            sub_folder = base_folder / "imgs" / cam_name
            sub_folder.mkdir(parents=True, exist_ok=True)

            dct["samplefolder"] = str(sub_folder)

            imageStorageSubProcess.storePicture(**dct)

        except Exception as e:
            logger.error(f"Failed to save image: {e}")

    def stopOfflineStorageService(self):
        """Stop the storage thread."""
        if self.isRunning():
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=2)
            self._running = False


    def saveImageOffline(self):
        """Queue an image for saving."""
       
        if self.isRunning():
            dct = self._cam_handle.getImageDictForSavingOffline()
            try:
                self._image_dict_queue.put(dct, timeout=1)
            except queue.Full:
                logger.warning("Image queue full, dropping image")

    def finishProcessesAndQueues(self):
        """Stop the storage thread and ensure cleanup."""
        if self.isRunning():
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=5)
            # Clear queue to avoid leftover items
            try:
                while not self._image_dict_queue.empty():
                    self._image_dict_queue.get_nowait()
            except Exception:
                pass
            self._running = False
            self._thread = None
            self._stop_event = None
            self._image_dict_queue = None
        
    def isRunning(self):
        return self._running and self._thread is not None and self._thread.is_alive()

