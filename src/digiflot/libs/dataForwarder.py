"""
Module for forwarding measurement data to external data lakes via MQTT.

This class manages threading for MQTT communication to send sensor data,
configuration, and model data to external data collection systems.
"""
import time
import logging
import threading
import queue
from datetime import datetime, timezone
try:
    from libs import dataForwarderSubProcess
    from libs import configurationManager
except:
    from . import dataForwarderSubProcess
    from . import configurationManager  

logger = logging.getLogger(__name__)

class DataForwarder():
    """
    Manages data forwarding to external data lakes via MQTT.

    This class orchestrates the forwarding of measurement data, sensor readings,
    and configuration information to external data collection systems through
    an MQTT broker. It runs the actual data transmission in a separate subprocess
    for non-blocking operation.

    Attributes:
        configuration: MQTT broker configuration from shared configuration
        taskModel: The task model providing process data
        camInstance: Camera instance for image data
        controller: Controller instance for device access
        _process_handle: Reference to the subprocess handling MQTT communication
        _insights_queue: Queue for sending measurement data to the subprocess
        _message_queue: Queue for control messages to the subprocess
    """
    def __init__(self, taskModel, camInstance, controller):
        self.configuration = configurationManager.getConfig("DataForwarder")
        self.taskModel = taskModel
        self.camInstance = camInstance
        self.controller = controller
        self._thread = None
        self._stop_event = None
        self._insights_queue = None
        self._message_queue = None
        self._mqtt_interface = None
        self._running = False
        
    def cleanup(self):
        """Explicit cleanup method - call before destruction."""
        self.finishProcessesAndQueues()

    def __del__(self):
        self.cleanup()
        
    def setController(self, controller):
        """Setter for the controller attribute.

        Args:
            controller: New controller instance to use
        """
        self.controller = controller

    def _mqttLoop(self):
        """Background thread for MQTT communication."""
        try:
            self._mqtt_interface = dataForwarderSubProcess.connectToMqtt(**self.configuration)
            if self._mqtt_interface is None:
                logger.error("Failed to connect to MQTT broker")
                self._running = False
                return
            
            while not self._stop_event.is_set():
                try:
                    insights_dct = self._insights_queue.get(timeout=0.1)
                    self._publishInsights(insights_dct)
                    self._insights_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error in MQTT loop: {e}")
        finally:
            if self._mqtt_interface is not None:
                self._mqtt_interface.client.loop_stop()
                self._mqtt_interface.client.disconnect()
            self._running = False

    def _publishInsights(self, insights_dct):
        """Publish insights to MQTT broker.
        
        Args:
            insights_dct: Dictionary of insights to publish
        """
        try:
            payload = dataForwarderSubProcess.serializeInsights(insights_dct)
            self._mqtt_interface.client.publish(
                self.configuration["topic_pub"],
                payload=payload,
                qos=0
            )
        except Exception as e:
            logger.error(f"Failed to publish insights: {e}")

    def getBroker(self):
        """Get the MQTT broker address from configuration.

        Returns:
            str: The broker IP address or hostname
        """
        return self.configuration["broker"]

    def getPort(self):
        """Get the MQTT broker port from configuration.

        Returns:
            int: The broker port number
        """
        return self.configuration["port"]

    def getUsername(self):
        """Get the MQTT username from configuration.

        Returns:
            str: The username for broker authentication
        """
        return self.configuration["username"]

    def getPassword(self):
        """Get the MQTT password from configuration.

        Returns:
            str: The password for broker authentication
        """
        return self.configuration["password"]

    def getTopic_pub(self):
        """Get the MQTT publish topic from configuration.

        Returns:
            str: The topic to publish data to
        """
        return self.configuration["topic_pub"]

    def __del__(self):
        """Cleanup method to ensure thread termination."""
        if self._thread is not None and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=2)

    def pushDataToDataLake(self, images_included):
        """
        Push collected insights to the data lake.

        If the forwarding service is running, collects current insights and
        sends them to the data lake via the insights queue.

        Args:
            images_included: Whether to include image data in the payload
        """
        if self.isRunning():
            insights_dct = self.collectInsights(images_included)
            self._insights_queue.put(insights_dct)

    def collectInsights(self, images_included=True):
        """
        Collect all relevant data for forwarding to the data lake.

        Gathers measurement data, configuration, and semi-structured model data.
        Image data can be optionally included.

        Args:
            images_included: Whether to include image data (currently disabled)

        Returns:
            dict: Combined data dictionary ready for transmission
        """
        data = self.collectMeasurementData()
        data = self.filterDictForDataLakeDataColumns(data)
        conf_dct = configurationManager.convertSharedConfigtoSerializableDict()
        semi = self.taskModel.provideSemiStructuredData()
        #if images_included:
        #    img_bytes = self.fetchImageBytes()
        #else: 
        #    img_bytes = b""
        #return {"sensor_data": data, "image_top_view": img_bytes, "image_side_view": b"", "model_data_JSON": semi, "configuration" : conf_dct} 
        return {"sensor_data": data,  "model_data_JSON": semi, "configuration" : conf_dct, "images_included": images_included} 

    def collectMeasurementData(self):
        """
        Collect current measurements from all connected devices.

        Generates a timestamp and queries each device in the controller's
        device dictionary for its latest measurement.

        Returns:
            dict: Dictionary mapping device names to their measured values
        """
        unix_timestamp_sec = time.time()
        datetime_obj = datetime.fromtimestamp(unix_timestamp_sec).astimezone(timezone.utc)
        formatted_timestamp = datetime_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        data_dict = {"timestamp": formatted_timestamp}
        for dev_name, dev_handle in self.controller.deviceDictionary.items():
            data_dict[dev_name] = dev_handle.getMeasuredValue()
        return data_dict

    def filterDictForDataLakeDataColumns(self, dct):
        """
        Filter the data dictionary to only include DataLake-compatible columns.

        Args:
            dct: Input dictionary with measurement data

        Returns:
            dict: Dictionary containing only the supported DataLake columns
        """
        ret = {"timestamp" : None, "ORP" : None, "pH" : None, "RTD" : None, "EC" : None, "LIDAR" : None}
        for k in ret.keys():
            try:
                ret[k] = dct[k]
            except:
                pass
        return ret

    def fetchImageBytes(self):
        """
        Fetch the latest image bytes from the camera.

        Returns:
            bytes: The latest image data in TIFF format, or empty bytes if unavailable
        """
        _, img_bytes = self.camInstance.getLatestImage(image_format= "TIFF")
        if img_bytes is None:
            img_bytes = b""
        return img_bytes

    def reconnectStreamToMqttBroker(self, broker="10.20.30.40", port = 1212, topic_sub="Server/Sub", topic_pub="topic", username="PASS", password="PASS"):
        """
        Reconnect to MQTT broker with new configuration.

        If the service is running, sends a LOAD message to the subprocess.
        Otherwise, updates the configuration for next service start.

        Args:
            broker: MQTT broker address
            port: MQTT broker port
            topic_sub: Subscription topic
            topic_pub: Publication topic
            username: Authentication username
            password: Authentication password
        """
        if self.isRunning():
            self.configuration["broker"] = broker
            self.configuration["port"] = port
            self.configuration["topic_sub"] = topic_sub
            self.configuration["topic_pub"] = topic_pub
            self.configuration["username"] = username
            self.configuration["password"] = password
            # Reconnect would need to stop and restart thread
        else:
            self.configuration["broker"] = broker
            self.configuration["port"] = port
            self.configuration["topic_sub"] = topic_sub
            self.configuration["topic_pub"] = topic_pub
            self.configuration["username"] = username
            self.configuration["password"] = password

    def finishProcessesAndQueues(self):
        """Stop the MQTT forwarding thread."""
        if self.isRunning():
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=2)
            self._running = False

    @staticmethod
    def requestQueueClosure(queue, sentinel_message):
        """Close a queue with sentinel message."""
        queue.put(sentinel_message)
        queue.close()
        queue.join_thread()

    def startDataForwarderService(self):
        """Start the MQTT forwarding service in a background thread."""
        self._insights_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._mqttLoop,
            daemon=True
        )
        self._running = True
        self._thread.start()

    def terminateForwarderService(self):
        """Forcefully stop the data forwarding thread."""
        if self.isRunning():
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=2)
            self._running = False

    def isRunning(self):
        """
        Check if the data forwarding service is currently running.

        Returns:
            bool: True if the thread is active, False otherwise
        """
        return self._running and self._thread is not None and self._thread.is_alive()
