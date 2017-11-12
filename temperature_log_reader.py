# this file contains the functions used to read the temperature logs and plot the data
import os
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates
import matplotlib.pyplot
import numpy as np
import twitter_credentials as tc
import camera_commands
import email_commands
import postgresql_credentials as psql

def get_temps():
    try:
        mainDir = '/sys/bus/w1/devices'
        allDeviceDirs = os.listdir(mainDir)
        deviceNames = allDeviceDirs[0:-1]
        numDevices = len(deviceNames)
        temps = [[] for i in range(numDevices)]
        for i in range(numDevices):
            tfile = open(mainDir + '/' + allDeviceDirs[-1] + '/' + deviceNames[i] + '/w1_slave')
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
            tempC = temp / 1000
            temps[i] = tempC * 9 / 5 + 32
        # end of reading in all the sensor data
        return temps
    except:
        print("Error in reading temperatures!")
        return [-1]


def get_temp():
    temps = get_temps()
    avg_temp = np.median(temps)
    return avg_temp


def take_image(twitter):
    print('take an image and send it to an email address')
    try:
        # take the picture, send an email, and report it via twitter DM
        camera_commands.save_image('capture.jpg')
        email_commands.send_image('capture.jpg')
        twitter.send_direct_message(text='Image taken!', screen_name=tc.ok_user_name)
    except:
        twitter.send_direct_message(text='Error reading temperatures', screen_name=tc.ok_user_name)


def temp(twitter):
    print('read the current temperture off the sensors')
    # read the temperature of the sensors and tweet it
    try:
        mainDir = '/sys/bus/w1/devices'
        allDeviceDirs = os.listdir(mainDir)
        deviceNames = allDeviceDirs[0:-1]
        numDevices = len(deviceNames)
        temps = [[] for i in range(numDevices)]
        for i in range(numDevices):
            tfile = open(mainDir + '/' + allDeviceDirs[-1] + '/' + deviceNames[i] + '/w1_slave')
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
            tempC = temp / 1000
            temps[i] = tempC * 9 / 5 + 32
        # end of reading in all the sensor data
        # now output to twitter
        strToPrint = str(temps[0])
        for i in range(numDevices - 1):
            strToPrint += ", " + str(temps[i + 1])
        twitter.send_direct_message(text=strToPrint, screen_name=tc.ok_user_name)
    except:
        twitter.send_direct_message(text='Error reading temperatures', screen_name=tc.ok_user_name)


def tempLog(twitter):
    print('read the temperture log')
    try:
        # TODO have this read from the postgres database!
        [psqlResult] = psql.getRecentTemp()
        last_line = psqlResult[1].strftime("%a, %b, %d, %Y, %I:%M:%S")+" %1.2f" % (psqlResult[0])
        """
        # read the last line of the most recent temperature log
        # first we need to find the most recently edited file in the directory
        search_dir = '/home/pi/bbt'
        max_mtime = 0
        for dirname, subdirs, files in os.walk(search_dir):
            for fname in files:
                full_path = os.path.join(dirname, fname)
                mtime = os.stat(full_path).st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
                    max_full_filename = full_path
        # now we have the most recently edited file, let's get the last line of it
        tfile = open(max_full_filename)
        # read the text
        text = tfile.read()
        # close the file
        tfile.close()
        # split the text with new lines and select the second to last line
        last_line = text.split("\n")[-2]
        """
        twitter.send_direct_message(text=last_line, screen_name=tc.ok_user_name)
    except:
        twitter.send_direct_message(text='Problem with reading the temperature log!', screen_name='GlennSugar')


def tempPlot(twitter, hrs_to_plot):
    startTime = datetime.datetime.now()-datetime.timedelta(hours=hrs_to_plot)

    [datesToPlot, tempsToPlot] = psql.getTempHistory(startTime)
    """ 
    secs_to_plot = hrs_to_plot * 60 * 60
    # This function will send a plot of the past x hrs of temperature data
    try:
        # create a month dictionary for datetime conversion
        month_dict = {' Jan': 1, ' Feb': 2, ' Mar': 3, ' Apr': 4, ' May': 5, ' Jun': 6, ' Jul': 7, ' Aug': 8, ' Sep': 9,
                     ' Oct': 10, ' Nov': 11, ' Dec': 12}
        # read the last line of the most recent temperature log
        # first we need to find the most recently edited file in the directory
        search_dir = '/home/pi/bbt'
        max_mtime = 0
        for dirname, subdirs, files in os.walk(search_dir):
            for fname in files:
                full_path = os.path.join(dirname, fname)
                mtime = os.stat(full_path).st_mtime
                if mtime > max_mtime:
                    max_mtime = mtime
                    max_full_filename = full_path
        # now we hhave the most recently edited file, let's get the last line of it
        tfile = open(max_full_filename)
        # read the text
        text = tfile.read()
        # close the file
        tfile.close()
        # split up the text by line while ignoring the last blank line
        text = text.split("\n")[0:-1]
        # get the datetimes of the log
        allDatetimes = [
            datetime.datetime(int(dummy.split(",")[3]), int(month_dict[dummy.split(",")[1]]), int(dummy.split(",")[2]),
                              int((dummy.split(",")[4]).split(":")[0]), int((dummy.split(",")[4]).split(":")[1]),
                              int((dummy.split(",")[4]).split(":")[2])) for dummy in text]
        # see which index we want to start at
        secBeforeNow = [(allDatetimes[-1] - allDatetimes[i]).total_seconds() for i in range(len(allDatetimes))]
        startIndex = min(range(len(secBeforeNow)), key=lambda i: abs(secBeforeNow[i] - secs_to_plot))
        # get the temperatures
        tempsToPlot = [float(dummy.split(",")[5]) for dummy in text[startIndex:]]
        datesToPlot = allDatetimes[startIndex:]
        """       
    try:
        # plot the data
        fig, ax = matplotlib.pyplot.subplots()
        ax.plot_date(datesToPlot, tempsToPlot, '-', tz=None, xdate=True, ydate=False)
        # matplotlib.pyplot.plot_date(datesToPlot,tempsToPlot, '-',  tz=None, xdate=True, ydate=False)
        matplotlib.pyplot.xlabel('Time')
        matplotlib.pyplot.ylabel('Temp (F)')
        matplotlib.pyplot.title(datesToPlot[0].strftime('Temperatures on %b %d, %Y'))
        fig.autofmt_xdate()
        # ax.fmt_xdata = matplotlib.dates.DateFormatter('g:ia')
        # save the plot
        matplotlib.pyplot.savefig('/home/pi/temperture_plots/temp_history.png')
        photo = open('/home/pi/temperture_plots/temp_history.png', 'rb')
        twitter.update_status_with_media(media=photo, status='Temperature Update')
        # twitter.upload_media(media=photo, status='Temperture Update')
        # send the plot to twitter
        twitter.send_direct_message(media=photo, text='Plot Posted!', screen_name=tc.ok_user_name)
    except:
        print('problem with plotting function')
        twitter.send_direct_message(text='Problem with plotting!!', screen_name=tc.ok_user_name)
