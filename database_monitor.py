# Author: Glenn Sugar
# This script will monitor the postgresql database and see if the heater should be turned on or off
# It uses modprobe to mount the sensors to /sys/bus/w1/devices/

import time
import postgresql_commands as psql
import remote_commands as rc
import iphone_commands as ic

verbose = True


def run():
    iphone_change_counter = 0
    iphone_change_counter_threashold = 30
    while True:
        # See if we should send a signal
        if psql.is_send_rf_on():
            # See if we should turn on or off
            if psql.is_heater_on():
                rc.onAll(None, False)
            else:
                rc.offAll(None, False)

        # See if the current temperature is within the thermostat range
        current_temp = float(psql.get_recent_temp()[0])
        temp_max = psql.get_float_variable('temp_max')
        temp_min = psql.get_float_variable('temp_min')

        # See if the thermostat is on
        if psql.is_thermostat_on():
            if current_temp < temp_min:
                psql.turn_heater_on()
                psql.turn_send_rf_on()
            elif current_temp > temp_max:
                psql.turn_heater_off()
                psql.turn_send_rf_on()
            else:
                psql.turn_send_rf_off()

        # See if the iphone is home
        is_iphone_home = ic.ping()

        # See if the iphone has changed from whats on the database
        if psql.is_iphone_home() != is_iphone_home:
            iphone_change_counter += 1
            if iphone_change_counter > iphone_change_counter_threashold:
                psql.set_iphone_home(is_iphone_home)
                # See if we left the house
                if not is_iphone_home:
                    # Turn off everything
                    psql.turn_heater_off()
                    psql.turn_send_rf_on()
                    psql.turn_thermostat_off()
        else:
            iphone_change_counter = 0

        if verbose:
            print("Current T: %f, Max T: %f, Min T: %f Iphone Home (ping, db): %s %s" %
                  (current_temp, temp_max, temp_min, is_iphone_home, psql.is_iphone_home()))


if __name__ == "__main__":
    run()
