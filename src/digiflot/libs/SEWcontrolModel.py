import logging
logger = logging.getLogger(__name__)

try:
    import minimalmodbus
except:
    minimalmodbus = None
    MINIMALMODBUS_INSTALLED = False
    logger.info("Minimalmodbus library for SEW control is not installed.")
else:
    MINIMALMODBUS_INSTALLED = True    

import pathlib

class SEWcontrolModel:
    """
    Manages communication and control for SEW brand drives.

    This class provides methods to connect to, get data from and set rotor speed to a SEW frequency converter. 

    Attributes:
        measuredRotorSpeed (float): Rotor speed measured by the SEW device.
        measuredSetRotorSpeed (float): Target rotor speed read from the SEW's frequency converter register.
        instrument (object): API handle to communicate with the SEW frequency converter, e.g. write to and read from its registers.
        successINIT (bool): Flag which indicates whether or not the connection to the SEW fequency converter was successfull.
    """
    def __init__(self):
        self.measuredRotorSpeed = -1.0
        self.measuredSetRotorSpeed = -1.0
        self.instrument, self.successINIT = self.connect()

    def __del__(self):
        self.setRotorSpeed(0.0)

    def connect(self):
        """
        Establishes a connection to the SEW device.

        This method attempts to open or activate the underlying communication channel.
        If the connection is successful, the internal `successINIT` attribute is set
        to True.

        Returns:
            object: API handle if the connection is established successfully, None otherwise.
            bool: True if the connection is established successfully, False otherwise.
        """
        if not MINIMALMODBUS_INSTALLED:
            return None, False

        paths = list(pathlib.Path("/dev/").glob("ttyUSB[0-9]"))
        if len(paths) == 0:
            logger.info("No Serial-To-USB-Adapter mounted.")
            return None, False

        #PORT='/dev/cu.usbserial-AC00XX39'        
        drehzahl_soll_REGISTER = 2
        drehzahl_ist_REGISTER = 7

        instrument = None
        for path in paths:
            try:
                # Connect to the local instrument, when no settings provided
                instrument = minimalmodbus.instrument(str(path))
            except:
                instrument = None
                logger.info(f"No SEW device device at {str(path)}.")
            else:
                #### does this work??? ####
                print(instrument.id)
                ret_id = instrument.id
                if ret_id is not None:
                    logger.info(f"Found SEW device with id {ret_id} at {str(path)}.")
                    break
                else:
                    instrument = None
                    logger.info(f"No SEW device device at {str(path)}.")

        #Make the settings explicit
        instrument.serial.baudrate = 19200        # Baud
        instrument.serial.bytesize = 8
        instrument.serial.parity   = minimalmodbus.serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout  = 1          # seconds

        ## Good practice
        #instrument.close_port_after_each_call = True
        #instrument.clear_buffers_before_each_transaction = True

        # Read temperatureas a float
        # if you need to read a 16 bit register use instrument.read_register()
        drehzahl_soll = instrument.read_float(drehzahl_soll_REGISTER)

        # Read the humidity
        drehzahl_ist = instrument.read_float(drehzahl_ist_REGISTER)

        #Pront the values
        print('The set rotation speed is: %.1f deg C\r' % drehzahl_soll)
        print('The actual rotation speed is: %.1f percent\r' % drehzahl_ist)

        successINIT = (instrument is not None)
        return instrument, successINIT

    def connectedSuccessfully(self):
        """
        Checks whether the last connection attempt to the SEW device was successful.

        This method returns True if the connection was established and is still
        considered valid. If no connection attempt has been made or if the connection
        failed, it returns False.

        Returns:
            bool: True if connected successfully, otherwise False.
        """
        return self.successINIT

    def setRotorSpeed(self, value):
        """
        Sets the rotor speed on the SEW device.

        This method sends a command to the SEW motor controller to adjust the rotor
        speed to the specified value. The valid speed range may depend on the device's
        capabilities or configuration.

        Args:
            value (float): The desired rotor speed, typically in revolutions per minute (RPM).

        Returns:
            success (bool): True if successfull, False if not connected.
        """
        if not self.connectedSuccessfully():
            return False

        if value < 0.0:
            value = 0.0
            
        drehzahl_soll_REGISTER = 2
        success = self.instrument.write_float(drehzahl_soll_REGISTER, value)
        return success

    def fetchRotorSpeed(self):
        """
        Retrieves the current rotor speed from the SEW device.

        This method queries the SEW controller to obtain the rotor speed. The speed
        is expressed in revolutions per minute (RPM).

        Returns:
            success (bool): True if successfull, False if not connected or if register was not found.
        """
        if not self.connectedSuccessfully():
            return None, False
        
        drehzahl_ist_REGISTER = 7
        ret_val = self.instrument.read_float(drehzahl_ist_REGISTER)
        success = (ret_val is not None)
        if success:
            self.measuredRotorSpeed = ret_val

        drehzahl_soll_REGISTER = 2
        ret_val2 = self.instrument.read_float(drehzahl_soll_REGISTER)
        success2 = (ret_val2 is not None)
        if success2:
            self.measuredSetRotorSpeed = ret_val2            
        return (ret_val, ret_val2), (success, success2)

    #get the last fetched, valid value for the rotor speed
    def getRotorSpeed(self):
        """
        Returns the locally stored rotor speed value.

        This method provides the value from the `measuredRotorSpeed` attribute
        rather than actively querying the device as fetchRotorSpeed does. 

        Returns:
        float: The last measured rotor speed in revolutions per minute (RPM).
        """
        return self.measuredRotorSpeed
    
    #get the last fetched, valid value for the set rotor speed
    def getSetRotorSpeed(self):
        """
        Retrieves the last set rotor speed value.

        This method returns the speed value that was previously
        requested for the SEW device by setMotorSpeed. 

        Returns:
            float: The rotor speed that was last set, typically in revolutions per
            minute (RPM).
        """
        return self.measuredSetRotorSpeed