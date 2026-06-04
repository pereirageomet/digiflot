#!/usr/bin/env python3
"""Minimal test script for the LIDAR sensor.
It performs two checks:
1. Uses the existing Lidar class (module) to initialise the sensor and read a distance.
2. Reads the sensor directly via pyserial without the Lidar wrapper.
"""

import sys
import os
import time
import pathlib

# Add the project src directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.append(PROJECT_ROOT)

# ---------- Test using the Lidar module ----------
try:
    from libs.lidar import Lidar
except Exception as e:
    print(f"Failed to import Lidar module: {e}")
    Lidar = None

def test_module():
    if Lidar is None:
        print("[module] Lidar class not available.")
        return
    # Minimal mock required by connectToLidar
    class AtlasMock:
        def __init__(self):
            self.times_list = {}
            self.modules_list = []
    lidar = Lidar()
    lidar.connectToLidar(AtlasMock())
    distance = lidar.getMeasuredValueFromLIDAR()
    print(f"[module] LIDAR distance: {distance}")

# ---------- Direct sensor access without the wrapper ----------
def test_direct():
    try:
        import serial
    except ImportError:
        print("pyserial not installed – cannot perform direct test.")
        return
    # Find any ttyUSB device (common for USB‑to‑UART adapters)
    tty_paths = list(pathlib.Path("/dev").glob("ttyUSB[0-9]"))
    if not tty_paths:
        print("No /dev/ttyUSB* device found.")
        return
    for dev in tty_paths:
        try:
            ser = serial.Serial(str(dev), 115200, timeout=2)
            time.sleep(0.2)
            if ser.in_waiting > 8:
                raw = ser.read(9)
                if raw[0] == 0x59 and raw[1] == 0x59:
                    distance = raw[2] + (raw[3] << 8)
                    print(f"[direct] LIDAR distance on {dev}: {distance}")
                    ser.close()
                    return
            ser.close()
        except Exception as e:
            print(f"Error accessing {dev}: {e}")
    print("No valid LIDAR data received from any device.")

if __name__ == "__main__":
    test_module()
    test_direct()
