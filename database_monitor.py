# Author: Glenn Sugar
# This script will monitor the postgresql database and see if the heater should be turned on or off
# It uses modprobe to mount the sensors to /sys/bus/w1/devices/

import time
import postgresql_commands as psql
import remote_commands as rc
import iphone_commands as ic

verbose = True


def run():
    while True:
        # See if we should send a signal
        if psql.is_send_rf_on():
            # See if we should turn on or off
            if psql.is_heater_on():
                rc.onAll(None, False)
            else:
                rc.offAll(None, False)

        # See if the thermostat is on
        if psql.is_thermostat_on():
            # See if the current temperature is within the thermostat range
            current_temp = float(psql.get_recent_temp()[0])
            temp_max = psql.get_float_variable('temp_max')
            temp_min = psql.get_float_variable('temp_min')
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
        psql.set_iphone_home(is_iphone_home)

        if verbose:
            print("Current T: %f, Max T: %f, Min T: %f Iphone Home: %s" % (current_temp, temp_max, temp_min,
                                                                           is_iphone_home))


if __name__ == "__main__":
    run()
