######################################################################
#    
#    Tapo-C200-event-listener
#    ONVIF event listener for Tapo C200 (and probably more cameras)
#
#    Ok, here is the deal, I am not native english speaker, so I'll try my best:
#
#    I made this script to listen for events on the TP-Link Tapo C200. This is not because I hate HASS (which is awesome!) but to know how to do it. Also the example from onvif-zeep-async made it possible, this is just a fork of their work. Also many thanks to pytapo, the lib that made me not return the camera because of the lack of cloud support haha.
#
#    Requieremets This is a listener, you need to have something turned on and in the same network. Also, better to fix the ip of the cam in your router.
#
#    I tested this with a Raspberry Pi 4B 2gb model, latest os. I assume you already know how to setup your camera for pytapo but if it is not the case, check TP-Link's guide
#
#    pip3 install pytapo
#    pip3 install onvif-zeep (dunno if needed for the second, but this were my steps)
#    pip3 install onvif-zeep-async  //not needed
#    (if you want to use my whole script, get opencv and pushbullet too)
#
#    Go to the onvif-zeep-async (Forking hunterjm/python-onvif-zeep-async) repo and download their wsdl folder. It is really important, as the onvif-zeep defs are broken. I also tested with the https://www.onvif.org/profiles/specifications/ and they work too. Run the script once, Python will tell you were to put the files. Run it again, it will tell you another directory. Run it again, it may work now, else copy all the files to that directory too. I know the ONVIFCamera() sets the path at the end, but this never worked for me properly.
#
#    Code has a lot of comments, it is really dirty, needs a lot of improvement and because it was for my use, I left it with the import of cv2 and pushbullet, cos my use is to grab frames and sent them to my phone (the main feature any security camara needs to have). You can set this as a service, I left it overnight and the camera never complained.
# 
#    If you know how to improve it, don't be shy, world needs more people like you.
#    
######################################################################

import asyncio, logging, time
import datetime as dt
from datetime import timezone
from pytz import UTC
from zeep import xsd
from onvif import ONVIFCamera
#import cv2
#from pytapo import Tapo
#from pushbullet import Pushbullet


#pb = Pushbullet('your token here')
user = "tapohome"
password = "TplinkJepes"
host = "192.168.1.211"

#camera just needs to be set once, no prob
#tapo = Tapo(host, user, password)

#enable this if you want to see the XML output from the service
#really REALLY helpful to debug.
#logging.getLogger("zeep").setLevel(logging.DEBUG)

#common pullpoint handlers, useful for debug
#http://192.168.100.35:1025/event-1025_1025
#http://192.168.100.35:1024/event-1024_1024


#to save frames with the event, you can delete it
def saveFrame(frame):
    fileDate = dt.datetime.now()
    fileDate = fileDate.strftime("%d-%m_%H-%M-%S")
    fileName = f'cap_{fileDate}.jpg'
    cv2.imwrite(fileName, frame)
    with open(fileName, "rb") as pic:
        file_data = pb.upload_file(pic, "picture.jpg")
    push = pb.push_file(**file_data)
    print("Capture sent: "+ str(fileName))
    
async def main():   #//renamed from run() to main()
    
    #bools for the loops, so I don't get mixed, may change it 
    mainCond = True
    seCond = True

    #starts main loop
    while mainCond:
        
        #check if motion is off to kill it
        #if tapo.getMotionDetection()['enabled'] == "off":
        #    print("bye bye")
        #    return
        
        try: 
            mycam = ONVIFCamera(host,2020,user,password)
        except:
            print("ONVIF cannot connect")
        #sets connection
        try:
            await mycam.update_xaddrs()
        except:
            print("error on mycam.update_xaddrs()")
            continue
        

        #check if events work with camera
        if not await mycam.create_pullpoint_subscription():
            print("PullPoint not supported")
            return

        #welcome msg
        print("Loop begins")
               
        
        #creates all the paperwork for the event handler
        pullpoint = mycam.create_pullpoint_service()
        await pullpoint.SetSynchronizationPoint()
        req = pullpoint.create_type("PullMessages")
        
        #this data comes from the ONVIF specification
        req.MessageLimit = 100
        req.Timeout = dt.timedelta(seconds=60)
    
        #Subs to the pullpoint event
        #the sub is what makes the connection doesn't end
        subscription = mycam.create_subscription_service("PullPointSubscription")
        
        #here comes the magic
        while seCond:
            
            #we kill everything if motion in the cam is turned off
            #if tapo.getMotionDetection()['enabled'] == "off":
            #    print("bye bye")
            #    await subscription.Unsubscribe()
            #    await mycam.close()
            #    return
            
            #check for messages
            print("cam ok pull of messages begins")
            messages = await pullpoint.PullMessages(req)
            
            #checks the list received, unfortunately, cannot
            #read that list to look for motion event,
            #may work directly using plain zeep and filter
            if messages.NotificationMessage:
                messages.NotificationMessage.clear()
                print("Event triggered")
    
                #I tried not closing connection, just recycling the
                #subscription, but it sends a TON of events and I couldn't
                #read them, this needs more work.
                await subscription.Unsubscribe()
                await mycam.close()
                
                                
                #set your actions here
                #maybe a CV2 to snap a frame
                #and send it over pushbullet
                #or email, you choose ;)
                
                #five pics, they take like 4 seconds each,
                #may work on resizing it to take less time
                #for i in range(1,6):
                    #rstp
                #    try:
                #        cap = cv2.VideoCapture(f'rtsp://{user}:{password}@{host}:554/stream1')
                #        ret, frame = cap.read()
                #        saveFrame(frame)
                #        cap.release()

                #     except:
                #         print("rtsp cannot connect")
                #         pass
                    
                    
                #get out of the loop                
                break
            
            else:
                print("nothing new in 60s")
                #renew sub. this will never end, it sets
                #next day always
                await subscription.Renew(setTime())
                             
       
        print("resetting")
        
        #to allow reconnect of the camera, 3 seconds are the min
        #if later we can read motion event without closing connection
        #this will be over and it'll be real time :) 
        time.sleep(3)
        

#just to get the time for expiring subscription, may work on something like hass does
#substracting seconds to renew daily so it doesn't bother the service that much,
#but for now it works 
def setTime():
    timenew = ((dt.datetime.utcnow() + dt.timedelta(days=1))
    .isoformat(timespec="seconds").replace("+00:00", "Z"))
    return timenew

#starts the loop, it will never end, the whiles wouldn't let it,
#... I supose.
#def main(): #in case you want to load it in another way
if __name__ == "__main__":
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(run())
     asyncio.run(main())
