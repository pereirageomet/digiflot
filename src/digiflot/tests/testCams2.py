import threading
import queue
import time
import os
import json
from picamera2 import Picamera2
from libcamera import controls
import cv2

# CONFIG
MQTT_BROKER = ""
MQTT_TOPIC = "camera/metadata"
output_dir  = "./test_output"
os.makedirs(output_dir,exist_ok=True)



# Initializations
with open('MQTT_test.txt','w') as f: f.write('')

cameras = []

write_queue = queue.Queue()
mqtt_queue = queue.Queue()

# WORKERS

def disk_writer():
	while True:
		item = write_queue.get()
		if item is None: break; # skip when there is no data
		filename,img_array = item
		
		img_bgr = cv2.cvtColor(img_array,cv2.COLOR_RGB2BGR)
		cv2.imwrite(filename,img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY),90])
		
		# with open(filename,'wb') as f: f.write(data); # RAW
		write_queue.task_done()

def mqtt_writer():
	#PLACEHOLDER FOR MQTT
	while True:
		item = mqtt_queue.get()
		with open('MQTT_test.txt','a') as f: f.write(json.dumps(item)+'\n')
		mqtt_queue.task_done()
	
threading.Thread(target=disk_writer, daemon = True).start()
threading.Thread(target=mqtt_writer, daemon = True).start()

# Camera initialization

camera_info = Picamera2.global_camera_info()

for i,info in enumerate(camera_info):
	# initialize
	os.makedirs(f"{output_dir}/cam{i}",exist_ok=True) # init dirs
	
	cam = Picamera2(info['Num']) #init cam
	# initialize the first camera as server and let the rest be clients for sync
	mode = controls.rpi.SyncModeEnum.Server if i==0 else controls.rpi.SyncModeEnum.Client
	
	config = cam.create_still_configuration(main={
		"format":'RGB888',
		},
		controls={
				'SyncMode': mode,
				'FrameRate': 30,			
				})
	cam.start(config)
	cameras.append(cam)
	print(f"Camera {info} Started as {mode}")

time.sleep(2)

# Camera capture loop
try:
	for frame_idx in range(10): #10 frames for test
		ts_now = time.time()
		frame_meta = {"frame": frame_idx, "timestamp":ts_now,"data":{}}
		# Get the frames for each cameras
		for i,cam in enumerate(cameras):
			# capture frame data
			
			# img_data = cam.capture_file(None,format='jpg')
			img_data = cam.capture_array()
			meta = cam.capture_metadata()
			#put into the queue
			write_queue.put((f"{output_dir}/cam{i}/{frame_idx}.jpg",img_data))
			frame_meta['data'][f"Cam_{i}"] = {
				"sensor_ts": meta.get('SensorTimestamp','ERROR'),
				"exposure": meta.get('ExposureTime','ERROR'),
			}
			mqtt_queue.put(frame_meta)
		print(f"Captured frame set {frame_idx}")
		time.sleep(0.1)
finally:
	# Close cameras
	for cam in cameras:
		cam.stop()
	# Close queues 	
	write_queue.put(None)
	write_queue.put(None)










