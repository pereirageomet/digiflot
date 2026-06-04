#!/usr/bin/python
"""Module for Atlas Scientific I2C device communication.

This module provides functions for discovering, listing, and communicating
with Atlas Scientific I2C modules (pH, ORP, EC, RTD sensors) via the I2C bus.
"""

import io
import sys
import fcntl
import time
import copy
import string
from AtlasI2C import (
	 AtlasI2C
)

def print_devices(device_list, device):
    """Print a list of detected devices, highlighting the active device.

    :param device_list: List of detected AtlasI2C devices
    :param device: Currently active device to highlight
    """
    for i in device_list:
        if(i == device):
            print("--> " + i.get_device_info())
        else:
            print(" - " + i.get_device_info())
    #print("")
    
def get_devices():
    """Discover and initialize all Atlas Scientific I2C devices.

    :return: List of initialized AtlasI2C device objects
    """
    device = AtlasI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []
    
    for i in device_address_list:
        device.set_i2c_address(i)
        response = device.query("I")
        try:
            moduletype = response.split(",")[1] 
            response = device.query("name,?").split(",")[1]
        except IndexError:
            print(">> WARNING: device at I2C address " + str(i) + " has not been identified as an EZO device, and will not be queried") 
            continue
        device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
    return device_list   
    
def print_help_text():
    """Print the help text with available commands and usage instructions."""
    print('''
>> Atlas Scientific I2C sample code
>> Any commands entered are passed to the default target device via I2C except:
  - Help
      brings up this menu
  - List 
      lists the available I2C circuits.
      the --> indicates the target device that will receive individual commands
  - xxx:[command]
      sends the command to the device at I2C address xxx 
      and sets future communications to that address
      Ex: "102:status" will send the command status to address 102
  - all:[command]
      sends the command to all devices
  - Poll[,x.xx]
      command continuously polls all devices
      the optional argument [,x.xx] lets you set a polling time
      where x.xx is greater than the minimum %0.2f second timeout.
      by default it will poll every %0.2f seconds
>> Pressing ctrl-c will stop the polling
    ''' % (AtlasI2C.LONG_TIMEOUT, AtlasI2C.LONG_TIMEOUT))
   
def main():
    """Main entry point for interactive I2C device testing."""
    
    print_help_text()
    
    device_list = get_devices()
        
    device = device_list[0]
    
    print_devices(device_list, device)
    
    real_raw_input = vars(__builtins__).get('raw_input', input)
    
    while True:
    
        user_cmd = real_raw_input(">> Enter command: ")
