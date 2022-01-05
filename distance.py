#!/usr/bin/env python
import time
import sys
import os
import signal
import requests

import VL53L1X

DEFAULT_DISTANCE_MIN=50
DEFAULT_DISTANCE_MAX=150
DEFAULT_TIME_AFTER_HIT=2.0
DEFAULT_TIME_AFTER_NO_HIT=0.1

url = 'http://10.18.8.31:8080/api/notification/SCREEN_TOGGLE'
#my_headers = {'Authorization': 'XXXXX',}
my_headers = None
payload = {'forced':True}



tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
tof.open()

tof.start_ranging(1)  # Start ranging
                      # 0 = Unchanged
                      # 1 = Short Range
                      # 2 = Medium Range
                      # 3 = Long Range

running = True

#function that decides if a system variable or the default value should be used
#the type of the return value will be the same as of the default value
#if the default value is boolean a value of "1" of the system variable will lead to a true value, all others to false
def sys_var_to_var(sys_var, default_value):
    if type(default_value) is int:
        return int(os.getenv(sys_var, default_value))
    elif type(default_value) is float:
        return float(os.getenv(sys_var, default_value))
    elif type(default_value) is bool:
        if default_value:
            cur_value = 1
        else:
            cur_value = 0
        if os.getenv(sys_var, cur_value) == 1:
            return True
        else:
            return False
    else:
        return os.getenv(sys_var, default_value)

def exit_handler(signal, frame):
    global running
    running = False
    tof.stop_ranging()
    print()
    sys.exit(0)
    

distance_min = sys_var_to_var("DISTANCE_MIN", DEFAULT_DISTANCE_MIN)
distance_max = sys_var_to_var("DISTANCE_MAX", DEFAULT_DISTANCE_MAX)
time_after_hit = sys_var_to_var("TIME_AFTER_HIT", DEFAULT_TIME_AFTER_HIT)
time_after_no_hit = sys_var_to_var("TIME_AFTER_NO_HIT", DEFAULT_TIME_AFTER_NO_HIT)


# Attach a signal handler to catch SIGINT (Ctrl+C) and exit gracefully
signal.signal(signal.SIGINT, exit_handler)

while running:
    distance_in_mm = tof.get_distance()
    
    if (distance_in_mm >= distance_min) and (distance_in_mm <= distance_max):
        print ("Hit: {}mm".format(distance_in_mm))
        
        r = requests.get(url, headers=my_headers, json=payload)
        
        
        time.sleep(time_after_hit)
    else:
        time.sleep(time_after_no_hit)
