# Describes abstract interface class that must be implemented by every hardware interface class
import abc
class FormalHardwareInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'updateMeasuredValue') and 
                callable(subclass.updateMeasuredValue) and 
                hasattr(subclass, 'getMeasuredValue') and 
                callable(subclass.getMeasuredValue) and                 
                hasattr(subclass, 'getDisplayValue') and 
                callable(subclass.getDisplayValue) and                 
                hasattr(subclass, 'valueInTolerance') and 
                callable(subclass.getDisplayValue) and                 
                hasattr(subclass, 'queryMidAverage') and 
                callable(subclass.getDisplayValue) and                 
                hasattr(subclass, 'queryLowAverage') and 
                callable(subclass.getDisplayValue) and                 
                hasattr(subclass, 'queryHighAverage') and 
                callable(subclass.valueInTolerance) or 
                NotImplemented)

    @abc.abstractmethod
    def updateMeasuredValue(self):
        """Pull measured value from device into interface class"""
        raise NotImplementedError

    @abc.abstractmethod
    def getMeasuredValue(self):
        """Return last measured value"""
        raise NotImplementedError

    @abc.abstractmethod
    def getDisplayValue(self):
        """Return value to be displayed"""
        raise NotImplementedError

    @abc.abstractmethod
    def valueInTolerance(self):
        """Check if measured value is in tolerance for the device"""
        raise NotImplementedError
    
    @abc.abstractmethod
    def queryMidAverage(self):
        """Query to make an average value and use it as the middle calibration point."""
        raise NotImplementedError

    @abc.abstractmethod
    def queryLowAverage(self):
        """Query to make an average value and use it as the lower calibration point."""
        raise NotImplementedError

    @abc.abstractmethod
    def queryHighAverage(self):
        """Query to make an average value and use it as the upper calibration point."""
        raise NotImplementedError