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
import postgresql_commands as psql


def get_temps():
    try:
        main_dir = '/sys/bus/w1/devices'
        all_device_dirs = os.listdir(main_dir)
        device_names = all_device_dirs[0:-1]
        num_devices = len(device_names)
        temps = [[] for i in range(num_devices)]
        for i in range(num_devices):
            tfile = open(main_dir + '/' + all_device_dirs[-1] + '/' + device_names[i] + '/w1_slave')
            # read the text
            text = tfile.read()
            # close the file
            tfile.close()
            # split the text with new lines and select the second to last line
            secondline = text.split("\n")[-2]
            # split the line into words, referring to the spaces and select the 10th word
            temp_word = secondline.split(" ")[9]
            # The first two characaters are t=, so get rid of them
            temp = float(temp_word[2:])
            # convert to correct temps
            temp_c = temp / 1000
            temps[i] = temp_c * 9 / 5 + 32
        # end of reading in all the sensor data
        return temps
    except Exception as e:
        print(e)
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
        twitter.send_direct_message(text='Image taken!', screen_name=tc.ok_user_id)
    except Exception as e:
        print(e)
        twitter.send_direct_message(text='Error reading temperatures', screen_name=tc.ok_user_id)


def temp(twitter):
    print('read the current temperture off the sensors')
    # read the temperature of the sensors and tweet it
    try:
        main_dir = '/sys/bus/w1/devices'
        all_device_dirs = os.listdir(main_dir)
        device_names = all_device_dirs[0:-1]
        num_devices = len(device_names)
        temps = [[] for i in range(num_devices)]
        for i in range(num_devices):
            tfile = open(main_dir + '/' + all_device_dirs[-1] + '/' + device_names[i] + '/w1_slave')
            # read the text
            text = tfile.read()
            # close the file
            tfile.close()
            # split the text with new lines and select the second to last line
            secondline = text.split("\n")[-2]
            # split the line into words, referring to the spaces and select the 10th word
            temp_word = secondline.split(" ")[9]
            # The first two characaters are t=, so get rid of them
            temp = float(temp_word[2:])
            # convert to correct temps
            temp_c = temp / 1000
            temps[i] = temp_c * 9 / 5 + 32
        # end of reading in all the sensor data
        # now output to twitter
        str_to_print = str(temps[0])
        for i in range(num_devices - 1):
            str_to_print += ", " + str(temps[i + 1])
        twitter.send_direct_message(text=str_to_print, screen_name=tc.ok_user_id)
    except Exception as e:
        print(e)
        twitter.send_direct_message(text='Error reading temperatures', screen_name=tc.ok_user_id)


def temp_log(twitter):
    print('read the temperture log')
    try:
        psql_result = psql.get_recent_temp()
        last_line = psql_result[1].strftime("%a, %b, %d, %Y, %I:%M:%S") + "  " + psql_result[0]
        twitter.send_direct_message(text=last_line, screen_name=tc.ok_user_id)
    except Exception as e:
        print(e)
        twitter.send_direct_message(text='Problem with reading the temperature log!', screen_name=tc.ok_user_id)


def temp_plot(twitter, hrs_to_plot):
    start_time = datetime.datetime.now()-datetime.timedelta(hours=hrs_to_plot)
    
    [dates_to_plot, temps_to_plot] = psql.get_temp_history(start_time)
    try:
        # plot the data
        fig, ax = matplotlib.pyplot.subplots()
        ax.plot_date(dates_to_plot, temps_to_plot, '-', tz=None, xdate=True, ydate=False)
        matplotlib.pyplot.xlabel('Time')
        matplotlib.pyplot.ylabel('Temp (F)')
        matplotlib.pyplot.title(dates_to_plot[0].strftime('Temperatures on %b %d, %Y'))
        fig.autofmt_xdate()
        # save the plot
        matplotlib.pyplot.savefig('/home/pi/temperature_plots/temp_history.png')
        photo = open('/home/pi/temperature_plots/temp_history.png', 'rb')
        image_ids = twitter.upload_media(media=photo)
        twitter.update_status(status='Temperature Update', media_ids=image_ids['media_id'])
        # send the plot to twitter
        twitter.send_direct_message(media=photo, text='Plot Posted!', screen_name=tc.ok_user_id)
    except Exception as e:
        print('problem with plotting function')
        print(e)
        #twitter.send_direct_message(text='Problem with plotting!!', screen_name=tc.ok_user_id)
