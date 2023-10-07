#!/usr/bin/env python3

import os, json, time, subprocess
from time import sleep
from predict import analyzeImage
from aladdin_connect import AladdinConnectClient

numExecutions_MAX = 3
rootDir = "/home/jkatebin/motion_detected/"
probabilityThreshold = 0.90
garage_email = ""
garage_password = ""




def loadAladdinConnectCredentials():
   "Loads AC credentials for the garage door from the HomeBridge configuration file so creds are in one place"
   homebridgeCfg = json.load(open("/var/lib/homebridge/config.json"))

   for i, curPlatform in enumerate(homebridgeCfg["platforms"]):
       if curPlatform["name"] == "Garage Door":
           globals()["garage_email"] = curPlatform["username"]
           globals()["garage_password"] = curPlatform["password"]

   return



def setupCamera():
    camera = PiCamera()
    camera.resolution = (2592, 1944)
    camera.rotation = 180
    return camera



def takePicture(basePath):
    "Take a picture from the RTSP stream of the garage camera and return the result filename"
    if basePath is None:
        basePath = rootDir

    timeStr = time.strftime("%Y%m%d-%H%M%S")
    imgPath = str(basePath + timeStr + ".jpg")

    print("Saving image from stream to: " + imgPath)

    commands = [
        "ffmpeg",
        "-i",
        "rtsp://192.168.50.23/live2",
	"-vframes",
     	"1",
        imgPath
	]

    if subprocess.run(commands).returncode == 0:
        print ("FFmpeg Script Ran Successfully")
    else:
        print ("There was an error running your FFmpeg script")
        return "/home/jkatebin/negative.jpg"
        #return "/home/jkatebin/20230522-150145.jpg"

#    ffmpeg -y -i rtsp://192.168.50.23/live2 -vframes 1 test.jpg

    return imgPath




def lookForMoto(pathToImage, deleteAfterReview):
    "Look for the motorcycle in the image specificed by the pathToImage parameter"
    analysisResult = analyzeImage(pathToImage)

    if deleteAfterReview:
        os.remove(pathToImage)
 
    for i, _potentialMatch in enumerate(analysisResult):
        if(_potentialMatch["probability"] > probabilityThreshold):
            print("Motorcycle found in image with " + str(_potentialMatch["probability"]) + " probability!")
            return True

    print("Image review complete, no motorcycle found...")
    return False




def openGarageDoor():
    "Open the garage door"
    # Decided to work with doors directly from python rather than back and forth via homebridge
    # Leaving homebridge connection in place however so I can still have the garage doors work with Apple
    # Library - https://github.com/shoejosh/aladdin-connect/tree/master
    # Run setup.py install to make avail to python

    # Create session using aladdin connect credentials
    global garage_email
    global garage_password
    client = AladdinConnectClient(garage_email, garage_password)
    client.login()

    # Get list of available doors
    for i, curDoor in enumerate(client.get_doors()):
        if curDoor["name"].lower().startswith("chamber"):
            if curDoor["status"] == "closed":
                print("Opening Garage Door")
                client.open_door(curDoor['device_id'], curDoor['door_number'])
            else:
                print("Garage door is already open!")
            return

    return






# Main logic
#camera = setupCamera()

loadAladdinConnectCredentials()

for curRunCount in range(numExecutions_MAX):
    # Take a picture and eval if my moto is in it.
    if lookForMoto(takePicture(rootDir), False):
        openGarageDoor()
        quit()
    else:
        sleep(3) # Wait a second and try again


print("Max number of image evaluation attempts has been reached, aborting script")
quit()


