"""Wrapper class for Atlas Scientific sensors that implements the FormalHardwareInterface.

This class provides a standardized interface for interacting with Atlas Scientific sensors
(pH, EC, RTD, ORP) including measurement reading, tolerance checking, and calibration queries.
"""
from .formalHardwareInterface import FormalHardwareInterface

class AtlasSensorWrapper(FormalHardwareInterface):
    """
    Wraps Atlas Scientific sensors with additional functionality for process control.

    This class acts as a wrapper around AtlasSensor instances, providing a consistent
    interface for hardware interaction including value reading, tolerance validation,
    and calibration management. It implements the FormalHardwareInterface for integration
    with the broader control system.

    Attributes:
        _taskModel: The task model providing target values and process parameters
        _atlasSensor: The underlying AtlasSensor instance for hardware communication
        _MOD: Module identifier string (e.g., 'pH', 'EC', 'RTD', 'ORP')
        _measurement: The last measured value from the sensor
        _targetValueColumn: Column name for target value lookup in task model
        _lower_tolerance: Lower tolerance multiplier for value validation
        _upper_tolerance: Upper tolerance multiplier for value validation
    """
    def __init__(self, taskModel, atlasSensor, MOD, targetValueColumn=None, lower_tolerance=0.0, upper_tolerance=100.0):
        self._taskModel= taskModel
        self._atlasSensor = atlasSensor
        self._MOD = MOD
        self._measurement = None
        self._targetValueColumn= targetValueColumn
        self._lower_tolerance = lower_tolerance
        self._upper_tolerance = upper_tolerance

    """
    Sets the column name for target value lookup in the task model.

    Args:
        targetValueColumn: Column name to use for fetching target values from task model
    """
    def setTargetValueColumn(self, targetValueColumn):
        self._targetValueColumn = targetValueColumn

    """
    Sets the relative tolerance bounds for value validation.

    Args:
        lower_tolerance: Lower bound multiplier (default: 0.0)
        upper_tolerance: Upper bound multiplier (default: 100.0)
    """
    def setRelativeTolerance(self, lower_tolerance=0.0, upper_tolerance=100.0):
        self._lower_tolerance = lower_tolerance
        self._upper_tolerance = upper_tolerance

    """
    Reads the current measurement from the sensor.

    Updates the internal measurement state and returns the latest value.

    Returns:
        float: The current measured value from the sensor
    """
    def updateMeasuredValue(self):
        self._measurement = self._atlasSensor.readOutValue(self._MOD)   
        return self._measurement 

    """
    Returns the last measured value from the sensor.

    Returns:
        float: The last measured value, or None if no measurement has been taken
    """
    def getMeasuredValue(self):
        return self._measurement 

    """
    Returns a formatted string for display purposes.

    Combines the module identifier with the measured value rounded to one decimal place.

    Returns:
        str: Formatted string in format "MOD: measurement"
    """
    def getDisplayValue(self):
        return self._MOD + ': ' +  str(round(self._measurement,1))

    """
    Checks if the current measurement is within the acceptable tolerance range.

    Compares the measured value against the target value from the task model,
    using the configured lower and upper tolerance multipliers.

    Returns:
        bool: True if measurement is within tolerance or no target is configured,
              False otherwise
    """
    def valueInTolerance(self):
        if self._targetValueColumn is not None:
            targetValue = self._taskModel.getCurrentTargetValue(column=self._targetValueColumn)
            return self._measurement > targetValue*self._lower_tolerance and self._measurement < targetValue * self._upper_tolerance
        else:
            return True

    def queryLowAverage(self, target):
        return self._atlasSensor.queryLowAverage(self._MOD, target)

    """
    Queries the sensor for a mid calibration point average.

    Sends a calibration query to set the middle calibration point for the sensor.

    Args:
        target: The target value for the mid calibration point

    Returns:
        str: The response string from the sensor
    """
    def queryMidAverage(self, target):
        return self._atlasSensor.queryMidAverage(self._MOD, target)

    """
    Queries the sensor for a high calibration point average.

    Sends a calibration query to set the upper calibration point for the sensor.

    Args:
        target: The target value for the high calibration point

    Returns:
        str: The response string from the sensor
    """
    def queryHighAverage(self, target):
        return self._atlasSensor.queryHighAverage(self._MOD, target)
    
    """
    Clears the calibration data on the sensor.

    Sends a clear command to reset the sensor's calibration settings.

    Returns:
        str: The response string from the sensor
    """
    def queryClear(self):
        return self._atlasSensor.queryClear(self._MOD)
    
    """
    Resets the sensor to factory default settings.

    Sends a factory reset command to restore default sensor configuration.

    Returns:
        str: The response string from the sensor
    """
    def queryFactory(self):
        return self._atlasSensor.queryFactory(self._MOD)
