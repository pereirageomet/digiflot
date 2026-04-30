"""Module docstring."""
import time
import logging
logger = logging.getLogger(__name__)

try:
    from libs.formalHardwareInterface import FormalHardwareInterface
except:
    try:
        from .formalHardwareInterface import FormalHardwareInterface
    except:
        #for debugging purposes, see main function
        from formalHardwareInterface import FormalHardwareInterface
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    logger.warning("Das Modul serial konnte nicht importiert werden.")

import pathlib

class Lidar(FormalHardwareInterface):

    def __init__(self):
        self._ser = None
        self._showLIDAR = False
        self._colorLIDAR = "red"
        self.pulplevel = "-"
        self._measuredValue = None

        self.measure_period = 0.5 # 0.5s/frame
        self.block_reading= False # blocks reading if buffer is in use
        self.measure_buffer_timer = 0.05 # How long to wait for sensor data to fill the buffer (TFmini+ can sent up to 1000hz, must be configured)

    @property
    def showLIDAR(self):
        return self._showLIDAR
    @property
    def colorLIDAR(self):
        return self._colorLIDAR



    
    @showLIDAR.setter
    def showLIDAR(self, value):
        self._showLIDAR = value
    @colorLIDAR.setter
    def colorLIDAR(self, value):
        self._colorLIDAR = value


    def getMeasuredValueFromLIDAR(self):
        if not self.connectedSuccessfully():
            return None

        self._ser.reset_input_buffer() # clear input buffer
        time.sleep(self.measure_buffer_timer) #let the buffer fill
        count = self._ser.in_waiting # count the number of received bytes in buffer
        if count > 8:
            recv = self._ser.read(9)   
            if recv[0] == 0x59 and recv[1] == 0x59:
                distance = recv[2] + recv[3] * 256
                strength = recv[4] + recv[5] * 256
                return distance

        logger.warning("Could not receive LiDAR data in time, consider increasing the measure buffer time.")

        return None




    def connectToLidar(self, atlasSensor):
        if not SERIAL_AVAILABLE:
            self.showLIDAR = False
            self.colorLIDAR = "red"
            self.pulplevel = "-"
            atlasSensor.times_list["LIDAR"] = 1.0
            return
        self.block_reading = True

        # Check for mounted Serial-To-USB-Adapter
        paths = list(pathlib.Path("/dev/").glob("ttyUSB[0-9]"))
        paths.append("/dev/serial0") # add raspi UART port 
        if not paths:
            logger.info("LiDAR not found.")
            return None, False

        for path in paths:
            try:
                # Open with a short timeout to prevent blocking during discovery
                _ser = serial.Serial(str(path), 115200, timeout=0.1)
                
                # Wait briefly for the hardware buffer to populate initially
                time.sleep(0.1) 
                
                # Read everything available to find the LATEST frame
                data = _ser.read_all()
                
                # Look for the last occurrence of the 0x59 0x59 header
                last_header_idx = data.rfind(b'\x59\x59')

                # Ensure header exists and there's enough data for a full 9-byte frame
                if last_header_idx != -1 and len(data) >= last_header_idx + 9:
                    raw = data[last_header_idx : last_header_idx + 9]
                    
                    distance = raw[2] + (raw[3] << 8)
                    logger.info(f"LIDAR connected on {path}: Dist.: {distance}")
                    
                    self._ser = _ser # stores the serial interface

                    if "LIDAR" not in atlasSensor.modules_list: # should use a set instead of a list
                        atlasSensor.modules_list.append("LIDAR")
                    
                    self.colorLIDAR = "green"
                    atlasSensor.times_list["LIDAR"] = self.measure_period
                    self.showLIDAR = True
                    self.pulplevel = 0
                    self.block_reading = True

                    return self._ser 
                else:
                    logger.info(f"No valid lidar frame found at {path}.")
                    _ser.close()

            except Exception as e:
                logger.info(f"Could not connect to {path}: {e}")




        

        # Fallback if havent yielded a valid sensor
        self.showLIDAR = False
        self.colorLIDAR = "red"
        self.pulplevel = "-"

    def connectedSuccessfully(self):
        return self.showLIDAR

    # Methods from formal interface

    def updateMeasuredValue(self):
        val = self.getMeasuredValueFromLIDAR()
        if val == 'none' or val is None:
            val = 0
        self._measuredValue = val
        return val

    def getMeasuredValue(self):
        return self._measuredValue

    def getDisplayValue(self):
        if self.pulplevel != "-":
            return round(self.pulplevel-self._measuredValue)
        else:
            return self._measuredValue

    def valueInTolerance(self):
        if self.pulplevel != "-":
            return (self._measuredValue > self.pulplevel * 0.9) and (self._measuredValue < self.pulplevel * 1.1)
        else:
            return True

    def queryMidAverage(self, MOD):
        return None

    def queryLowAverage(self, MOD):
        return None

    def queryHighAverage(self, MOD):
        return None

def modultest1():
    class AtlasSensorMock:
        def __init__(self):
            self.times_list = {}
            self.modules_list = []
    lidar = Lidar()
    lidar.connectToLidar(AtlasSensorMock())
    val = lidar.getMeasuredValueFromLIDAR()
    print(f"Value: {val}")

def modultest2():
    for baudrate in [115200, 230400, 460800, 500000, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]:
        with serial.Serial("/dev/ttyUSB0", baudrate, timeout=1) as ser:
            for II in range(0,10):            
                time.sleep(0.1)
                count = ser.in_waiting
                recv = ser.read(9)    
                print(f"baudrate: {baudrate}, count: {count}, recv: {recv}")

if __name__=="__main__":
    modultest1()
    modultest2()
