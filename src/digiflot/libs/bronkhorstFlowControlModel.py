"""Module for Bronkhorst mass flow controller interface.

This module provides a wrapper around the propar library to interface with
Bronkhorst mass flow controllers via serial connection. It handles device
initialization, flow control, and measurement fetching.
"""
import logging
logger = logging.getLogger(__name__)
try:
    import propar
except:
    propar = None
    PROPAR_INSTALLED = False
    logger.info("Bronkhorst driver is not installed.")
else:
    PROPAR_INSTALLED = True    

import pathlib

class BronkhorstFlowControlModel:
    """
    Interface for Bronkhorst mass flow controllers.

    This class provides a wrapper around the propar library to communicate with
    Bronkhorst mass flow controllers via serial connection. It handles device
    initialization, air flow control, and measurement fetching.

    Attributes:
        measuredAirFlow (float): Last fetched actual air flow measurement in mL/min
        measuredSetAirFlow (float): Last fetched set air flow value in mL/min
        instrument: The propar instrument object for communication
        successINIT (bool): Flag indicating successful device initialization
    """
    def __init__(self):
        """
        Initialize the BronkhorstFlowControlModel and attempt device connection.
        """
        self.measuredAirFlow = -1.0
        self.measuredSetAirFlow = -1.0
        self.instrument, self.successINIT = self.getConnection()

    def __del__(self):
        """
        Cleanup method that sets air flow to zero on deletion.
        """
        self.setAirFlow(0.0)

    def getConnection(self):
        if not PROPAR_INSTALLED:
            return None, False

        paths = list(pathlib.Path("/dev/").glob("ttyUSB[0-9]"))
        if len(paths) == 0:
            logger.info("No Serial-To-USB-Adapter mounted.")
            return None, False

        instrument = None
        for path in paths:
            try:
                # Connect to the local instrument, when no settings provided
                # defaults to locally connected instrument (address=0x80, baudrate=38400)
                instrument = propar.instrument(str(path))
            except:
                instrument = None
                logger.info(f"No Bronkhorst device at {str(path)}.")
            else:
                ret_id = instrument.id
                if ret_id is not None:
                    logger.info(f"Found Bronkhorst device with id {ret_id} at {str(path)}.")
                    #One Bronkhorst device is enough ...
                    break
                else:
                    instrument = None
                    logger.info(f"No Bronkhorst device at {str(path)}.")

        successINIT = (instrument is not None)
        return instrument, successINIT

    def connectedSuccessfully(self):
        """
        Check if the device was successfully initialized.

        Returns:
            bool: True if device connection and initialization succeeded, False otherwise.
        """
        return self.successINIT

    def setAirFlow(self, value):
        """
        Set the air flow setpoint for the Bronkhorst controller.

        Args:
            value (float): Desired air flow in mL/min. Clamped to range [0.0, 10.0].

        Returns:
            bool: True if the parameter was written successfully, False otherwise.
        """
        if not self.connectedSuccessfully():
            return False

        if value < 0.0:
            value = 0.0

        if value > 10.0:
            value = 10.0

        success = self.instrument.writeParameter(206, value)
        return success

    def fetchAirFlow(self):
        """
        Fetch current and set air flow values from the Bronkhorst controller.

        Returns:
            tuple: ((actual_flow, set_flow), (success_actual, success_set))
                   where each flow value and success flag correspond to actual and set values.
                   Returns (None, False) if device is not connected.
        """
        if not self.connectedSuccessfully():
            return None, False
        
        ret_val = self.instrument.readParameter(205)
        success = (ret_val is not None)
        if success:
            self.measuredAirFlow = ret_val
            
        ret_val2 = self.instrument.readParameter(206)
        success2 = (ret_val2 is not None)
        if success2:
            self.measuredSetAirFlow = ret_val2            
        return (ret_val, ret_val2), (success, success2)

    def getAirFlow(self):
        """
        Get the last fetched actual air flow value.

        Returns:
            float: The last measured air flow in mL/min, or -1.0 if not yet fetched.
        """
        return self.measuredAirFlow
    
    def getSetAirFlow(self):
        """
        Get the last fetched set air flow value.

        Returns:
            float: The last set air flow value in mL/min, or -1.0 if not yet fetched.
        """
        return self.measuredSetAirFlow
