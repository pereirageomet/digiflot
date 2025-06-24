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

    ## LiDar 
    # RX = 15
    # pi = pigpio.pi()
    # pi.set_mode(RX, pigpio.INPUT)
    # pi.bb_serial_read_open(RX, 115200)
    # for I in range(0,10):
    #     time.sleep(0.1)
    #     (count, recv) = pi.bb_serial_read(RX)
    # if recv != '':
    #     modules_list = modules_list + ("LIDAR",)
    #     _colorLIDAR = "green"
    #     intervalLIDAR = 1
    #     _showLIDAR = True
    # else:
    #     _showLIDAR = False
    #     _colorLIDAR = "red"

    def __init__(self):
        self._ser = None
        self._showLIDAR = False
        self._colorLIDAR = "red"
        self._pulplevel = "-"
        self._measuredValue = None

    @property
    def showLIDAR(self):
        return self._showLIDAR

    @showLIDAR.setter
    def showLIDAR(self, value):
        self._showLIDAR = value

    @property
    def colorLIDAR(self):
        return self._colorLIDAR

    @colorLIDAR.setter
    def colorLIDAR(self, value):
        self._colorLIDAR = value

    @property
    def pulplevel(self):
        return self._pulplevel

    @pulplevel.setter
    def pulplevel(self, value):
        self._pulplevel = value

    def getMeasuredValueFromLIDAR(self):
        if not self.connectedSuccessfully():
            return "none"
                
        #nächste Zeile notwendig notwendig?
        #self._ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
        #time.sleep(0.1)
        count = self._ser.in_waiting
        if count > 8:
            recv = self._ser.read(9)   
            self._ser.reset_input_buffer() 
            if recv[0] == 0x59 and recv[1] == 0x59:
                distance = recv[2] + recv[3] * 256
                strength = recv[4] + recv[5] * 256
                self._ser.reset_input_buffer()
                return(distance)
        else:
            return("none")
        
    def connectToLidar(self, atlasSensor):
        if not SERIAL_AVAILABLE:
            self.showLIDAR = False
            self.colorLIDAR = "red"
            self.pulplevel="-"
            atlasSensor.times_list["LIDAR"] = 1.0
            return

        paths = list(pathlib.Path("/dev/").glob("ttyUSB[0-9]"))
        if len(paths) == 0:
            logger.info("No Serial-To-USB-Adapter mounted.")
            return None, False

        recv = None
        for path in paths:
            try:
                _ser = serial.Serial(str(path), 115200, timeout=1)
                for _ in range(0,10):
                    time.sleep(0.1)
                    count = _ser.in_waiting
                    recv = _ser.read(9)
                if count > 8 and recv[0] == 0x59 and recv[1] == 0x59:
                    self._ser = serial.Serial(str(path), 115200, timeout=1)
                    #one lidar is enough
                    break
                else:
                    logger.info(f"No lidar device at {str(path)}.")
            except:
                logger.info(f"No device reachable via serial module at {str(path)}.")

        if self._ser is not None and recv is not None and recv != b'':
            atlasSensor.modules_list = atlasSensor.modules_list + ["LIDAR"]
            self.colorLIDAR = "green"
            intervalLIDAR = .5
            atlasSensor.times_list["LIDAR"] = intervalLIDAR
            self.showLIDAR = True
            self.pulplevel=0
        else:
            self.showLIDAR = False
            self.colorLIDAR = "red"
            self.pulplevel="-"

    def connectedSuccessfully(self):
        return self.showLIDAR

    # Methods from formal interface

    def updateMeasuredValue(self):
        val = self.getMeasuredValueFromLIDAR()
        if val == 'none':
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
