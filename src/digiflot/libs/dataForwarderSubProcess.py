"""Module providing data forwarding subprocess functionality.

This module handles forwarding sensor data and images to an MQTT broker
in a separate process. It manages MQTT connections, serializes data for
transmission, and handles network-related delays.
"""
import logging
logger = logging.getLogger(__name__)

import time
import json
import pandas as pd
import numpy as np
import base64

try:
    from libs.mqttInterface import MqttInterface
    from libs import hardwareInfoProvider 
except:
    from .mqttInterface import MqttInterface
    from . import hardwareInfoProvider

def evaluateRequest(message_queue, has_finished, mqttInterface, configuration):
    """Process control messages from the queue to manage MQTT connection.

    :param message_queue: Queue for receiving control messages
    :param has_finished: Flag indicating if the process should finish
    :param mqttInterface: Current MQTT interface instance
    :param configuration: Current MQTT configuration dictionary
    :return: Tuple of (updated has_finished, updated mqttInterface)
    """
    #Default case
    if message_queue.empty():
        return has_finished, mqttInterface
    else:
        message = message_queue.get()
        if isinstance(message, dict):
            # extract message string from dict and pass the dct without the message on
            msg = message.pop("message")
            dct = message
            message = msg

        if message == "START":
            pass
        elif message == "STOP":
            pass
        elif message == "LOAD":
            disconnectFromMqtt(mqttInterface)
            mqttInterface = connectToMqtt(**dct)
            if mqttInterface is not None:
                #successfull connection
                #update configuration for all processes
                configuration["broker"] = dct["broker"]
                configuration["port"] = dct["port"]
                configuration["topic_sub"] = dct["topic_sub"]
                configuration["topic_pub"] = dct["topic_pub"]
                configuration["username"] = dct["username"]
                configuration["password"] = dct["password"]
            else:
                logger.error(f"Error when calling connectToMqtt. Passed values: {dct}")
                #reconnect with previous settings
                mqttInterface = connectToMqtt(**configuration)

        elif message == "FINISH":
            has_finished = True
        return has_finished, mqttInterface

def connectToMqtt(broker, port, topic_sub, topic_pub, username, password, **kwargs):
    """Create and connect an MQTT interface instance.

    :param broker: MQTT broker address
    :param port: MQTT broker port
    :param topic_sub: Subscription topic
    :param topic_pub: Publishing topic
    :param username: MQTT username
    :param password: MQTT password
    :param kwargs: Additional keyword arguments
    :return: MqttInterface instance or None on failure
    """
    try:
        mqttInterface = MqttInterface(broker, port, topic_sub, topic_pub, username, password)
        mqttInterface.connectMqtt()
        mqttInterface.client.loop_start()
    except:
        mqttInterface = None
        logger.error(f"Error when connecting to mqtt broker. Passed values: {broker}, {port}, {topic_sub}, {topic_pub}, {username}, {password}, {kwargs}")
    return mqttInterface

def disconnectFromMqtt(mqttInterface):
    """Disconnect and stop the MQTT client loop.

    :param mqttInterface: MQTT interface instance to disconnect
    """
    try:
        mqttInterface.client.loop_stop()
        mqttInterface.client.disconnect()
    except:
        logger.error("Error when disconnecting from mqtt broker.")

def startDataForwarderLoop(insights_dict_queue, image_array, imageHeight, imageWidth, nof_pixel_values, message_queue, configuration):
    mqttInterface = connectToMqtt(**configuration)
    
    if mqttInterface is None:
        return

    has_finished = False
    while not has_finished:
        if not insights_dict_queue.empty():
            handleOverDueRequestsDueToBadInternet(insights_dict_queue, image_array, imageHeight, imageWidth, nof_pixel_values, mqttInterface)

        has_finished, mqttInterface = evaluateRequest(message_queue, has_finished, mqttInterface, configuration)
        time.sleep(1e-3)

    mqttInterface.client.loop_stop()
    mqttInterface.client.disconnect()

def handleOverDueRequestsDueToBadInternet(insights_dict_queue, image_array, imageHeight, imageWidth, nof_pixel_values, mqttInterface):
    """Process accumulated insights and publish them with current images.

    Handles network delays by publishing old insights without images,
    then the latest insight with current image data.

    :param insights_dict_queue: Queue of insight dictionaries
    :param image_array: Shared memory array for image data
    :param imageHeight: Height of images in pixels
    :param imageWidth: Width of images in pixels
    :param nof_pixel_values: Number of color channels
    :param mqttInterface: MQTT interface for publishing
    """
    insights_lst = []
    while not insights_dict_queue.empty():
        insights_lst.append(insights_dict_queue.get())
    
    #the newest one is up-to-date
    latest_insights = insights_lst.pop()
    doRegularHandling(latest_insights, image_array, imageHeight, imageWidth, nof_pixel_values, mqttInterface)

    # Publish first old, then the up-to-date insights to avoid changing the order
    for old_insights in insights_lst:
        old_insights["image_top_view"] = b''            
        old_insights["image_side_view"] = b''
        dataLakeStr = dataLakeSerializer(old_insights)
        mqttInterface.publish(dataLakeStr)

    dataLakeStr = dataLakeSerializer(latest_insights)
    mqttInterface.publish(dataLakeStr)

