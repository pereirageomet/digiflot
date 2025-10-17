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

def _get_default_config():
    """Return a dictionary with all default configuration values."""
    defaults = {
        "RaspiCamModel": {
            "camera trademark": "Raspberry Pi",
            "image interval": 1.0,
            "exposure time": 20,
            "gain": 20.0,
            "normalize image": False,
            "output raw image": False,
            "image format": "tiff",
            "brightness": 0.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
        },
        "DahengCamModel": {
            "camera trademark": "Daheng",
            "image interval": 1.0,
            "exposure time": 200,
            "gain": 1.0,
            "normalize image": False,
            "output raw image": False,
            "image format": "tiff",
        },
        "DataForwarder": {
            "broker": "10.20.30.40",
            "port": 1212,
            "topic_sub": "Server/Sub",
            "topic_pub": "topic",
            "username": "PASS",
            "password": "PASS",
        },
        "TabViewInformation": {
            "broker": "10.20.30.40",
            "port": 1212,
            "topic_sub": "Server/Sub",
            "topic_pub": "topic_view",
            "username": "PASS",
            "password": "PASS",
        },
        "Controller": {
            "measurement timer": 1000,
            "run tab timer": 100,
            "camera tab timer": 30,
        },
        "MainWindow": {
            "software": "DigiFlot Lab Assistant",
            "project": "default",
            "camera model class": "RaspiCamModel",
            "font scale": 1,
            "background color": "#000000",
            "font color": "#ffffff",
        },
    }
    return defaults


def _ensure_all_defaults_present():
    """Ensure that any missing keys/subkeys from the defaults are added to shared_config."""
    global shared_config, manager
    defaults = _get_default_config()

    for key, default_val in defaults.items():
        # Create top-level if missing
        if key not in shared_config:
            shared_config[key] = (
                manager.dict(default_val) if isinstance(default_val, dict) else default_val
            )
            continue

        # Update nested dicts if partially missing
        target = shared_config[key]
        if isinstance(default_val, dict):
            if isinstance(target, dict):
                for subkey, subval in default_val.items():
                    if subkey not in target:
                        target[subkey] = subval
            elif hasattr(target, "keys"):  # Manager.dict
                for subkey, subval in default_val.items():
                    if subkey not in target.keys():
                        target[subkey] = subval


def initializeSharedConfiguration(path):
    """
    Initialize the shared configuration manager with default values.
    Loads user configuration from JSON if available, otherwise stores defaults.
    """
    global manager, shared_config, json_path
    json_path = path

    if manager is None:
        manager = Manager()
        defaults = _get_default_config()

        # Initialize with defaults using manager.dict for subdicts
        shared_config = {}
        for key, val in defaults.items():
            if isinstance(val, dict):
                shared_config[key] = manager.dict(val)
            else:
                shared_config[key] = val

        # Load user configuration and fill in any missing defaults
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
            
            _ensure_all_defaults_present()
            storeConfToJsonRelentlessly()  # optional but recommended
            
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
