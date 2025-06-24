import random
from paho.mqtt import client as mqtt_client
import time

class MqttInterface:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.client is not None:
            self.client.disconnect()
            self.client = None

    def __init__(self, broker='10.20.30.40', port=1212, topic_sub="TOPIC_SUB", topic_pub="TOPIC_PUB", username="test_pub", password="test_pub"):

        self.broker = broker
        self.port = port
        self.topic_sub = topic_sub
        self.topic_pub = topic_pub
        self.username = username
        self.password = password

        # Generate a Client ID with the publish prefix.
        self.client_id = f'publish-{random.randint(0, 1000)}'

        #Data
        self.start = time.time()
        self.stop = time.time()
        self.timing_list = []
        self.timestamp_list = []

        #Counter
        self.messageCounter = 0

        #Message handle
        self.msg = []

        #Client handle
        self.client = None

    def __del__(self):
        if self.client is not None:
            self.client.disconnect()
            self.client = None

    def waitForMsg(self):
        while self.msg == []:
            time.sleep(1e-4)
        return self.msg.pop(0)

    def connectMqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
                Exception(f"Failed to connect, return code {rc}\n")

        self.client = mqtt_client.Client(self.client_id)
        self.client.on_connect = on_connect
        self.client.username_pw_set(self.username, self.password)
        #client.tls_set(certfile="/home/admin_schmidt/Documents/certificate.crt",
        #    keyfile="/home/admin_schmidt/Documents/private.key",
        #    ca_certs="/home/admin_schmidt/Documents/hifmole-hzdr-de-zertifikatskette.pem",
        #    cert_reqs=ssl.CERT_REQUIRED)
        #client.tls_insecure_set(True)
        self.client.connect(self.broker, self.port)

    def publish(self, msg, local_topic_pub=None):
        if local_topic_pub is None:
            result = self.client.publish(self.topic_pub, msg)
            # result: [0, 1]
            status = result[0]
            if status == 0:
                pass
                #print(f"Send `{msg}` to topic `{self.topic_pub}`")
            else:
                print(f"Failed to send message to topic_pub {self.topic_pub}")
        else:
            result = self.client.publish(local_topic_pub, msg)
            status = result[0]
            if status == 0:
                pass
                #print(f"Send `{msg}` to topic `{local_topic_pub}`")
            else:
                print(f"Failed to send message to topic_pub {local_topic_pub}")

    def subscribe(self):
        def on_message(client, userdata, msg):
            self.stop = time.time()
            self.timing_list.append(self.stop-self.start)
            self.timestamp_list.append((self.stop+self.start)/2)
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            print(f"Time elapsed: {self.timing_list[-1]}")
            self.messageCounter = self.messageCounter + 1
            self.msg.append(msg)

        self.client.subscribe(self.topic_sub)
        self.client.message_callback_add(self.topic_sub, on_message)        

    def subscribeToTimer(self, on_message, timer_topic="Server/Sub"):
        print("Subscribe to timer of spark")
        self.client.subscribe(timer_topic)
        self.client.message_callback_add(timer_topic, on_message)