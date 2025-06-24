#Atlas sensors
try: 
    from libs import AtlasI2C
except:
    from . import AtlasI2C

class AtlasSensor():
    """
    Manages connections to Atlas Scientific Sensors.
    
    This class provides methods to connect to the Atlas Scientific Sensors, to read a out specific values, 
    and to query a calibration for a lower, upper, or intermediate calibration point.
    
    Attributes:
        times_list (list): contains timeouts of the sensors
        modules_list (list): contains name strings of the devices
        device_list (list): contains handles of the devices
        colorpH (string): encodes apparent color of the pH sensor on the setup tab
        colorT (string): encodes apparent color of the temperature sensor on the setup tab
        colorCond (string): encodes apparent color of the EC sensor on the setup tab
        colorOR (string): encodes apparent color of the ORP sensor on the setup tab
    """
    
    def __init__(self):
        self._times_list = []
        self._modules_list = []
        self._colorpH = "red"
        self._colorT = "red"
        self._colorCond = "red"
        self._colorOR = "red"
        self._device_list = []
        self.connect_devices()
        print(self.times_list)

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def times_list(self):
        return self._times_list

    @times_list.setter
    def times_list(self, value):
        self._times_list = value

    @property
    def modules_list(self):
        return self._modules_list

    @modules_list.setter
    def modules_list(self, value):
        self._modules_list = value

    @property
    def colorpH(self):
        return self._colorpH

    @colorpH.setter
    def colorpH(self, value):
        self._colorpH = value

    @property
    def colorT(self):
        return self._colorT

    @colorT.setter
    def colorT(self, value):
        self._colorT = value

    @property
    def colorCond(self):
        return self._colorCond

    @colorCond.setter
    def colorCond(self, value):
        self._colorCond = value

    @property
    def colorOR(self):
        return self._colorOR

    @colorOR.setter
    def colorOR(self, value):
        self._colorOR = value

    @property
    def device_list(self):
        return self._device_list

    @device_list.setter
    def device_list(self, value):
        self._device_list = value

    def connect_devices(self):
        """
        Scans for and connects to Atlas Scientific sensors measuring pH, EC, RTD, and ORP.

        This method attempts to discover each of these sensor types in the environment
        and establish a communication link for subsequent data retrieval.

        Returns:
            bool: True if at least one sensor was successfully connected, False otherwise.
        """

        #get the devices connected
        try:
            self.device_list = self.get_devices()
        except (FileNotFoundError, PermissionError):
            self.device_list = []

        self.times_list = {}
        try :
            self.modules_list =  [I.moduletype for I in self.device_list]
        except:
            self.modules_list = []
        #check for all devices if they are connected. If yes, show them in the initial window in green, otherwise in red.
        #create self.device variables and check the frequency in which requests can be made
        #Already send a write command to all devices available so that a measurement can be taken when the software starts

        if("pH" in self.modules_list):
            devpH = self.device_list[self.modules_list.index("pH")]
            intervalpH = devpH.long_timeout
            self.times_list["pH"] = intervalpH
            self.colorpH = "green"
            devpH.write("R")
        else:
            self.colorpH = "red"

        if("RTD" in self.modules_list):
            self.colorT = "green"
            devRTD = self.device_list[self.modules_list.index("RTD")]
            intervalRTD = devRTD.long_timeout
            self.times_list["RTD"] = intervalRTD
            devRTD.write("R")
        else:
            self.colorT = "red"

        if("EC" in self.modules_list):
            devEC = self.device_list[self.modules_list.index("EC")]
            intervalEC = devEC.long_timeout
            self.times_list["EC"] = intervalEC
            self.colorCond = "green"
            devEC.write("R")
        else:
            self.colorCond = "red"

        if("ORP" in self.modules_list):
            self.colorOR = "green"
            devORP = self.device_list[self.modules_list.index("ORP")]
            intervalORP = devORP.long_timeout
            self.times_list["ORP"] = intervalORP
            devORP.write("R")
        else:
            self.colorOR = "red"

    def connectedSuccessfully(self):
        """
        Checks if the given connection has been established successfully.

        This function tests whether the provided connection object self.device is fully operational.

        Returns:
            bool: True if the connection is successfully established to at least one of the Atlas Scientific sensors pH, EC, RTD, or ORP, False otherwise.
        """
        return len(self.device_list) > 0 and (self._colorpH == "green" or self._colorT == "green" or self._colorCond == "green" or self._colorOR == "green")

    def print_devices(self, MOD):
        """
        Prints device information to the console.

        This function iterates over a list of device objects and prints
        details provided by get_device_info.

        Returns:
            None: This function does not return a value; it simply prints
            device information to the console.
        """
        if not AtlasI2C.FCNTL_AVAILABLE:
            return
        
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        
        for i in self.device_list:
            if(i == dev):
                print("--> " + i.get_device_info())
            else:
                print(" - " + i.get_device_info())

    def get_devices(self):
        """
        Creates a full list of available device handles.

        This method uses the AtlasI2C class to list the available i2c devices, and then creates 
        instances of AtlasI2c class specificfor each moduletype, e.g. pH.

        Returns:
        device_list (object): A list of instances of AtlasI2C corresponding to the specific Atlas Scientific sensors.
        """
        if not AtlasI2C.FCNTL_AVAILABLE:
            return None, []
        
        device = AtlasI2C.AtlasI2C()
        device_address_list = device.list_i2c_devices()
        device_list = []

        for i in device_address_list:
            device.set_i2c_address(i)
            response = device.query("i")
            
            # check if the self.device is an EZO self.device
            checkEzo = response.split(",")
            if len(checkEzo) > 0:
                if checkEzo[0].endswith("?I"):
                    # yes - this is an EZO self.device
                    moduletype = checkEzo[1]
                    response = device.query("name,?").split(",")[1]
                    device_list.append(AtlasI2C.AtlasI2C(address = i, moduletype = moduletype, name = response))
        return device_list

    def readOutValue(self, MOD):
        """
        Reads out measurement values from sensor.
        
        Takes string MOD which contains the target measurement value and outputs the measured value.

        Returns:
            float: measured value
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        measurement = dev.read()
        dev.write("R")
        measurement = measurement.split(":")
        measurement = measurement[1]
        measurement = measurement.split("\x00")
        return float(measurement[0])

    def queryLowAverage(self, MOD, target):
        """
        Query for setting the lower calibration point of the calibration curve for the device MOD

        Args:
            MOD (string): encodes the device, i.e. pH, EC, RTD, ORP
            target (float): Setpoint value

        Returns:
            string: returned string from the query
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,low,{target}")
        return val

    def queryMidAverage(self, MOD, target):
        """
        Query for setting the middle calibration point of the calibration curve for the device MOD

        Args:
            MOD (string): encodes the device, i.e. pH, EC, RTD, ORP
            target (float): Setpoint value

        Returns:
            string: returned string from the query
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,mid,{target}")
        return val

    def queryHighAverage(self, MOD, target):
        """
        Query for setting the upper calibration point of the calibration curve for the device MOD

        Args:
            MOD (string): encodes the device, i.e. pH, EC, RTD, ORP
            target (float): Setpoint value

        Returns:
            string: returned string from the query
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,high,{target}")
        return val
    
    def queryClear(self, MOD):
        """
        Query for setting the upper calibration point of the calibration curve for the device MOD

        Args:
            MOD (string): encodes the device, i.e. pH, EC, RTD, ORP
            target (float): Setpoint value

        Returns:
            string: returned string from the query
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Clear")
        return val
    
    def queryFactory(self, MOD):
        """
        Query for setting the upper calibration point of the calibration curve for the device MOD

        Args:
            MOD (string): encodes the device, i.e. pH, EC, RTD, ORP
            target (float): Setpoint value

        Returns:
            string: returned string from the query
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Factory")
        return val
        
#to be called like "python3 -m libs.atlasSensor"
if __name__ == "__main__":
    atlasSensor = AtlasSensor()
    print(atlasSensor.modules_list)