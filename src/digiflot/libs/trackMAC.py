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

def getMACdict():
    nets = ["eth0", "wlan0"]#, "ens18"]
    MAC_dict = {}
    for net in nets:
        MAC_address = do(f"cat /sys/class/net/{net}/address")
        if MAC_address is not None:
            MAC_dict[net] = MAC_address
    return MAC_dict

if __name__ == "__main__":
    print(getMACdict())
