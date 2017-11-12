# This file contains the postgresql database interaction functions
import psycopg2
import time
import pg_credentials

dbname = pg_credentials.dbname
user = pg_credentials.user
host = pg_credentials.host
password = pg_credentials.password

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

def writeNewTemp(temperature, timeStamp):
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
        commandTimeStamp = "SELECT datetime FROM temperature_history WHERE datetime BETWEEN '" + time1 + "' AND now();"
        cur.execute(commandTimeStamp)
        timeStamps = []
        for stamp, in cur:
            timeStamps.append(stamp)
        commandTemps = "SELECT temp FROM temperature_history WHERE datetime BETWEEN '" + time1 + "' AND now();"
        cur.execute(commandTemps)
        temps = []
        for temp, in cur:
            temps.append(temp)
        conn.close()
        return [timeStamps, temps]
    except:
        print("PSQL send-receive error!")
