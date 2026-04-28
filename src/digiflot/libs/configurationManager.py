"""
This module manages process-shared configuration dictionaries for the DigiFlot application.

It provides a centralized configuration system using multiprocessing.Manager() to share
configuration data across multiple processes safely. Configuration can be loaded from
JSON files and defaults are provided for all supported components.

The module supports dynamic configuration updates and ensures all default values
are present in the shared configuration.
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
            "cameras": []
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

    Creates a new Manager instance and populates shared_config with default values
    for all supported components. If a configuration file exists at the given path,
    it loads and merges user configuration with defaults.

    Args:
        path: Path object pointing to the configuration directory
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
    """
    Update the configuration path and reload configuration from the new location.

    If the manager has been initialized, this function updates the json_path and
    attempts to load configuration from the new location, storing defaults if not found.

    Args:
        path: Path object pointing to the new configuration directory
    """
    global manager
    global shared_config
    global json_path
    if manager is not None:
        # update path
        json_path = path
        # try to load configuration from updated path, or store default values alternatively
        loadConfFromJsonRelentlessly()

def tryToUpdateSharedConfiguration(path):
    """
    Attempt to update the configuration path and load configuration without error handling.

    If the manager has been initialized, this function updates the json_path and
    attempts to load configuration from the new location. Does not store defaults
    if the configuration file is not found.

    Args:
        path: Path object pointing to the new configuration directory
    """
    global manager
    global shared_config
    global json_path
    if manager is not None:
        # update path
        json_path = path
        # just try to load configuration from updated path
        tryToLoadConfFromJson()

def getConfig(key):
    """
    Retrieve configuration values for the specified key.

    Args:
        key: Configuration key to retrieve. Use "all" to retrieve entire shared_config.

    Returns:
        dict or None: Configuration dictionary for the key, the entire shared_config if
                      key is "all", or None if the key is not found.
    """
    if key == "all":
        return shared_config
    elif key in shared_config.keys():
        return shared_config[key]
    else:
        logger.error(f"The key {key} passed to getConfig is not one of shared_config.")
        return None

def convertSharedConfigtoSerializableDict():
    """
    Convert the shared configuration to a regular dictionary.

    Converts all Manager.dict objects to regular Python dictionaries to enable
    JSON serialization.

    Returns:
        dict: A serializable dictionary representation of the configuration
    """
    global shared_config
    # Convert managed dictionaries to regular dictionaries
    dct = {}
    for key, nested_dct in shared_config.items():
        dct[key] = dict(nested_dct)
    return dct

def storeToJson():
    """
    Store the current configuration to a JSON file.

    Serializes the shared configuration to a JSON file named 'configuration.json'
    in the configured json_path directory with 4-space indentation.
    """
    global json_path
    with open(json_path/"configuration.json", "w") as file:
        json.dump(convertSharedConfigtoSerializableDict(), file, indent=4)

def storeJsonToPath(json_path):
    """
    Store the current configuration to a JSON file at a specific path.

    Args:
        json_path: Path object specifying where to save the configuration file
    """
    with open(json_path/"configuration.json", "w") as file:
        json.dump(convertSharedConfigtoSerializableDict(), file, indent=4)

def storeConfToJsonRelentlessly():
    """
    Store configuration to JSON with retry logic.

    Continuously attempts to write the configuration to disk, retrying every
    0.1 seconds until successful. This ensures configuration persistence
    even if the file is temporarily locked.
    """
    success = False
    while not success:
        try:        
            storeToJson()
        except:
            time.sleep(0.1)
        else:
            success = True

def loadFromJson():
    """
    Load configuration from the JSON file.

    Returns:
        dict: The configuration dictionary loaded from 'configuration.json'
    """
    global json_path
    with open(json_path/"configuration.json", "r") as file:
        dct = json.load(file)
    return dct

def loadConfFromJsonRelentlessly():
    """
    Load configuration from JSON with retry logic and default fallback.

    Attempts to load configuration from the JSON file. If the file doesn't exist,
    generates defaults and saves them. Retries every 0.1 seconds on error until
    successful. Merges loaded configuration with existing shared_config and
    ensures all defaults are present.
    """
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
    """
    Attempt to load configuration from JSON without error handling.

    Loads configuration from the JSON file if it exists and merges it with
    the existing shared_config. Does nothing if the file doesn't exist.
    """
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
