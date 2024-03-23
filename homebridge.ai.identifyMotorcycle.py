#!/usr/bin/env python3

import os, json, time, subprocess, requests
from time import sleep
from predict import analyzeImage


numExecutions_MAX = 3
rootDir = "/home/jkatebin/motion_detected/"
probabilityThreshold = 0.85

homebridgeUrl = 'https://192.168.50.102'
homebridgeAuthHeaders = ''
garage_door_accessory_name = 'Chamberlain 2'
garage_door_accessory_uniqueId = ''




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







    


def genHomebridgeToken():
    "Generate OAuth2 token to make API calls against the Homebridge"    
    global homebridgeAuthHeaders
    
    cfg = json.load(open("/usr/local/bin/homebridge.json"))["homebridge"]

    creds = { 'username': cfg['username'], 'password': cfg['password'] }

    auth = requests.post(homebridgeUrl + '/api/auth/login', json = creds, verify=False).json()
    homebridgeAuthHeaders = {"Authorization": "Bearer " + auth['access_token'] }
    
    return


def getGarageDoorAccessoryId():
    global homebridgeAuthHeaders
    global garage_door_accessory_uniqueId
    
    genHomebridgeToken()
    
    accessories = requests.get(homebridgeUrl + '/api/accessories', headers=homebridgeAuthHeaders, verify=False).json()
    
    # Search for the 'Chamberlain 2' accessory and get it's unique ID property
    for item in accessories:
        if item['serviceName'] == garage_door_accessory_name:
            garage_door_accessory_uniqueId = item['uniqueId']       





def openGarageDoor():
    "Open the garage door"
    global homebridgeAuthHeaders
    global garage_door_accessory_uniqueId

    getGarageDoorAccessoryId()

    if garage_door_accessory_uniqueId == '':
        print('Error - Cannot find garage door accessory named: ' + garage_door_accessory_name)
        return
    

    open_request = {
        "characteristicType": "TargetDoorState",
        "value": "0"
        }
    
    print("Opening Garage Door")
    open_result = requests.put(homebridgeUrl + '/api/accessories/' + garage_door_accessory_uniqueId, json=open_request, headers=homebridgeAuthHeaders, verify=False)

    return









# Main logic
#camera = setupCamera()

for curRunCount in range(numExecutions_MAX):
    # Take a picture and eval if my moto is in it.
    if lookForMoto(takePicture(rootDir), False):
        openGarageDoor()
        quit()
    else:
        sleep(3) # Wait a second and try again


print("Max number of image evaluation attempts has been reached, aborting script")
quit()


