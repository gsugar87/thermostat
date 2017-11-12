# this file will use the raspberry pi camera to take and save images

import picamera


def save_image(filename):
    # take an image with the camera
    camera = picamera.PiCamera()
    camera.capture(filename)
    camera.close()
