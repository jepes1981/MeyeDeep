
import cv2
import urllib.request
import numpy as np
from pytapo import Tapo
import sys

#PYTAPO DATA and initialization
user = "tapohome" # user you set in Advanced Settings -> Camera Account
password = "TplinkJepes" # password you set in Advanced Settings -> Camera Account
host = "192.168.1.211" # ip of the camera, example: 192.168.1.52
cameraMoveSpeed = 9
tapo = Tapo(host, user, password)

#additional info
#vertical moveMotor is total of 69 interval
#from middle to top/bottom is 25 interval
#from middle to left/right most is 45 interval
HorizontalFactor = 45
VerticalFactor = 25



#initialize global variables
rtspResolutionX = 1920
rtspResolutionY = 1080
CENTERPERCENTAGE = 0.1 #percentage of screen to use as no move, camera does not move if center of target is with the bounding box

#url for motioneye image
url='http://192.168.1.208:8765/picture/1/current/'


def centerPercentageCoords(rtspResolutionX, rtspResolutionY, CENTERPERCENTAGE):
    startx = int((rtspResolutionX/2)-(rtspResolutionX*CENTERPERCENTAGE/2))
    starty = int((rtspResolutionY/2)-(rtspResolutionY*CENTERPERCENTAGE/2))
    start_point = (startx, starty)
    endx = int(CENTERPERCENTAGE*rtspResolutionX)
    endy = int(CENTERPERCENTAGE*rtspResolutionY)
    #end_point = (startx + endx, starty + endy)
    #return start_point, end_point # returns ( (x,y) , (x+w, x+h) )
    return startx, starty , startx + endx, starty + endy


def getImage():
    url_response = urllib.request.urlopen(url)
    img = cv2.imdecode(np.array(bytearray(url_response.read()), dtype=np.uint8), -1)
    return img


def chooseDirection(x, y):
    xDir = 0
    yDir = 0

def isTargetWithinBounds(centerbound, targetX, targetY):
    x, y, xw, yh = centerbound
    print(x, y, xw, yh)
    if ( ((targetX>=x) and (targetX<=xw)) and ((targetY>=y) and (targetY<=yh)) ):
        return True
    else:
        return False


def getTarget():
    targetX = 575
    targetY = 324
    return targetX, targetY

def moveCamera(centerBound, targetX, targetY):
    print("moving camera...")
    errorNormalPanTilt = False
    errorX = False
    x, y, xw, yh = centerBound
    moveTargetX = 0
    moveTargetY = 0
    if targetX < x:
        moveTargetX = -1*cameraMoveSpeed
    elif targetX > xw:
        moveTargetX = cameraMoveSpeed

    if targetY < y:
        moveTargetY = cameraMoveSpeed
    elif targetY > yh:
        moveTargetY = -1*cameraMoveSpeed

    print("vamera target",targetX,targetY)
    try:
        tapo.moveMotor(moveTargetY, moveTargetY)
    except Exception as e:
        print("Error moving camera normally", str(e))
        errorNormalPanTilt = True
    if errorNormalPanTilt:
        print("Trying to pan/horintal only movement")
        try:
            tapo.moveMotor(moveTargetX, 0)
        except Exception as e:
            print("Error moving camera PAN/HORTIZONTAL: Exeption = ", str(e))
            errorX = True
    if errorX:
        try:
            tapo.moveMotor(0, moveTargetY)
        except Exception as e:
            print("Error moving camera TILT/VERTICAL: Exeption = ", str(e))

def moveCameraOld(centerBound, targetX, targetY):
    print("moving camera...")
    errorNormalPanTilt = False
    errorX = False
    x, y, xw, yh = centerBound
    moveTargetX = 0
    moveTargetY = 0
    if targetX < x:
        moveTargetX = -1*cameraMoveSpeed
    elif targetX > xw:
        moveTargetX = cameraMoveSpeed

    if targetY < y:
        moveTargetY = cameraMoveSpeed
    elif targetY > yh:
        moveTargetY = -1*cameraMoveSpeed
    try:
        tapo.moveMotor(moveTargetY, moveTargetY)
    except Exception as e:
        print("Error moving camera normally", str(e))
        errorNormalPanTilt = True
    if errorNormalPanTilt:
        print("Trying to pan/horintal only movement")
        try:
            tapo.moveMotor(moveTargetX, 0)
        except Exception as e:
            print("Error moving camera PAN/HORTIZONTAL: Exeption = ", str(e))
            errorX = True
    if errorX:
        try:
            tapo.moveMotor(0, moveTargetY)
        except Exception as e:
            print("Error moving camera TILT/VERTICAL: Exeption = ", str(e))



def resetCameraPosition():
    tapo.setPreset(1)

def cameraTracker(X, Y):
    centerBound = centerPercentageCoords( rtspResolutionX, rtspResolutionY, CENTERPERCENTAGE )
    targetX, targetY = getTarget()
    targetX = X
    targetY = Y
    print(isTargetWithinBounds(centerBound, targetX, targetY))
    if not (isTargetWithinBounds(centerBound, targetX, targetY)):
        moveCamera(centerBound, targetX, targetY)
        return True
    return False



if __name__ == "__main__":
    if (not len(sys.argv) == 3):
        print("sys.arv length is != 3", sys.argv)
        exit()
    cameraTracker(int(sys.argv[1]), int(sys.argv[2]))
