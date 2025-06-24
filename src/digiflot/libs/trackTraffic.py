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
    else: 
        result = int(result)
    return result

#determine available networks
nets = ["eth0", "wlan0", "lo"] #, "ens18"]
nets_available = []
for net in nets:
    rx_bytes = do(f"cat /sys/class/net/{net}/statistics/rx_bytes")
    if rx_bytes is not None:
        nets_available.append(net)

#init dct_previous and ts_previous for determing the rate
ts_previous = time.time()
dct_previous = {}
for net in nets_available:
    rx_bytes = do(f"cat /sys/class/net/{net}/statistics/rx_bytes")
    tx_bytes = do(f"cat /sys/class/net/{net}/statistics/tx_bytes")
    dct_previous[net] = { "rx bytes" : rx_bytes, "tx bytes" : tx_bytes }

def getRxAndTxByteRate():
    global nets_available
    global ts_previous
    global dct_previous
    
    ts = time.time()
    #calc time interval
    dt = ts - ts_previous
    
    dct_rate = {}
    for net in nets_available:
        rx_bytes = do(f"cat /sys/class/net/{net}/statistics/rx_bytes")
        tx_bytes = do(f"cat /sys/class/net/{net}/statistics/tx_bytes")
        dct_rate[net] = { "rx bps" : round(( rx_bytes - dct_previous[net]["rx bytes"] ) / dt), "tx bps" : round(( tx_bytes - dct_previous[net]["tx bytes"] ) // dt) }
        #update previous dct
        dct_previous[net] = { "rx bytes" : rx_bytes, "tx bytes" : tx_bytes }
    #update previous timestamp
    ts_previous = ts
    
    return dct_rate

def trackTraffic(N=-1):
    period = 1 #seconds
    start = time.time()
    if N <= 0:
        counter = 0        
        while True:
            while time.time() - start < period*counter:
                time.sleep(1e-2)
            dct = getRxAndTxByteRate()
            print(dct)
            counter = counter + 1
    else:
        padding = 120 # 1 extra Minute
        #padding = period
        for i in range (N//period + 1 + padding//period):
            while time.time() - start < period*i:
                time.sleep(1e-2)
            dct = getRxAndTxByteRate()
            print(dct)

if __name__ == "__main__":
    trackTraffic(1)