def doRegularHandling(insights, image_array, imageHeight,imageWidth,nof_pixel_values, mqttInterface):
    """Enrich insights with hardware info and attach current images.

    :param insights: Dictionary of insight data to process
    :param image_array: Shared memory array for image data
    :param imageHeight: Height of images in pixels
    :param imageWidth: Width of images in pixels
    :param nof_pixel_values: Number of color channels
    :param mqttInterface: MQTT interface for publishing
    """
    enrichInsightsWithHardwareInformation(insights)
    if insights["images_included"]:
        with image_array.get_lock():
            # then in each new process create a new numpy array using:
            image = np.frombuffer(image_array.get_obj(), dtype=np.uint8).reshape((imageHeight,imageWidth,nof_pixel_values)).copy()
        insights["image_top_view"] = image            
        insights["image_side_view"] = b''
    else:
        insights["image_top_view"] = b''            
        insights["image_side_view"] = b''

def closeQueue(queue, sentinel_message):
    """Close a multiprocessing queue and join its thread.

    :param queue: Queue to close
    :param sentinel_message: Message sentinel to stop draining the queue
    """
    message = None
    ts = time.time()
    #while not message_queue.empty():
    #    message_queue.get()    
    while message != sentinel_message:
        if not queue.empty():
            message = queue.get()
        time.sleep(1e-3)
        if ts - time.time() > 10.0:
            break
    queue.close()
    queue.join_thread()

def dataLakeSerializer(insights):
    """Serialize insights dictionary to a data lake format string.

    Converts sensor data, hardware/software states, and images into
    a JSON-based format suitable for storage and transmission.

    :param insights: Dictionary containing sensor data, images, and configurations
    :return: Serialized string in data lake format
    """
    ### match dct to target_dct
    model_data_dct = json.loads(insights["model_data_JSON"])
    configuration_dct = insights["configuration"]
    project = configuration_dct["MainWindow"].pop("project")
    run = model_data_dct.pop("selectedSample")
    stage_name = model_data_dct.pop("currentstagename")    
    software_config_dct = {key : configuration_dct.pop(key) for key in ["DataForwarder", "Controller", "MainWindow"]}
    setup_config_dct = configuration_dct

    software_state_JSON = json.dumps(model_data_dct, allow_nan=True)
    software_config_dct_JSON = json.dumps(software_config_dct, allow_nan=False)
    setup_config_dct_JSON = json.dumps(setup_config_dct, allow_nan=False)
    hardware_state_JSON = json.dumps(insights["hardware_state"], allow_nan=False)
    hardware_config_JSON = json.dumps(insights["hardware_config"], allow_nan=False)

    target_dct = {"timestamp" : insights["sensor_data"]["timestamp"], \
                            "ORP" : insights["sensor_data"]["ORP"], \
                            "pH" : insights["sensor_data"]["pH"], \
                            "EC" : insights["sensor_data"]["EC"], \
                            "RTD" : insights["sensor_data"]["RTD"], \
                            "LIDAR" :insights["sensor_data"]["LIDAR"], \
                            "project" : project, \
                            "run" : run, \
                            "stage_name" : stage_name, \
                            "setup_state" : None, \
                            "setup_config" : setup_config_dct_JSON, \
                            "hardware_state" : hardware_state_JSON, \
                            "hardware_config" : hardware_config_JSON, \
                            "software_state" : software_state_JSON, \
                            "software_config" : software_config_dct_JSON, \
                            "image_top_view" : str(base64.b64encode(insights["image_top_view"]))[2:-1], \
                            "image_side_view" : str(base64.b64encode(insights["image_side_view"]))[2:-1]\
                }
    
    params = [target_dct["timestamp"], target_dct["ORP"], target_dct["pH"], target_dct["EC"], target_dct["RTD"], target_dct["LIDAR"], target_dct["project"], target_dct["run"], target_dct["stage_name"], target_dct["setup_state"], target_dct["setup_config"], target_dct["hardware_state"], target_dct["hardware_config"], target_dct["software_state"], target_dct["software_config"], target_dct["image_top_view"], target_dct["image_side_view"]]
    
    ##
    for i, par in enumerate(params):
        if par is None or pd.isna(par):
            params[i] = ""
        elif isinstance(par, dict):
            #check for nan or None entries of the dict and remove them
            rm_lst = []
            for k,v in par.items():
                if v is None or pd.isna(v):
                    rm_lst.append(k)
            for k in rm_lst:
                par.pop(k)
            #check if the dictionary is empty ...
            if len(par) > 0:
                params[i] = json.dumps(par, allow_nan=False)         
            else:
                params[i] = ""
        elif not isinstance(par, str):
            #int64 not json serializable
            if isinstance(par, np.int64):
                par = float(par)
            params[i] = json.dumps(par, allow_nan=False)

    #Join to &-seperated string
    res_str = '&'.join(params)      
    return res_str

