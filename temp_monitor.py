# Author: Glenn Sugar
# This script will monitor the temperature sensors attached to the raspberry pi
# It uses modprobe to mount the sensors to /sys/bus/w1/devices/

import os
import time
import numpy
import postgresql_commands as psql
import datetime
import settings

# MAIN SETTINGS
main_dir = '/sys/bus/w1/devices'
# set the time formatting we want for time printing
timeFormat = "%a, %b, %d, %Y, %H:%M:%S"
# set the time in seconds between logs (approximate)
log_rate_sec = 20
# it takes about 3 seconds to read the sensors
log_rate_sec -= 3


def initialize_sensors():
    # get the addresses of the temperature sensors
    all_device_dirs = os.listdir(main_dir)
    while len(all_device_dirs) < 2:
        time.sleep(15)
        os.system('sudo modprobe w1-gpio')
        os.system('sudo modprobe w1-therm')
        # the devices have not been initialized yet!
        all_device_dirs = os.listdir(main_dir)
        if len(all_device_dirs) < 2:
            print('Cannot find directories, trying to initialize temperature sensors again...')
    return all_device_dirs


def read_sensors(sensor_dirs, temp_lists):
    i = 0
    for sensor_dir in sensor_dirs:
        tfile = open(sensor_dir)
        text = tfile.read()
        # close the file
        tfile.close()
        # split the text with new lines and select the second to last line
        second_line = text.split("\n")[-2]
        # split the line into words, referring to the spaces and select the 10th word
        temp_word = second_line.split(" ")[9]
        # The first two characters are t=, so get rid of them
        temp = float(temp_word[2:])
        # convert to correct temps
        temp_c = temp / 1000
        temp_lists[i].append(temp_c * 9 / 5 + 32)
        i += 1
    return temp_lists


def run():
    # initialize the sensors
    all_device_dirs = initialize_sensors()

    device_names = []
    master_dir = ''
    for deviceName in all_device_dirs:
        if 'master' not in deviceName:
            device_names.append(deviceName)
        else:
            master_dir = deviceName

    num_devices = len(device_names)
    sensor_dirs = []
    for i in range(num_devices):
        sensor_dirs.append(main_dir + '/' + master_dir + '/' + device_names[i] + '/w1_slave')

    # create lists to hold the temp data for averaging
    temp_lists = [[] for i in range(num_devices)]
    temp_avgs = [[] for i in range(num_devices)]

    old_time_sec = time.localtime().tm_sec
    # start the loop
    while True:
        time_str = time.strftime(timeFormat, time.localtime())
        # get the temperature from sensors
        try:
            temp_lists = read_sensors(sensor_dirs, temp_lists)
        except Exception as e:
            # print the time to the log file
            print(e)
            print(time_str + ': Cannot find directories, trying to initialize temperature sensors again...')
            initialize_sensors()

        # see if we should log the temperature
        current_time_sec = time.localtime().tm_sec
        if current_time_sec < old_time_sec:
            current_time_sec += 60
        if current_time_sec-old_time_sec >= log_rate_sec:
            old_time_sec = time.localtime().tm_sec
            # get the average temperatures from all the devices
            for i in range(num_devices):
                temp_avgs[i] = numpy.median(temp_lists[i])
            # clear the temp lists to store new values to get the avg
            temp_lists = [[] for i in range(num_devices)]
            # WRITE TO POSTGRES DATABASE
            psql.write_new_temp(numpy.median(temp_avgs), datetime.datetime.fromtimestamp(time.mktime(time.localtime())))
            time.sleep(2)


if __name__ == "__main__":
    run()
