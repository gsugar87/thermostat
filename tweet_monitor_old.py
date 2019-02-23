#!/usr/bin/env python

'''
Commands:
# ON
# OFF
ALL ON
ALL OFF
TEMP
T
PIC
SLEEP START #
SLEEP END #
SLEEP
SET ## (bottom temp)
RANGE # (top-bottom temp)
ON (thermostat mode on)
OFF (thermostat mode off)
STATUS
'''

import sys
import time
import os
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates
import matplotlib.pyplot
from twython import Twython
import numpy
from subprocess import Popen, PIPE
import twitter_credentials as tc
import iphone_data as iphone
import remote_commands as rc
import temperature_log_reader as tlr
import postgresql_commands as psql
import camera_commands as cc
import traceback


# your twitter consumer and access information goes here
CONSUMER_KEY = tc.CONSUMER_KEY
CONSUMER_SECRET = tc.CONSUMER_SECRET
ACCESS_TOKEN = tc.ACCESS_TOKEN
ACCESS_SECRET = tc.ACCESS_SECRET
# acceptable username
ok_user_name = tc.ok_user_id

# set iphone info
iPhoneIP = iphone.iPhoneIP
iPhoneMAC = iphone.iPhoneMAC
# set the variables for iPhone check
iPhoneStatusOld = 0  # default to 0 (not here)
iPhoneStatusNew = 0  # default to 0 (not here)

# sign on to twitter
twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_SECRET)

# set if we are using an ac or heater
is_heater = 1

# set the sleep_mode variable
sleep_status = False   # False = sleep mode waiting to start, True = sleep mode has started, waiting to end
sleep_mode = True  # we will want to start and stop sleep mode
# set the sleep end and start times
sleep_start = datetime.datetime.now()
sleep_end = datetime.datetime.now()
sleep_start_hour_default = 0
sleep_start_minute_default = 0
sleep_end_hour_default = 7
sleep_end_minute_default = 30

# set the thermostat mode variable (0 off, 1 on)
thermostat_always_off = False
thermostat_mode = 0
thermostat_temp = 71
thermostat_range = 1
# active_heaters (all, 1, 2, 3, 4)
active_heaters = [True, False, False, False, False]
# activate_heaters (-1 = off, 0 = no action, 1 = on)
activate_heaters = 0

# set the delta times for each process (in sec)
# TweetCheck: check twitter
# IPhoneCheck: check if iphone is connected
# ThermTweetCheck: send a dm tweet if thermostat sends a signal
# CameraCheck: check the camera image
delta_tweet_check = 60
delta_i_phone_check = 120
delta_therm_tweet_check = 600
delta_camera_check = 60
delta_psql_check = 5
delta_activate_heaters = 0
tweet_check_time = 0
iphone_check_time = 0
therm_tweet_check_time = 0
camera_check_time = 0
psql_check_time = 0
activate_heaters_check_time = 0
current_time = time.time()

commands = {'1 ON': rc.on1,
            '1 OFF': rc.off1,
            '2 ON': rc.on2,
            '2 OFF': rc.off2,
            '3 ON': rc.on3,
            '3 OFF': rc.off3,
            '4 ON': rc.on4,
            '4 OFF': rc.off4,
            'ALL ON': rc.onAll,
            'ALL OFF': rc.offAll,
            'TEMP': tlr.temp,
            'T': tlr.temp_log,
            'PIC': tlr.take_image}


def make_midnight_plot(do_plot):

    if do_plot:
        if current_datetime.hour == 0:
            # put the last 24 hours on twitter
            tlr.temp_plot(twitter, 24)
            # make sure we do not repeat the midnight plot
            do_plot = False
    elif current_datetime.hour > 0:
        # make sure we will do a midnight plot when the time is correct
        do_plot = True
    return do_plot