def serializeInsights(insights):
    """Serialize insights dictionary to MQTT payload string.
    
    :param insights: Dictionary containing sensor data and metadata
    :return: Serialized payload string
    """
    import json
    import base64
    import numpy as np
    import pandas as pd
    
    sensor_data = insights.get("sensor_data", {})
    model_data_dct = insights.get("model_data_JSON", {})
    configuration_dct = insights.get("configuration", {})
    images_included = insights.get("images_included", False)
    
    project = configuration_dct["MainWindow"].pop("project")
    run = model_data_dct.pop("selectedSample", "")
    stage_name = model_data_dct.pop("currentstagename", "")    
    software_config_dct = {key: configuration_dct.pop(key) for key in ["DataForwarder", "Controller", "MainWindow"] if key in configuration_dct}
    setup_config_dct = configuration_dct

    software_state_JSON = json.dumps(model_data_dct, allow_nan=True)
    software_config_dct_JSON = json.dumps(software_config_dct, allow_nan=False)
    setup_config_dct_JSON = json.dumps(setup_config_dct, allow_nan=False)
    
    hardware_state_JSON = json.dumps(insights.get("hardware_state", {}), allow_nan=False)
    hardware_config_JSON = json.dumps(insights.get("hardware_config", {}), allow_nan=False)

    target_dct = {
        "timestamp": sensor_data.get("timestamp", ""),
        "ORP": sensor_data.get("ORP"),
        "pH": sensor_data.get("pH"),
        "EC": sensor_data.get("EC"),
        "RTD": sensor_data.get("RTD"),
        "LIDAR": sensor_data.get("LIDAR"),
        "project": project,
        "run": run,
        "stage_name": stage_name,
        "setup_state": None,
        "setup_config": setup_config_dct_JSON,
        "hardware_state": hardware_state_JSON,
        "hardware_config": hardware_config_JSON,
        "software_state": software_state_JSON,
        "software_config": software_config_dct_JSON,
        "image_top_view": "",
        "image_side_view": ""
    }
    
    if images_included:
        img_bytes = insights.get("image_top_view", b"")
        if img_bytes:
            target_dct["image_top_view"] = str(base64.b64encode(img_bytes))[2:-1]
    
    params = [
        target_dct["timestamp"], target_dct["ORP"], target_dct["pH"],
        target_dct["EC"], target_dct["RTD"], target_dct["LIDAR"],
        target_dct["project"], target_dct["run"], target_dct["stage_name"],
        target_dct["setup_state"], target_dct["setup_config"],
        target_dct["hardware_state"], target_dct["hardware_config"],
        target_dct["software_state"], target_dct["software_config"],
        target_dct["image_top_view"], target_dct["image_side_view"]
    ]
    
    for i, par in enumerate(params):
        if par is None or pd.isna(par):
            params[i] = ""
        elif isinstance(par, dict):
            rm_lst = [k for k, v in par.items() if v is None or pd.isna(v)]
            for k in rm_lst:
                par.pop(k)
            params[i] = json.dumps(par, allow_nan=False) if len(par) > 0 else ""
        elif isinstance(par, np.int64):
            params[i] = json.dumps(float(par), allow_nan=False)
        elif not isinstance(par, str):
            params[i] = json.dumps(par, allow_nan=False)

    return '&'.join(params)

def enrichInsightsWithHardwareInformation(insights):
    """Add hardware state and configuration to insights dictionary.

    :param insights: Dictionary to enrich with hardware information
    """
    hardwareState = hardwareInfoProvider.provideHardwareState()
    hardwareConfig = hardwareInfoProvider.provideHardwareConfig()
    insights.update({"hardware_state": hardwareState, "hardware_config": hardwareConfig})

#for testing locally
def main():
    """Entry point for testing the subprocess module."""
    import multiprocessing as mp
    queue = mp.Queue()
    queue2 = mp.Queue()
    queue2.put({"message" : "LOAD", "broker" : "10.20.30.40", "port" : 1212, "topic_sub" : "Server/Sub", "topic_pub" : "topic", "username" : "PASS", "password" : "PASS"})
    queue2.put("FINISH")
    startDataForwarderLoop(queue, queue2)

if __name__=="__main__":
    main()
