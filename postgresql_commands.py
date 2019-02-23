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


def send_receive_sql(command):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        cur.execute(command)
        psql_result = cur.fetchall()
        conn.commit()
        conn.close()
        return psql_result
    except Exception as e:
        print(e)
        print("PSQL send-receive error!")


def send_sql(command):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        print("PSQL send error!")
    return


def write_new_temp(temperature, time_stamp):
    if time_stamp.tzinfo is None:
        time_stamp.replace(tzinfo=pytz.timezone('PST8PDT'))
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command = "INSERT INTO thermostat_temperaturereading (temperature, time) VALUES (%f, '%s')" % (temperature, time_stamp)
        cur.execute(command)
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)
        print("PSQL send error!  Couldn't log temperature")
    return


def get_recent_temp():
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command_temp = "SELECT (temperature, time) FROM thermostat_temperaturereading WHERE time = (select max(time) from thermostat_temperaturereading);"
        cur.execute(command_temp)
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


def get_temp_history(time1):
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        command_time_stamp = "SELECT * FROM thermostat_temperaturereading WHERE time BETWEEN '" + time1.isoformat() + "' AND now();"
        cur.execute(command_time_stamp)
        response = cur.fetchall()

        time_stamps = []
        temps = []
        for entry in response:
            time_stamps.append(entry['time'])
            temps.append(entry['temperature'])
        conn.close()
        return [time_stamps, temps]
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Postgresql error!")
        print("PSQL send-receive error!")


def get_recent_temp():
    try:
        conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host +
                                "' password='" + password + "'")
        cur = conn.cursor()
        command_temp = "SELECT (temp, datetime) FROM temperature_history WHERE datetime = (select max(datetime) from temperature_history);"
        cur.execute(command_temp)
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


def get_bool_variable(var_name):
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command = "SELECT value FROM thermostat_boolvariable WHERE name = '%s';" % var_name
        cur.execute(command)
        response = cur.fetchall()
        return response[0][0]
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("PSQL send-receive error!")


def set_bool_variable(var_name, var_value):
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command = "UPDATE thermostat_boolvariable SET value = '%s' WHERE NAME = '%s';" % (var_value, var_name)
        cur.execute(command)
        conn.commit()
        conn.close()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("PSQL send-receive error!")


def get_float_variable(var_name):
    try:
        conn = psycopg2.connect("dbname='" + dbname2 + "' user='" + user2 + "' host='" + host2 +
                                "' password='" + password2 + "'")
        cur = conn.cursor()
        command = "SELECT value FROM thermostat_floatvariable WHERE name = '%s';" % var_name
        cur.execute(command)
        response = cur.fetchall()
        return response[0][0]
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("PSQL send-receive error!")


def is_send_rf_on():
    return get_bool_variable('send_rf')


def is_heater_on():
    return get_bool_variable('heater_on')


def is_thermostat_on():
    return get_bool_variable('thermostat_on')


def turn_heater_on():
    set_bool_variable('heater_on', True)


def turn_heater_off():
    set_bool_variable('heater_on', False)


def turn_send_rf_on():
    set_bool_variable('send_rf', True)


def turn_send_rf_off():
    set_bool_variable('send_rf', False)


def turn_thermostat_on():
    set_bool_variable('thermostat_on', True)


def turn_thermostat_off():
    set_bool_variable('thermostat_on', False)


def get_thermostat_max_temp():
    return get_float_variable('temp_max')


def get_thermostat_min_temp():
    return get_float_variable('temp_min')