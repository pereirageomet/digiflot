import time
import subprocess
import platform

def do(command):
    if platform.system() != "Linux":
        return None    
    try:
        result = subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        #print(f"Error executing command: {e}")
        result = None
    return result

def getTemperature():
    result = do("vcgencmd measure_temp")
    if result is not None:
        return {"temperature['C]": result.split("=")[1].split("'")[0]}
    else:
        return {"temperature['C]": "-273.15"}

def trackTraffic(N=-1):
    period = 1 #seconds
    start = time.time()
    if N <= 0:
        counter = 0        
        while True:
            while time.time() - start < period*counter:
                time.sleep(1e-2)
            dct = getTemperature()
            print(dct)
            counter = counter + 1
    else:
        padding = 120 # 1 extra Minute
        #padding = period
        for i in range (N//period + 1 + padding//period):
            while time.time() - start < period*i:
                time.sleep(1e-2)
            dct = getTemperature()
            print(dct)

if __name__ == "__main__":
    trackTraffic(1)
