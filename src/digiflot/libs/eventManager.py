_eventDict = {} 

def registerEvent(eventName, eventHandle):
    #if eventHandle is isinstance(pyqtSignal) and eventName.isinstance(string.String):
    _eventDict[eventName] = eventHandle 

def connectToEvent(eventName, methodHandle):
    #if eventName in self._eventDict.keys():
    _eventDict[eventName].connect(methodHandle)