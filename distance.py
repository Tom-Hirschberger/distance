#!/usr/bin/env python
import time
import sys
import os
import signal
import requests

DEFAULT_DISTANCE_HIT_MIN=50
DEFAULT_DISTANCE_HIT_MAX=150
DEFAULT_DISTANCE_PRESENCE_MIN=350
DEFAULT_DISTANCE_PRESENCE_MAX=1500
DEFAULT_DISTANCE_PRESENCE_SLEEP=30.0
DEFAULT_TIME_AFTER_HIT=5.0
DEFAULT_TIME_AFTER_NO_HIT=0.3
DEFAULT_TIMING_BUDGET=2
DEFAULT_DISTANCE_DEBUG=True
DEFAULT_DISTANCE_SENSOR="VL53L1X"

url_toggle = 'http://10.18.8.31:8080/api/notification/SCREEN_TOGGLE'
url_presence = 'http://10.18.8.31:8080/api/userpresence/true'
#my_headers = {'Authorization': 'XXXXX',}
my_headers = None
payload_toggle = {'forced':True}


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
        if int(os.getenv(sys_var, cur_value)) == 1:
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
    

distance_hit_min = sys_var_to_var("DISTANCE_HIT_MIN", DEFAULT_DISTANCE_HIT_MIN)
distance_hit_max = sys_var_to_var("DISTANCE_HIT_MAX", DEFAULT_DISTANCE_HIT_MAX)

distance_presence_min = sys_var_to_var("DISTANCE_PRESENCE_MIN", DEFAULT_DISTANCE_PRESENCE_MIN)
distance_presence_max = sys_var_to_var("DISTANCE_PRESENCE_MAX", DEFAULT_DISTANCE_PRESENCE_MAX)
distance_presence_sleep = sys_var_to_var("DISTANCE_PRESENCE_SLEEP", DEFAULT_DISTANCE_PRESENCE_SLEEP)

time_after_hit = sys_var_to_var("DISTANCE_TIME_AFTER_HIT", DEFAULT_TIME_AFTER_HIT)
time_after_no_hit = sys_var_to_var("DISTANCE_TIME_AFTER_NO_HIT", DEFAULT_TIME_AFTER_NO_HIT)
ranging_value = sys_var_to_var("DISTANCE_TIMING_BUDGET", DEFAULT_TIMING_BUDGET)
debug = sys_var_to_var("DISTANCE_DEBUG", DEFAULT_DISTANCE_DEBUG)
sensor_type = sys_var_to_var("DISTANCE_SENSOR", DEFAULT_DISTANCE_SENSOR)

print ("Configuration: ")
print ("  DISTANCE_HIT_MIN: %d" % distance_hit_min)
print ("  DISTANCE_HIT_MAX: %d" % distance_hit_max)
print ("  DISTANCE_PRESENCE_MIN: %d" % distance_presence_min)
print ("  DISTANCE_PRESENCE_MAX: %d" % distance_presence_max)
print ("  DISTANCE_TIME_AFTER_HIT: %f" % time_after_hit)
print ("  DISTANCE_TIME_ARTER_NO_HIT: %f" % time_after_no_hit)
print ("  DISTANCE_RANGING_VALUE: %d" % ranging_value)
print ("  DISTANCE_DEBUG: %s" % debug)


if "VL53L1X" in sensor_type:
    import VL53L1X
    tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
    tof.open()

    #workaround to make sure the new raning value is accepted
    tof.start_ranging(0)
    tof.stop_ranging()

    tof.start_ranging(ranging_value)  # Start ranging
                        # 0 = Unchanged
                        # 1 = Short Range
                        # 2 = Medium Range
                        # 3 = Long Range
elif "VL53L0X" in sensor_type:
    import VL53L0X
    tof = VL53L0X.VL53L0X(i2c_bus=1,i2c_address=0x29)
    tof.open()
    tof.start_ranging()

running = True

#without flushed the value will not be written to the journal of the service
sys.stdout.flush()

# Attach a signal handler to catch SIGINT (Ctrl+C) and exit gracefully
signal.signal(signal.SIGINT, exit_handler)

distance_in_mm = -1
last_presence_send= -1
while running:
    #make sure that at least two values (the last and current one) are within reach of a hit
    #this is to filter wrong values of the sensor which can occour randomly
    old_distance = distance_in_mm
    distance_in_mm = tof.get_distance()
    
    if (distance_in_mm >= distance_hit_min) and (distance_in_mm <= distance_hit_max) and (old_distance >= distance_hit_min) and (old_distance <= distance_hit_max):
        print ("Hit: {}mm".format(distance_in_mm))
        sys.stdout.flush()
        
        try:
            r = requests.post(url_toggle, json=payload_toggle)
        except:
            pass
        
        if "VL53L1X" in sensor_type:
            tof.stop_ranging()
        
        time.sleep(time_after_hit)
        if "VL53L1X" in sensor_type:
            tof.start_ranging(0)
            tof.stop_ranging()
            tof.start_ranging(ranging_value)
    elif (distance_in_mm >= distance_presence_min) and (distance_in_mm <= distance_presence_max) and ((time.time() - last_presence_send) > distance_presence_sleep):
        try:
            print ("PRESENCE: {}mm".format(distance_in_mm))
            sys.stdout.flush()
            last_presence_send = time.time()
            r = requests.get(url_presence)
        except:
            pass
    else:
        if debug:
            print ("Distance: {}mm".format(distance_in_mm))
            sys.stdout.flush()
        time.sleep(time_after_no_hit)
