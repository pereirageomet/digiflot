#Atlas sensors
try: 
    from libs import AtlasI2C
except:
    from . import AtlasI2C

class AtlasSensor():
    """
    Manages connections to Atlas Scientific sensors for pH, EC, RTD, and ORP measurements.

    This class provides methods to connect to the Atlas Scientific sensors, read specific measurement values,
    and perform calibration queries for lower, upper, or intermediate calibration points.

    Attributes:
        _times_list (dict): Dictionary mapping sensor types to their timeout intervals
        _modules_list (list): List of detected sensor module types (e.g., "pH", "EC", "RTD", "ORP")
        _device_list (list): List of AtlasI2C device handle instances
        _colorpH (str): Color indicator for pH sensor connection status ("green" if connected, "red" otherwise)
        _colorT (str): Color indicator for temperature (RTD) sensor connection status
        _colorCond (str): Color indicator for EC (conductivity) sensor connection status
        _colorOR (str): Color indicator for ORP (oxidation-reduction potential) sensor connection status
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
        """Get the single device handle (deprecated, use device_list instead)."""
        return self._device

    @device.setter
    def device(self, value):
        """Set the single device handle (deprecated, use device_list instead)."""
        self._device = value

    @property
    def times_list(self):
        """Get the dictionary of sensor timeout intervals."""
        return self._times_list

    @times_list.setter
    def times_list(self, value):
        """Set the dictionary of sensor timeout intervals."""
        self._times_list = value

    @property
    def modules_list(self):
        """Get the list of detected sensor module types."""
        return self._modules_list

    @modules_list.setter
    def modules_list(self, value):
        """Set the list of detected sensor module types."""
        self._modules_list = value

    @property
    def colorpH(self):
        """Get the connection status indicator for pH sensor."""
        return self._colorpH

    @colorpH.setter
    def colorpH(self, value):
        """Set the connection status indicator for pH sensor."""
        self._colorpH = value

    @property
    def colorT(self):
        """Get the connection status indicator for temperature sensor."""
        return self._colorT

    @colorT.setter
    def colorT(self, value):
        """Set the connection status indicator for temperature sensor."""
        self._colorT = value

    @property
    def colorCond(self):
        """Get the connection status indicator for EC sensor."""
        return self._colorCond

    @colorCond.setter
    def colorCond(self, value):
        """Set the connection status indicator for EC sensor."""
        self._colorCond = value

    @property
    def colorOR(self):
        """Get the connection status indicator for ORP sensor."""
        return self._colorOR

    @colorOR.setter
    def colorOR(self, value):
        """Set the connection status indicator for ORP sensor."""
        self._colorOR = value

    @property
    def device_list(self):
        """Get the list of AtlasI2C device handle instances."""
        return self._device_list

    @device_list.setter
    def device_list(self, value):
        """Set the list of AtlasI2C device handle instances."""
        self._device_list = value

    def connect_devices(self):
        """
        Scan for and connect to Atlas Scientific sensors measuring pH, EC, RTD, and ORP.

        This method attempts to discover each of these sensor types in the environment
        and establish a communication link for subsequent data retrieval. It also initializes
        measurement timeouts and visual status indicators for each connected sensor type.

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
        Check if at least one Atlas Scientific sensor is successfully connected.

        This method verifies that the device list is populated and at least one sensor type
        (pH, EC, RTD, or ORP) has been detected and initialized successfully.

        Returns:
            bool: True if at least one sensor is connected, False otherwise.
        """
        return len(self.device_list) > 0 and (self._colorpH == "green" or self._colorT == "green" or self._colorCond == "green" or self._colorOR == "green")

    def print_devices(self, MOD):
        """
        Print device information to the console for a specific sensor type.

        This function iterates over the device list and prints details for the specified
        sensor type, highlighting it with an arrow prefix.

        Args:
            MOD (str): The sensor module type to print (e.g., "pH", "EC", "RTD", "ORP").

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
        Create a full list of available device handles.

        This method uses the AtlasI2C class to list available I2C devices, then creates
        instances of AtlasI2C specifically for each detected module type (e.g., pH, EC, RTD, ORP).

        Returns:
            list: A list of AtlasI2C instances corresponding to the detected Atlas Scientific sensors.
                  Returns (None, []) if I2C functionality is not available.
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
        Read the measurement value from a specific sensor type.

        Takes a string MOD which specifies the target measurement value and returns the measured value.

        Args:
            MOD (str): The sensor module type to read from (e.g., "pH", "EC", "RTD", "ORP").

        Returns:
            float: The measured value from the sensor.
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
        Query for setting the lower calibration point of the calibration curve.

        Args:
            MOD (str): The sensor module type (e.g., "pH", "EC", "RTD", "ORP").
            target (float): The calibration setpoint value.

        Returns:
            str: The response string from the sensor query.
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,low,{target}")
        return val

    def queryMidAverage(self, MOD, target):
        """
        Query for setting the middle calibration point of the calibration curve.

        Args:
            MOD (str): The sensor module type (e.g., "pH", "EC", "RTD", "ORP").
            target (float): The calibration setpoint value.

        Returns:
            str: The response string from the sensor query.
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,mid,{target}")
        return val

    def queryHighAverage(self, MOD, target):
        """
        Query for setting the upper calibration point of the calibration curve.

        Args:
            MOD (str): The sensor module type (e.g., "pH", "EC", "RTD", "ORP").
            target (float): The calibration setpoint value.

        Returns:
            str: The response string from the sensor query.
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Cal,high,{target}")
        return val
    
    def queryClear(self, MOD):
        """
        Query to clear the calibration for a specific sensor type.

        Args:
            MOD (str): The sensor module type (e.g., "pH", "EC", "RTD", "ORP").

        Returns:
            str: The response string from the sensor query.
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Clear")
        return val
    
    def queryFactory(self, MOD):
        """
        Query to reset the sensor to factory calibration settings.

        Args:
            MOD (str): The sensor module type (e.g., "pH", "EC", "RTD", "ORP").

        Returns:
            str: The response string from the sensor query.
        """
        ind = self.modules_list.index(MOD)
        dev = self.device_list[ind]
        val = dev.query(f"Factory")
        return val
        
#to be called like "python3 -m libs.atlasSensor"
if __name__ == "__main__":
    atlasSensor = AtlasSensor()
    print(atlasSensor.modules_list)