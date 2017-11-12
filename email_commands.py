# This file contains the email commands used by the raspberry pi

import smtplib
import email_credentials
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import datetime

def send_image(image_filename):
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(email_credentials.username, email_credentials.password)
    msg = MIMEMultipart()
    msgText = MIMEText('Image taken at ' + datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p') +
                       '. <br><img src="cid:image1"><br>', 'html')
    msg.attach(msgText)
    fp = open(image_filename, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()
    msgImage.add_header('Content-ID', '<image1>')
    msg.attach(msgImage)
    msg['Subject'] = 'Image from Raspberry Pi!'
    msg['From'] = email_credentials.username+'@gmail.com'
    msg['To'] = email_credentials.send_to
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.close()
