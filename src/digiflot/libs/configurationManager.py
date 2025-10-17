"""
This is a module for handling process-shared dictionaries that contains configuration data for several classes.
"""
import json
import time
import logging
logger = logging.getLogger(__name__)
from multiprocessing import Manager

manager = None
shared_config = None
json_path = None

def initializeSharedConfiguration(path):
    global manager
    global shared_config
    global json_path
    json_path = path
    if manager is None:
        manager = Manager()
        # Initialization with default values for linux
        shared_config = {}
        shared_config["RaspiCamModel"] = manager.dict({"camera trademark" : "Raspberry Pi", "image interval" : 1.0, "exposure time" : 20, "gain" : 20.0, "normalize image" : False, "output raw image" : False, "image format" : "tiff", "brightness" : 0.0, "contrast" : 1.0, "saturation" : 1.0, "sharpness" : 1.0})
        shared_config["DahengCamModel"] = manager.dict({"camera trademark" : "Daheng", "image interval" : 1.0, "exposure time" : 200, "gain" : 1.0, "normalize image" : False, "output raw image" : False, "image format" : "tiff"})
        shared_config["DataForwarder"] = manager.dict({"broker" :  "10.20.30.40", "port" : 1212, "topic_sub" : "Server/Sub", "topic_pub" : "topic", "username" : "PASS", "password" : "PASS"})
        shared_config["TabViewInformation"] = {"broker" :  "10.20.30.40", "port" : 1212, "topic_sub" : "Server/Sub", "topic_pub" : "topic_view", "username" : "PASS", "password" : "PASS"}
        shared_config["Controller"] = {"measurement timer" : 1000, "run tab timer" : 100, "camera tab timer" : 30}
        shared_config["MainWindow"] = {"software" : "DigiFlot Lab Assistant", "project" : "default", "camera model class" : "RaspiCamModel","font scale":1,"background color": "#000080","font color": "#ffffff"}
        # try to load configuration, or store default values alternatively
        loadConfFromJsonRelentlessly()

def updateSharedConfiguration(path):
    global manager
    global shared_config
    global json_path
    if manager is not None:
        # update path
        json_path = path
        # try to load configuration from updated path, or store default values alternatively
        loadConfFromJsonRelentlessly()

def tryToUpdateSharedConfiguration(path):
    global manager
    global shared_config
    global json_path
    if manager is not None:
        # update path
        json_path = path
        # just try to load configuration from updated path
        tryToLoadConfFromJson()

def getConfig(key):
    if key == "all":
        return shared_config
    elif key in shared_config.keys():
        return shared_config[key]
    else:
        logger.error(f"The key {key} passed to getConfig is not one of shared_config.")
        return None

def convertSharedConfigtoSerializableDict():
    global shared_config
    # Convert managed dictionaries to regular dictionaries
    dct = {}
    for key, nested_dct in shared_config.items():
        dct[key] = dict(nested_dct)
    return dct

def storeToJson():
    global json_path
    with open(json_path/"configuration.json", "w") as file:
        json.dump(convertSharedConfigtoSerializableDict(), file, indent=4)

def storeJsonToPath(json_path):
    with open(json_path/"configuration.json", "w") as file:
        json.dump(convertSharedConfigtoSerializableDict(), file, indent=4)

def storeConfToJsonRelentlessly():
    success = False
    while not success:
        try:        
            storeToJson()
        except:
            time.sleep(0.1)
        else:
            success = True

def loadFromJson():
    global json_path
    with open(json_path/"configuration.json", "r") as file:
        dct = json.load(file)
    return dct

def loadConfFromJsonRelentlessly():
    success = False
    while not success:
        try:        
            dct = loadFromJson()
        except FileNotFoundError:
            # There is no configuration file yet ... save default
            global json_path
            logger.info(f"Configuration.json not found at {str(json_path)}. Generated json file from preset variables.")
            storeConfToJsonRelentlessly()
            success = True
        except:
            time.sleep(0.1)
        else:
            global shared_config
            # load dicts from dct whose key is element of the keys of the share_config
            for className in shared_config.keys():
                if className in dct.keys():
                    if isinstance(shared_config[className], dict):
                        shared_config[className].update(dct[className])
                    else:
                        shared_config[className].update(manager.dict(dct[className]))

            success = True  

def tryToLoadConfFromJson():
    try:        
        dct = loadFromJson()
    except FileNotFoundError:
        pass
    else:
        global shared_config
        # load dicts from dct whose key is element of the keys of the share_config
        for className in shared_config.keys():
            if className in dct.keys():
                if isinstance(shared_config[className], dict):
                    shared_config[className].update(dct[className])
                else:
                    shared_config[className].update(manager.dict(dct[className]))
