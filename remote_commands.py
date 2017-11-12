# This file contains the commands used to control the remote switches

import os
import twitter_credentials as tc
import time

numSignals = 4


def on1(twitter, sendMessage=True):
    # turn on the first outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997391')
    print('turning on outlet 1')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 1 On', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def off1(twitter, sendMessage=True):
    # turn off the first outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997383')
    print('turning off outlet 1')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 1 Off', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def on2(twitter, sendMessage=True):
    # turn on the second outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997387')
    print('turning on outlet 2')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 2 On', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def off2(twitter, sendMessage=True):
    # turn off the second outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997379')
    print('turning off outlet 2')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 2 Off', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def on3(twitter, sendMessage=True):
    # turn on the third outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997389')
    print('turning on outlet 3')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 3 On', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def off3(twitter, sendMessage=True):
    # turn off the third outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997381')
    print('turning off outlet 3')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 3 Off', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def on4(twitter, sendMessage=True):
    # turn on the fourth outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997390')
    print('turning on outlet 4')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 4 On', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def off4(twitter, sendMessage=True):
    # turn off the fourth outlet
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997382')
    print('turning off outlet 4')
    try:
        if sendMessage:
            twitter.send_direct_message(text='Outlet 4 Off', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def onAll(twitter, sendMessage=True):
    # turn on all outlets
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997384')
    print('turning on all outlets')
    try:
        if sendMessage:
            twitter.send_direct_message(text='All Outlets On', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def offAll(twitter, sendMessage=True):
    # turn off all outlets
    for i in range(numSignals):
        os.system('sudo /home/pi/433Utils/RPi_utils/codesend 997380')
    print('turning off all outlets')
    try:
        if sendMessage:
            twitter.send_direct_message(text='All Outlets Off', screen_name=tc.ok_user_name)
    except:
        print('error with twitter')


def onWait(twitter, hrsToWait):
    # This function will turn on all outlets after a certain amount of time (hrsToWait)
    # get the current time
    baselineTime = time.time()
    secsToWait = hrsToWait * 60 * 60
    continueWaiting = 1
    while continueWaiting == 1:
        currentTime = time.time()
        if (currentTime - baselineTime) > secsToWait:
            # turn on all outlets
            rc.onAll(twitter)
            continueWaiting = 0
        try:
            direct_messages = twitter.get_direct_massages()
        except:
            print('rate limit error')
            direct_messages = []
        if len(direct_messages) > 0:
            continueWaiting = 0
        # sleep 60 seconds so that we don't hit the rate limit of twitter
        time.sleep(60)