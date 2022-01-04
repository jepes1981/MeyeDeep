import time
import urllib.request
from PIL import Image
from deepstack_sdk import ServerConfig, Detection
import urllib.request

threshold = 0.55
meye_recording_state = False
record_delay_end = 15
time_from_last_detection = record_delay_end
config = ServerConfig("http://192.168.1.208:89")
detection = Detection(config)
#"{IP}:{port}/{camid}/config/set?
motioneye_ip = "192.168.1.208"
motioneye_remote_control_port = "7999"
motioneye_cam_id = "1"

motioneye_set_command = motioneye_ip + ":" + motioneye_remote_control_port + "/" + motioneye_cam_id + "/config/set?"
motioneye_get_command = motioneye_ip + ":" + motioneye_remote_control_port + "/" + motioneye_cam_id + "/config/get?"

def check_recording_state():
    print("return recording state")
    try:
        print("attempting to open meye query path")
        contents = urllib.request.urlopen("http://"+motioneye_get_command+"query=emulate_motion",timeout=10).read().decode()
        print("contents:", contents)
        contents = contents[30:32]
    except:
        print('exception getting recording state')
        return -1
    if contents == 'on':
        print('motioneye currently recording')
        meye_recording_state = True
        return 1
    elif contents == 'of':
        print('motioneye currently NOT recording')
        meye_recording_state = False
        return 1
    else:
        print('unknown checking motion eye recording state:', contents)
        return -2
    return 1
        
   
def stop_recording():
    print("running stop_recording()")
    try:
        contents = urllib.request.urlopen("http://"+motioneye_set_command+"emulate_motion=0",timeout=10).read().decode()
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
 
def start_recording():
    print("running start_recording()")
    try:
        contents = urllib.request.urlopen("http://"+motioneye_set_command+"emulate_motion=1",timeout=10).read().decode()
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
    


def get_image():
    urllib.request.urlretrieve("http://192.168.1.208:8765/picture/1/current/", "output.jpg")
    img = Image.open("output.jpg")
    return img

def check_detection(response, object):
    personfound = False
    for obj in response:
        if (obj.label == object) and obj.confidence>=threshold:
            personfound = True
            print(obj.label, obj.confidence)
            print("Name: {}, Confidence: {}, x_min: {}, y_min: {}, x_max: {}, y_max: {}".format(obj.label, obj.confidence, obj.x_min, obj.y_min, obj.x_max, obj.y_max))
    return personfound
  

            
if __name__ == "__main__":
    personInFrame = False
    if(check_recording_state()> 0):
       stop_recording()
    while True:
        print("loop")
        if(check_recording_state() > 0):
            break
        else:
            print("cannot check recording state, retrying after 1 second...")
            time.sleep(1) # wait for another seonds the retry checking state
    while True:
        start = time.time()
        try:
            #print('deepcheck')
            print(".",end='',flush=True)
            response = detection.detectObject(get_image(),output="frane.jpg")
        except:
            print("error reaching deepstackAI")
        try:
            personInFrame = check_detection(response, object="person")
        except Exception as e:
            print("exception caused by unreachable deepstackAI:", str(e))
        #print("PersonInFrame = ", personInFrame)
        if personInFrame:
            time_from_last_detection = record_delay_end
            if meye_recording_state == False:
                if time_from_last_detection == record_delay_end:
                    start_recording()
                    meye_recording_state = True
        if not(personInFrame) and meye_recording_state == True:
            time_from_last_detection = time_from_last_detection - 1
            print("time_from_last_detection:", time_from_last_detection)
            if time_from_last_detection <= 0:
                stop_recording()
                meye_recording_state = False
                print("meye_recording_state:",meye_recording_state)
        end = time.time()
        delta = end - start
        #print("delta:", delta)
        if delta < 1:
            time.sleep(2.0 - delta)
            end = time.time()
        #print("duration:", end - start)



            
        


