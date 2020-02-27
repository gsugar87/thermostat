import os
import time
import numpy
import postgresql_commands as psql
import datetime
import pytz

# make sure the system has actuated the temperature sensors
os.system('sudo modprobe w1-gpio')
os.system('sudo modprobe w1-therm')

# set the time foratting we want for the log
timeFormat = "%a, %b, %d, %Y, %H:%M:%S"

# set the time in seconds between logs (approximate)
logRateSec = 20
# it takes about 3 seconds to read the sensors
logRateSec -= 3

# get the addresses of the temperature sensors
mainDir = '/sys/bus/w1/devices'
allDeviceDirs = os.listdir(mainDir)
while len(allDeviceDirs) < 2:
    time.sleep(15)
    # the devices have not been initialized yet!
    print('Cannot find directories, trying to initialize temperature sensors again...')
    os.system("sudo modprobe w1-gpio")
    os.system("sudo modprobe w1-therm")
    allDeviceDirs = os.listdir(mainDir)

deviceNames = []
masterDir = ''
for deviceName in allDeviceDirs:
    if 'master' not in deviceName:
        deviceNames.append(deviceName)
    else:
        masterDir = deviceName
        
#deviceNames = allDeviceDirs[0:-1]
numDevices = len(deviceNames)
# create lists to hold the temp data for averaging
tempLists = [[] for i in range(numDevices)]
tempAvgs = [[] for i in range(numDevices)]

oldTimeSec = time.localtime().tm_sec
# start the loop
while True:
    try:
        # go through each device
        for i in range(numDevices):
            # print(i)
            tfile = open(mainDir + '/' + masterDir + '/' + deviceNames[i] + '/w1_slave')
            # tfile = open("/sys/bus/w1/devices/28-000006577aff/w1_slave")
            # tfile = open("/sys/bus/w1/devices/w1_bus_master1/28-000006577aff/w1_slave")
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
            tempC = temp/1000
            tempLists[i].append(tempC*9/5 + 32)
        timeToPrint = time.strftime(timeFormat, time.localtime())
    except:
        # print the time to the log file
        print('Cannot find directories, trying to initialize temperature sensors again...')
        os.system("sudo modprobe w1-gpio")
        os.system("sudo modprobe w1-therm")
        print('error reading the sensors!')
        timeToPrint = time.strftime(timeFormat, time.localtime())

    try:
        # see if we should write to the file
        currentTimeSec = time.localtime().tm_sec
        if currentTimeSec < oldTimeSec:
            currentTimeSec += 60
        if currentTimeSec-oldTimeSec >= logRateSec:
            oldTimeSec = time.localtime().tm_sec
            # get the average temperatures from all the devices
            for i in range(numDevices):
                tempAvgs[i] = numpy.median(tempLists[i])
            # clear the temp lists to store new values to get the avg
            tempLists = [[] for i in range(numDevices)]
            # WRITE TO POSTGRES DATABASE
            timestamp = datetime.datetime.fromtimestamp(time.mktime(time.localtime()))
            timestamp = timestamp.replace(tzinfo=pytz.timezone('UTC'))
            psql.writeNewTemp(numpy.median(tempAvgs), timestamp)
            time.sleep(2)
    except Exception as e:
        timeToPrint = time.strftime(timeFormat, time.localtime())
        print(timeToPrint + ': Unable to open log file!')
        print(type(e))
        print(e.args)
        print(e)