def run():
    do_midnight_plot = True
    while True:
        # get the current time
        current_time = time.time()
        # get the current datetime
        current_datetime = datetime.datetime.now()

        # see if we want to post the date history
        do_midnight_plot = make_midnight_plot(do_midnight_plot)

        # see if we should check the postgresql database
        if psql_check_time < current_time:
            # update the psql check time
            psql_check_time = current_time + delta_psql_check
            # try to read the psql database
            try:
                psql_result = psql.send_receive_sql("SELECT min FROM therm;")
                thermostat_temp = float(psql_result[0][0])
                psql_result = psql.send_receive_sql("SELECT range FROM therm;")
                thermostat_range = float(psql_result[0][0])
                psql_result = psql.send_receive_sql("SELECT sleep FROM status")
                sleep_mode = psql_result[0][0]
                # see if we should change the sleep status
                if sleep_mode:
                    psql_result = psql.send_receive_sql("SELECT endHour FROM sleep")
                    sleep_end.hour = int(psql_result[0][0])
                    sleep_end.minute = int(psql_result[0][0] - sleep_end.hour)
                    psql_result = psql.send_receive_sql("SELECT startHour FROM sleep")
                    sleep_start.hour = int(psql_result[0][0])
                    sleep_start.minute = int(psql_result[0][0] - sleep_end.hour)
                    # see if we should start the sleep status
                    if sleep_status and current_datetime.hour == sleep_start.hour and \
                       current_datetime.minute == sleep_start.minute:
                        # GOING TO SLEEP!
                        sleep_status = True
                        psql.send_sql("UPDATE sleep SET active = true;")
                    # see if we should end the sleep status
                    if sleep_status and current_datetime.hour == sleep_end.hour and \
                       current_datetime.minute == sleep_end.minute:
                        # WAKING UP!
                        sleep_status = False
                        psql.send_sql("UPDATE sleep SET active = false;")
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("Postgresql error!")

            # check the temperatures
            try:
                mainDir = '/sys/bus/w1/devices'
                allDeviceDirs = os.listdir(mainDir)
                # find index that has masater directory
                deviceNames = []
                for i in range(len(allDeviceDirs)):
                    if allDeviceDirs[i] == 'w1_bus_master1':
                        masterDirIndex = i
                    else:
                        deviceNames.append(allDeviceDirs[i])
                numDevices = len(deviceNames)
                temps = [[] for i in range(numDevices)]
                for i in range(numDevices):
                    tfile = open(mainDir + '/' + allDeviceDirs[masterDirIndex] + '/' + deviceNames[i] + '/w1_slave')
                    # read the text
                    text = tfile.read()
                    # close the file
                    tfile.close()
                    # split the text with new lines and select the second to last line
                    secondline = text.split("\n")[-2]
                    # split the line into words, referring to the spaces and select the 10th word
                    tempWord = secondline.split(" ")[9]
                    # The first two characaters are t=, so get rid of them
                    temp = float(tempWord[2:])
                    # convert to correct temps
                    tempC = temp / 1000
                    temps[i] = tempC * 9 / 5 + 32
                # end of reading in all the sensor data
                # get the median
                tempF = numpy.median(temps)

                #tempF = tlr.get_temp()
                tempFstr = "%.2f" % tempF
                psql.send_sql("DELETE FROM temp WHERE now > 0 OR now <= 0;")
                psql.send_sql("INSERT INTO temp (now) VALUES (" + tempFstr + ");")
                #psql.sendSQL("UPDATE temp SET now = " + tempFstr + ";")
                # activate heaters if neccessary
                if tempF < thermostat_temp and not thermostat_always_off:
                    if is_heater > 0:
                        # turn on heat
                        rc.onAll(twitter, sendMessage=False)
                    else:
                        # turn off ac
                        rc.offAll(twitter, sendMessage=False)
                if tempF > thermostat_temp + thermostat_range and not thermostat_always_off:
                    if is_heater > 0:
                        # turn off heat
                        rc.offAll(twitter, sendMessage=False)
                    else:
                        # turn on ac
                        rc.onAll(twitter, sendMessage=False)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("Error reading temperatures")

        # see if we should check twitter
        if tweet_check_time < current_time:
            # update the tweet check time
            tweet_check_time = current_time + delta_tweet_check
            # read direct messages
            # see if we are in thermostat mode
            if thermostat_mode != 0:
                # see what the temperature is
                # read the temperature of the sensors and tweet it
                try:
                    mainDir = '/sys/bus/w1/devices'
                    allDeviceDirs = os.listdir(mainDir)
                    #deviceNames = allDeviceDirs[0:-1]
                    deviceNames = []
                    masterDir = ''
                    for deviceName in allDeviceDirs:
                        if 'master' not in deviceName:
                            deviceNames.append(deviceName)
                        else:
                            masterDir = deviceName

                    numDevices = len(deviceNames)
                    temps = [[] for i in range(numDevices)]
                    for i in range(numDevices):
                        tfile = open(mainDir + '/' + masterDir + '/' + deviceNames[i] + '/w1_slave')
                        # read the text
                        text = tfile.read()
                        # close the file
                        tfile.close()
                        # split the text with new lines and select the second to last line
                        secondline = text.split("\n")[-2]
                        # split the line into words, referring to the spaces and select the 10th word
                        tempWord = secondline.split(" ")[9]
                        # The first two characaters are t=, so get rid of them
                        temp = float(tempWord[2:])
                        # convert to correct temps
                        tempC = temp / 1000
                        temps[i] = tempC * 9 / 5 + 32
                    # end of reading in all the sensor data
                    # get the median
                    tempF = numpy.median(temps)

                    tempFstr = "%.2f" % tempF
                    psql.send_sql("DELETE FROM temp WHERE now > 0 OR now <= 0;")
                    psql.send_sql("INSERT INTO temp (now) VALUES (" + tempFstr + ");")
                    #psql.sendSQL("UPDATE temp SET now = " + tempFstr + ";")

                    # compare to thermostat threshold and send message if needed
                    if therm_tweet_check_time < current_time:
                        sendTweetUpdate = True
                        therm_tweet_check_time = current_time + delta_therm_tweet_check
                    else:
                        sendTweetUpdate = False

                    if tempF < thermostat_temp and not thermostat_always_off:
                        if is_heater > 0:
                            # turn on heat
                            rc.onAll(twitter, sendMessage=sendTweetUpdate)
                        else:
                            # turn off ac
                            rc.offAll(twitter, sendMessage=sendTweetUpdate)
                    if tempF > thermostat_temp + thermostat_range and not thermostat_always_off:
                        if is_heater > 0:
                            # turn off heat
                            rc.offAll(twitter, sendMessage=sendTweetUpdate)
                        else:
                            # turn on ac
                            rc.onAll(twitter, sendMessage=sendTweetUpdate)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    twitter.send_direct_message(text='Error reading temperatures', screen_name=tc.ok_user_id)

            # see if we are in sleep mode
            if sleep_mode != 0:
                now = datetime.datetime.now()
                # see if we are at the sleep hour and minute
                if (not sleep_status) and now.hour == sleep_start.hour and now.minute == sleep_start.minute:
                    # we are at the sleep start time, so turn off the heat
                    rc.offAll(twitter)
                    # keep sleep mode on
                    sleep_status = True
                    psql.send_sql("UPDATE sleep SET active = true;")
                    print('sleep mode start activated')
                if sleep_status and now.hour == sleep_end.hour and now.minute == sleep_end.minute:
                    # we are at the sleep end time, so turn on the heat
                    rc.onAll(twitter)
                    # turn off sleep mode
                    sleep_status = 0
                    psql.send_sql("UPDATE sleep SET active = false;")
                    twitter.send_direct_message(text='Sleep Mode Off', screen_name=tc.ok_user_id)
                    print('sleep mode end activated')

            # read direct messages
            try:
                direct_messages = twitter.get_direct_messages()
                direct_messages = direct_messages['events']
            except:
                print('twitter GET rate limit error')
                direct_messages = []

            num_messages = len(direct_messages)
            # see if there is a new direct message
            # print('found ' + str(num_messages) + ' messages')
            for i in range(num_messages):
                #sender_name = direct_messages[num_messages - i - 1]['sender_screen_name']
                sender_name = direct_messages[num_messages - i -1]['message_create']['sender_id']
                message_id = direct_messages[num_messages - i - 1]['id']
                if sender_name == ok_user_name:
                    #message = direct_messages[num_messages - i - 1]['text'].upper()
                    message = direct_messages[num_messages - i - 1]['message_create']['message_data']['text'].upper()
                    # see what command was sent
                    print(message)
                    try:
                        commands[message](twitter)
                    except:
                        try:
                            message_split = message.split(' ')
                            if message[0] == 'T':
                                try:
                                    hoursToPlot = int(message[1:])
                                    tlr.temp_plot(twitter, hoursToPlot)
                                except Exception as err:
                                    print('could not plot the temp')
                                    traceback.print_tb(err.__traceback__)
                            elif message_split[0] == 'SLEEP':
                                # turn on sleep mode
                                sleep_mode = 1
                                try:
                                    if message_split[1] == 'START':
                                        sleep_start = datetime.datetime.now()
                                        if sleep_start.hour > int(message_split[2]):
                                            sleep_start += datetime.timedelta(days=1)
                                        sleep_start = sleep_start.replace(hour=int(message_split[2]))
                                        sleep_start = sleep_start.replace(minute=int(message_split[3]))
                                        print('start sleep mode tweet received')
                                        twitter.send_direct_message(
                                            text='Sleep mode will start on ' + sleep_start.strftime('%H:%M'),
                                            screen_name=tc.ok_user_id)

                                    elif message_split[1] == 'END':
                                        sleep_end = datetime.datetime.now()
                                        if sleep_end.hour > int(message_split[2]):
                                            sleep_end += datetime.timedelta(days=1)
                                        sleep_end = sleep_end.replace(hour=int(message_split[2]))
                                        sleep_end = sleep_end.replace(minute=int(message_split[3]))
                                        print('end sleep mode tweet received')
                                        twitter.send_direct_message(
                                            text='Sleep mode will end on ' + sleep_end.strftime('%H:%M'),
                                            screen_name=tc.ok_user_id)
                                    else:
                                        # use the default sleep settings
                                        sleep_start = datetime.datetime.now()
                                        if sleep_start.hour > sleep_start_hour_default:
                                            sleep_start += datetime.timedelta(days=1)
                                        sleep_start = sleep_start.replace(hour=sleep_start_hour_default)
                                        sleep_start = sleep_start.replace(minute=sleep_start_minute_default)
                                        sleep_end = datetime.datetime.now()
                                        if sleep_end.hour > sleep_end_hour_default:
                                            sleep_end += datetime.timedelta(days=1)
                                        sleep_end = sleep_end.replace(hour=sleep_end_hour_default)
                                        sleep_end = sleep_end.replace(minute=sleep_end_minute_default)
                                        print('default sleep mode')
                                        twitter.send_direct_message(
                                            text='Default Sleep mode enabled. Sleep mode will start on ' + sleep_start.strftime(
                                                '%H:%M'), screen_name=tc.ok_user_id)
                                        twitter.send_direct_message(
                                            text='Sleep mode will end on ' + sleep_end.strftime('%H:%M'),
                                            screen_name=tc.ok_user_id)

                                except:
                                    print('issues with sleep mode tweet read')
                            elif message_split[0] == 'SET':
                                # set the new thermostat temp
                                thermostat_temp = int(message_split[1])
                                # put the  the psql database
                                try:
                                    psql.send_sql("DELETE FROM therm WHERE min > 0 OR min <= 0;")
                                    psql.send_sql("INSERT INTO therm VALUES (" + str(thermostat_temp) + ", " +
                                                  str(thermostat_range) + ");")
                                    #psql.sendSQL("UPDATE therm SET now = " + tempFstr + ";")
                                except Exception as e:
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                    print(exc_type, fname, exc_tb.tb_lineno)
                                    print("Postgresql error!")
                                twitter.send_direct_message(text='Thermostat temp set to ' + message_split[1],
                                                            screen_name=tc.ok_user_id)
                            elif message_split[0] == 'RANGE':
                                # set the new thermostat range
                                thermostat_range = int(message_split[1])
                                twitter.send_direct_message(
                                    text='Thermostat max temp set to ' + str(int(message_split[1]) + thermostat_temp),
                                    screen_name=tc.ok_user_id)
                                try:
                                    psql.send_sql("DELETE FROM therm WHERE min > 0 OR min <= 0;")
                                    psql.send_sql("INSERT INTO therm VALUES (" + str(thermostat_temp) + ", " +
                                                  str(thermostat_range) + ");")
                                except Exception as e:
                                    exc_type, exc_obj, exc_tb = sys.exc_info()
                                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                                    print(exc_type, fname, exc_tb.tb_lineno)
                                    print("Postgresql error!")

                            elif message_split[0] == 'ON':
                                # turn on thermostat mode
                                thermostat_mode = 1
                                psql.send_sql("UPDATE status SET thermostat = true;")
                                twitter.send_direct_message(text='Thermostat mode turned on', screen_name=tc.ok_user_id)
                            elif message_split[0] == 'OFF':
                                # turn off thermostat mode
                                thermostat_mode = 0
                                psql.send_sql("UPDATE status SET thermostat = false;")
                                twitter.send_direct_message(text='Thermostat mode turned off', screen_name=tc.ok_user_id)
                            elif message_split[0] == 'STATUS':
                                # send the status of the thermostat
                                message_to_send = 'Temp: %1.1f, Thermostat Mode: %d,  T Range: %d-%d,  Home: %d' % \
                                                  (tlr.get_temp(), thermostat_mode, thermostat_temp,
                                                   thermostat_temp+thermostat_range, iPhoneStatusOld)
                                twitter.send_direct_message(text=message_to_send, screen_name=tc.ok_user_id)
                            else:
                                print('unknown twitter command!')
                                twitter.send_direct_message(text='Did not understand command', screen_name=tc.ok_user_id)
                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            print(exc_type, fname, exc_tb.tb_lineno)
                            print('twitter sending error')
                try:
                    twitter.destroy_direct_message(id=message_id)
                    print('direct message destroyed')
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print('error deleting direct message!')
            # end of the tweet check

        # see if we should check if the iphone is here
        if i_phone_check_time < current_time and not thermostat_always_off:
            # update the iPhone check time
            i_phone_check_time = current_time + delta_i_phone_check
            # ping the iphone
            try:
                ping_response = Popen(["ping", iPhoneIP, '-c 1'], stdout=PIPE).stdout.read()
                pid = Popen(["arp", "-a", iPhoneIP], stdout=PIPE)
                arp_output = pid.communicate()[0].split()
                # see if iphone is connected
                if iPhoneMAC in arp_output:
                    iPhoneStatusNew = 1
                    if iPhoneStatusNew != iPhoneStatusOld:
                        thermostat_mode = 1
                        psql.send_sql("UPDATE status SET thermostat = true;")
                        twitter.send_direct_message(text='You came home! Thermostat mode turned on',
                                                    screen_name=tc.ok_user_id)
                    iPhoneStatusOld = 1
                else:
                    # iphone is disconnected!
                    iPhoneStatusNew = 0
                    if iPhoneStatusNew != iPhoneStatusOld:
                        # we have a switch (I just left home)
                        # turn off the thermostat mode and all outlets
                        thermostat_mode = 0
                        psql.send_sql("UPDATE status SET thermostat = false;")
                        twitter.send_direct_message(text='You left the house!  Thermostat mode and all outlets turned off.',
                                                    screen_name=tc.ok_user_id)
                        rc.offAll(twitter)
                    iPhoneStatusOld = 0
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print('Error with iphone pinging')

        # see if we should check if the camera sees something
        if camera_check_time < current_time:
            camera_check_time = current_time + delta_camera_check
            # check the camera
            # camera.capture(image_filename)

        # see if we should activate heaters
        if activate_heaters_check_time < current_time and not thermostat_always_off:
            # update the activate heaters checktime
            activate_heaters_check_time = current_time + delta_activate_heaters
            if activate_heaters > 0:
                if active_heaters[0]:
                    rc.onAll(twitter, sendMessage=False)
                if active_heaters[1]:
                    rc.on1(twitter, sendMessage=False)
                if active_heaters[2]:
                    rc.on2(twitter, sendMessage=False)
                if active_heaters[3]:
                    rc.on3(twitter, sendMessage=False)
                if active_heaters[4]:
                    rc.on4(twitter, sendMessage=False)
            elif activate_heaters < 0:
                # turn off heat
                if active_heaters[0]:
                    rc.offAll(twitter, sendMessage=False)
                if active_heaters[1]:
                    rc.off1(twitter, sendMessage=False)
                if active_heaters[2]:
                    rc.off2(twitter, sendMessage=False)
                if active_heaters[3]:
                    rc.off3(twitter, sendMessage=False)
                if active_heaters[4]:
                    rc.off4(twitter, sendMessage=False)
