# This file contains the postgresql database interaction functions
from dateutil import parser
import re
import psycopg2
import time
import pg_credentials
import os
import sys
import pytz

dbname = pg_credentials.dbname
user = pg_credentials.user
host = pg_credentials.host
password = pg_credentials.password
dbname2 = pg_credentials.dbname2
user2 = pg_credentials.user2
host2 = pg_credentials.host2
password2 = pg_credentials.password2



def sendReceiveSQL(command):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        cur.execute(command)
        psqlResult = cur.fetchall()
        conn.commit()
        conn.close()
        return psqlResult
    except:
        print("PSQL send-receive error!")


def sendSQL(command):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        conn.close()
    except:
        print("PSQL send error!")
    return

def writeNewTemp2(temperature, timeStamp):
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command = "INSERT INTO thermostat_temperaturereading (temperature, time) VALUES (%f, '%s')" % (temperature, timeStamp)
        cur.execute(command)
        conn.commit()
        conn.close()
    except:
        print("PSQL send error!  Couldn't log temperature")
    return


def writeNewTemp(temperature, timeStamp):
    writeNewTemp2(temperature, timeStamp.replace(tzinfo=pytz.timezone('PST8PDT')))
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        command = "INSERT INTO temperature_history (temp, datetime) VALUES (%f, '%s')" % (temperature, timeStamp)
        cur.execute(command)
        conn.commit()
        conn.close()
    except:
        print("PSQL send error!  Couldn't log temperature")
    return

def getTempHistory(time1):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        commandTimeStamp = "SELECT datetime FROM temperature_history WHERE datetime BETWEEN '" + time1.isoformat() + "' AND now();"
        cur.execute(commandTimeStamp)
        timeStamps = []
        for stamp, in cur:
            timeStamps.append(stamp)
        commandTemps = "SELECT temp FROM temperature_history WHERE datetime BETWEEN '" + time1.isoformat() + "' AND now();"
        cur.execute(commandTemps)
        temps = []
        for temp, in cur:
            temps.append(temp)
        conn.close()
#        if len(temps) > len(timeStamps):
#            temps = temps[0:(len(timeStamps)-1)]
        return [timeStamps, temps]
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Postgresql error!")
        print("PSQL send-receive error!")

def getRecentTemp():
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        commandTemp = "SELECT (temp, datetime) FROM temperature_history WHERE datetime = (select max(datetime) from temperature_history);"
        cur.execute(commandTemp)
        response = cur.fetchall()
        conn.close()
        response = response[0][0].split(',')
        # Get rid of any weird characters for the temperature
        response[0] = re.findall("\d+\.\d+", response[0])[0]
        # convert string to datetime
        response[1] = parser.parse(response[1][1:-2])
        return response
    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("PSQL send-receive error!")
