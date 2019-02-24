from subprocess import Popen, PIPE
import iphone_data


# ping the iphone
def ping():
    pid = Popen(["arp", "-a", iphone_data.iPhoneIP], stdout=PIPE)
    arp_output = pid.communicate()[0].split()
    # see if iphone is connected
    return iphone_data.iPhoneMAC in arp_output
