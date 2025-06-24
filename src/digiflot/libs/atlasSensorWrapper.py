try:
    from libs.formalHardwareInterface import FormalHardwareInterface
except:
    from .formalHardwareInterface import FormalHardwareInterface

class AtlasSensorWrapper(FormalHardwareInterface):
    def __init__(self, taskModel, atlasSensor, MOD, targetValueColumn=None, lower_tolerance=0.0, upper_tolerance=100.0):
        self._taskModel= taskModel
        self._atlasSensor = atlasSensor
        self._MOD = MOD
        self._measurement = None
        self._targetValueColumn= targetValueColumn
        self._lower_tolerance = lower_tolerance
        self._upper_tolerance = upper_tolerance

    def setTargetValueColumn(self, targetValueColumn):
        self._targetValueColumn = targetValueColumn

    def setRelativeTolerance(self, lower_tolerance=0.0, upper_tolerance=100.0):
        self._lower_tolerance = lower_tolerance
        self._upper_tolerance = upper_tolerance

    def updateMeasuredValue(self):
        self._measurement = self._atlasSensor.readOutValue(self._MOD)   
        return self._measurement 

    def getMeasuredValue(self):
        return self._measurement 

    def getDisplayValue(self):
        return self._MOD + ': ' +  str(round(self._measurement,1))

    def valueInTolerance(self):
        if self._targetValueColumn is not None:
            targetValue = self._taskModel.getCurrentTargetValue(column=self._targetValueColumn)
            return self._measurement > targetValue*self._lower_tolerance and self._measurement < targetValue * self._upper_tolerance
        else:
            return True

    def queryLowAverage(self, target):
        return self._atlasSensor.queryLowAverage(self._MOD, target)

    def queryMidAverage(self, target):
        return self._atlasSensor.queryMidAverage(self._MOD, target)

    def queryHighAverage(self, target):
        return self._atlasSensor.queryHighAverage(self._MOD, target)
    
    def queryClear(self):
        return self._atlasSensor.queryClear(self._MOD)
    
    def queryFactory(self):
        return self._atlasSensor.queryFactory(self._MOD)