#!/usr/bin/env python

import time
import urllib.request
from PIL import Image
from deepstack_sdk import ServerConfig, Detection
import urllib.request
import shutil
import datetime
import followtarget2 as camMover
import cv2
import numpy as np

#debug flags
DEBUG = False

MOVECAMERA = True
cameraMoved = False
threshold = 0.7
recording_state = False
detection_interval = 3.0
record_delay_end = 15
time_from_last_detection = record_delay_end
config = ServerConfig("http://192.168.1.208:89")
detection = Detection(config)
targetObject = "person"
#"{IP}:{port}/{camid}/config/set?
motioneye_ip = "192.168.1.208"
motioneye_remote_control_port = "7999"
motioneye_cam_id = "1"


motioneye_set_command = motioneye_ip + ":" + motioneye_remote_control_port + "/" + motioneye_cam_id + "/config/set?"
motioneye_get_command = motioneye_ip + ":" + motioneye_remote_control_port + "/" + motioneye_cam_id + "/config/get?"

class MotionEye:
    def __init__(self, motioneye_set_command, motioneye_get_command, motioneye_recording_state, motioneye_ip, motioneye_remote_control_port, motioneye_cam_id):
        self.motioneye_set_command = motioneye_set_command
        self.motioneye_get_command = motioneye_get_command
        self.meye_recording_state = motioneye_recording_state
        self.motioneye_ip = motioneye_ip
        self.motioneye_remote_control_port = motioneye_remote_control_port
        self.motioneye_cam_id = motioneye_cam_id

    def check_recording_state(self):
        print("return recording state")
        try:
            print("attempting to open meye query path")
            contents = urllib.request.urlopen("http://"+self.motioneye_get_command+"query=emulate_motion",timeout=10).read().decode()
            print("contents:", contents)
            contents = contents[30:32]
        except:
            print('exception getting recording state')
            return -1
        if contents == 'on':
            print('motioneye currently recording')
            self.meye_recording_state = True
            return 1
        elif contents == 'of':
            print('motioneye currently NOT recording')
            self.meye_recording_state = False
            return 1
        else:
            print('unknown checking motion eye recording state:', contents)
            return -2
        return 1



    def stop_recording(self):
        print("running stop_recording()")
        try:
            contents = urllib.request.urlopen("http://"+self.motioneye_set_command+"emulate_motion=0",timeout=10).read().decode()
            #print(contents)
            if(contents.find('emulate_motion =')>=0):
                #contents = contents[17:18]
                print(contents)
                return 0
            else:
                print("error stopping motioneye recording:", contents)
                return -1
        except:
            print('exception getting recording state')
            return -1

    def start_recording(self):
        print("running start_recording()")
        try:
            contents = urllib.request.urlopen("http://"+self.motioneye_set_command+"emulate_motion=1",timeout=10).read().decode()
            #print(contents)
            if(contents.find('emulate_motion =')>=0):
                #contents = contents[17:18]
                print(contents)
                return 0
            else:
                print("error starting motioneye recording:", contents)
                return -1
        except:
            print('exception getting recording state')
            return -1

    def get_image(self):
        urllib.request.urlretrieve("http://"+self.motioneye_ip+":8765/picture/1/current/", "output.jpg")
        img = Image.open("output.jpg")
        return img

    def get_imageCV(self):
        url_response = urllib.request.urlopen("http://"+self.motioneye_ip+":8765/picture/1/current/")
        img = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)
        return img



