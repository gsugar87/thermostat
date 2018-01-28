# thermostat

This is a specialized home thermostat that should be run on a raspberry pi.  It controls wireless outlets connected to space heaters to heat the apartment.  The program does many things.

1) Logs temperature continuously and saves it to a postgresql database

2) Knows if you are home by searching your wifi network to see if your phone is connected to turn on/off

3) Can set the temperature range you want heaters on

4) Can turn off thermostat for a set amount of time (good for saving energy during while you sleep)

5) Send commands via twitter so you can control it from anywhere

6) Sends current temperature readings or a temperature history plot via twitter

7) Can use the raspberry pi camera to take images and send to a specific email address

This needs four more files to work:

1) iphone_data.py, which has the following lines of code filled in with your phone's ip and mac addresses:

        iPhoneIP = 'xxx.xxx.xx.xx'
        iPhoneMAC = 'xx:xx:xx:xx:xx:xx'

2) twitter_credentials.py, which has the following lines of code filled in with your twitter information:

        CONSUMER_KEY = ''
        CONSUMER_SECRET = ''
        ACCESS_TOKEN = ''
        ACCESS_SECRET =''
        ok_user_name = '' # the twitter username that you will send commands from

3) email_credentials.py, which has the following lines of code filled in with your email information:

        username = '' # your gmail username that will SEND the image
        password = '' # the gmail password associated with username
        send_to = '' # the email address where you want the image email sent

4) pg_credentials.py, which has the following lines of code filled in with your postgresql information:

        dbname = 'postgres'
        user = 'postgres'
        host = 'localhost'
        password = 'YOURPASSWORDHERE'

5) You will also have to install the libraries that allow for remote control of the wireless switches (433Utils) and find the code used to control each outlet.  You will need to run RFSniffer or a similar program to find the code used to control each outlet.

        git clone --recursive git://github.com/ninjablocks/433Utils.git
        cd 433Utils/RPi_utils
        make
	
Now you can use RFSniffer to get the RF code you want your raspberry pi to send.  Type in the following command and then press the buttons on your remote that you want to copy.

        ./RFSniffer

Save these codes and put them wherever you see "sudo /home/pi/433Utils/RPi_utils/codesend ' in remote_commands.py.


6) You will need to set up the postgresql server that will save the temperature history data.

        sudo apt-get install postgresql postgresql-contrib
        sudo -u postgres psql postgres
        (now you're on the psql command line)
        CREATE TABLE temperature_history (datetime timestamp, temp float);
        ALTER USER postgres ENCRYPTED PASSWORD 'your password in pg_credentials.py here';
        \q
        (now you're out of the psql command line)
        sudo nano -c /etc/postgresql/9.4/main/pg_hba.conf
        sudo nano -c /etc/postgresql/9.4/main/postgresql.conf


7) Install psycopg2 for python postgresql communication:

        sudo apt-get install python-psycopg2
	
8) Install other required python libraries:

        pip --no-cache-dir install matplotlib
	
