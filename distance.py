#!/usr/bin/env python
import time
import sys
import os
import signal
import requests

import VL53L1X

DEFAULT_DISTANCE_MIN=50
DEFAULT_DISTANCE_MAX=150
DEFAULT_TIME_AFTER_HIT=5.0
DEFAULT_TIME_AFTER_NO_HIT=0.3
DEFAULT_TIMING_BUDGET=2
DEFAULT_DISTANCE_DEBUG=False

url = 'http://10.18.8.31:8080/api/notification/SCREEN_TOGGLE'
#my_headers = {'Authorization': 'XXXXX',}
my_headers = None
payload = {'forced':True}



tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)


#function that decides if a system variable or the default value should be used
#the type of the return value will be the same as of the default value
#if the default value is boolean a value of "1" of the system variable will lead to a true value, all others to false
def sys_var_to_var(sys_var, default_value):
    print("CurSysVar: %s" % sys_var)
    if type(default_value) is int:
        print("it is a int")
        return int(os.getenv(sys_var, default_value))
    elif type(default_value) is float:
        print("it is a float")
        return float(os.getenv(sys_var, default_value))
    elif type(default_value) is bool:
        print("it is a bool")
        if default_value:
            print("default is true setting 1")
            cur_value = 1
        else:
            print("default is false setting 0")
            cur_value = 0
        print("Sys_var has value: %s" %os.getenv(sys_var))
        if int(os.getenv(sys_var, cur_value)) == 1:
            print("Total result is 1")
            return True
        else:
            print("Total result is 0")
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
time_after_hit = sys_var_to_var("DISTANCE_TIME_AFTER_HIT", DEFAULT_TIME_AFTER_HIT)
time_after_no_hit = sys_var_to_var("DISTANCE_TIME_AFTER_NO_HIT", DEFAULT_TIME_AFTER_NO_HIT)
ranging_value = sys_var_to_var("DISTANCE_TIMING_BUDGET", DEFAULT_TIMING_BUDGET)
debug = sys_var_to_var("DISTANCE_DEBUG", DEFAULT_DISTANCE_DEBUG)

print ("Configuration: ")
print ("  DISTANCE_MIN: %d" % distance_min)
print ("  DISTANCE_MAX: %d" % distance_max)
print ("  DISTANCE_TIME_AFTER_HIT: %f" % time_after_hit)
print ("  DISTANCE_TIME_ARTER_NO_HIT: %f" % time_after_no_hit)
print ("  DISTANCE_RANGING_VALUE: %d" % ranging_value)
print ("  DISTANCE_DEBUG: %s" % debug)

tof.open()

#workaround to make sure the new raning value is accepted
tof.start_ranging(0)
tof.stop_ranging()

tof.start_ranging(ranging_value)  # Start ranging
                      # 0 = Unchanged
                      # 1 = Short Range
                      # 2 = Medium Range
                      # 3 = Long Range

running = True

#without flushed the value will not be written to the journal of the service
sys.stdout.flush()

# Attach a signal handler to catch SIGINT (Ctrl+C) and exit gracefully
signal.signal(signal.SIGINT, exit_handler)

distance_in_mm = -1
while running:
    #make sure that at least two values (the last and current one) are within reach of a hit
    #this is to filter wrong values of the sensor which can occour randomly
    old_distance = distance_in_mm
    distance_in_mm = tof.get_distance()
    
    if (distance_in_mm >= distance_min) and (distance_in_mm <= distance_max) and (old_distance >= distance_min) and (old_distance <= distance_max):
        print ("Hit: {}mm".format(distance_in_mm))
        sys.stdout.flush()
        
        r = requests.get(url, headers=my_headers, json=payload)
        
        #tof.stop_ranging()
        time.sleep(time_after_hit)
        #tof.start_ranging(ranging_value)
    else:
        if debug:
            print ("Distance: {}mm".format(distance_in_mm))
            sys.stdout.flush()
        time.sleep(time_after_no_hit)