def check_detection(response, object, image):
    personfound = False
    x = 0
    y = 0
    xw = 1920
    yh = 1080
    personCentroidX = -1
    personCentroidY = -1
    listX = []
    listY = []
    listXW = []
    listYH = []
    for obj in response:
        image = cv2.rectangle(image, (obj.x_min, obj.y_min), (obj.x_max,obj.y_max), (255,0,0), 2)
        image = cv2.putText(image, obj.label+" "+"{:.2%}".format(obj.confidence), (obj.x_min, obj.y_min-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1, cv2.LINE_AA)

        if (obj.label == object) and obj.confidence>=threshold:
            personfound = True
            print(obj.label, obj.confidence)
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print("Name: {}, Confidence: {}, x_min: {}, y_min: {}, x_max: {}, y_max: {}".format(obj.label, obj.confidence, obj.x_min, obj.y_min, obj.x_max, obj.y_max))
            listX.append(obj.x_min)
            listY.append(obj.y_min)
            listXW.append(obj.x_max)
            listYH.append(obj.y_max)
            #image = cv2.rectangle(image, (obj.x_min, obj.y_min), (obj.x_max,obj.y_max), (255,0,0), 2)
            #image = cv2.putText(image, obj.label, (obj.x_min, obj.y_min-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1, cv2.LINE_AA)
            #create a box when multiple objects are detected


    # computer center of box if person is found before returning
    if personfound:
        x = min(listX)
        y = min(listY)
        xw = max(listXW)
        yh = max(listYH)
        personCentroidX = int((x+xw)/2)
        personCentroidY = int((y+yh)/2)
        image = cv2.rectangle(image, (x, y), (xw ,yh), (0,0,255), 20)
        image = cv2.circle(image, (personCentroidX, personCentroidY), 5, (0,0,255), 5)
        image = cv2.putText(image, str(personCentroidX)+","+str(personCentroidY), (personCentroidX, personCentroidY-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 1, cv2.LINE_AA)
    return personfound, personCentroidX, personCentroidY, image



def save_image(source,destination_folder):  #source=path and filename #destination_folder=folder only path
    fname = str(datetime.datetime.now()).replace("-", "").replace(" ", "").replace(":", "").replace(".", "")
    print(fname)
    try:
        shutil.copy(source, destination_folder+fname+'.jpg')
    except shutil.SameFileError:
        print("Source and destination represents the same file.")
    # If there is any permission issue
    except PermissionError:
        print("Permission denied.")
    # For other errors
    except Exception as e:
        print("Error occurred while copying file.:", str(e))

def showImage(img):
    x, y, xw, yh = camMover.centerPercentageCoords(1920, 1080, 0.2)
    img = cv2.rectangle(img, (x, y), (xw, yh), (0, 255, 0), 1)
    cv2.imshow("debugWindow", img)
    cv2.waitKey(1)


def main():
    centroidX = -1
    centroidY = -1
    personInFrame = False

    motioneye = MotionEye( motioneye_set_command, motioneye_get_command, recording_state, motioneye_ip, motioneye_remote_control_port, motioneye_cam_id)



    if(motioneye.check_recording_state()> 0):
       motioneye.stop_recording()
    while True:
        print("loop")
        if(motioneye.check_recording_state() > 0):
            break
        else:
            print("cannot check recording state, retrying after 1 second...")
            time.sleep(1) # wait for another seonds the retry checking state
    while True:
        start = time.time()
        try:
            rtspFrame = motioneye.get_imageCV()
        except Exception as e:
            print("Exception getting frame:", str(e))
        try:
            #print('deepcheck')
            print(".",end='',flush=True)
            response = detection.detectObject( rtspFrame,output="frame.jpg")
        except:
            print("error reaching deepstackAI")
        try:
            personInFrame, centroidX, centroidY, rtspFrame = check_detection(response, object=targetObject, image=rtspFrame)
        except Exception as e:
            print("exception caused by unreachable deepstackAI:", str(e))
        #print("PersonInFrame = ", personInFrame)
        if DEBUG:
            showImage(rtspFrame)
        if personInFrame:
            if MOVECAMERA:
              cameraMoved = camMover.cameraTracker(centroidX, centroidY)
            save_image(source='./frame.jpg' ,destination_folder='./detections/') #comment this out so that detections are not saved
            time_from_last_detection = record_delay_end
            if motioneye.meye_recording_state == False:
                if time_from_last_detection == record_delay_end:
                    motioneye.start_recording()
                    motioneye.meye_recording_state = True


        if not(personInFrame) and motioneye.meye_recording_state == True:
            time_from_last_detection = time_from_last_detection - 1
            print("time_from_last_detection:", time_from_last_detection)
            if time_from_last_detection <= 0:
                motioneye.stop_recording()
                motioneye.meye_recording_state = False
                if cameraMoved and MOVECAMERA:
                    camMover.resetCameraPosition()
                    cameraMoved = False
                print("meye_recording_state:",motioneye.meye_recording_state)
        end = time.time()
        delta = end - start
        #print("delta:", delta)
        if delta < 1:
            time.sleep(detection_interval - delta)
            end = time.time()
        #print("duration:", end - start)

if __name__ == "__main__":
    main()
