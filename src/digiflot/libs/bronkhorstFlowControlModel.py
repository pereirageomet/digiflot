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
    def __init__(self):
        self.measuredAirFlow = -1.0
        self.measuredSetAirFlow = -1.0
        self.instrument, self.successINIT = self.getConnection()

    def __del__(self):
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
        return self.successINIT

    def setAirFlow(self, value):
        if not self.connectedSuccessfully():
            return False

        if value < 0.0:
            value = 0.0

        if value > 10.0:
            value = 10.0

        success = self.instrument.writeParameter(206, value)
        return success

    def fetchAirFlow(self):
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

    #get the last fetched, valid value for the air flow
    def getAirFlow(self):
        return self.measuredAirFlow
    
    #get the last fetched, valid value for the set air flow
    def getSetAirFlow(self):
        return self.measuredSetAirFlow