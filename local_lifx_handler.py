import paho.mqtt.client as mqtt
import datetime
import json
import requests
import pygame
from lifxlan import LifxLAN
from copy import copy
import sys

acksound = '/home/pi/Downloads/computer.mp3'
lifx_auth = 'c3d6d0ee501bf70f40ad7722a2907fa126b2dadc6a160bd7debb6fd7b4ad905d'
location = "Englefield Road"
global base_location
base_location = location

def time_now():
    return datetime.datetime.now().strftime('%H:%M:%S.%f')

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()
HOST = "localhost"
PORT = "1883"
GOOD_STUFF = ['hermes/hotword/default/detected',
              'hermes/intent/lightsTurnOnSet',
              'hermes/intent/lightsTurnDown',
              'hermes/intent/lightsTurnUp',
              'hermes/intent/lightsTurnOff',
              'hermes/intent/rxe1:lightschangecolour']


def determine_LIFX_environment():

    num_lights = None
    if len(sys.argv) != 2:
        print("\nDiscovery will go much faster if you provide the number of lights on your LAN:")
        print("  python {} <number of lights on LAN>\n".format(sys.argv[0]))
    else:
        num_lights = int(sys.argv[1])

    # instantiate LifxLAN client, num_lights may be None (unknown).
    # In fact, you don't need to provide LifxLAN with the number of bulbs at all.
    # lifx = LifxLAN() works just as well. Knowing the number of bulbs in advance 
    # simply makes initial bulb discovery faster.
    print("Discovering lights...")
    lifx = LifxLAN(num_lights)

    # get devices
    global devices
    global num_devices
    devices = lifx.get_lights()
    num_devices = len(devices)
    print("\nFound {} light(s):\n".format(num_devices))


 
def on_connect(client, userdata, flags, rc):
    for topic in GOOD_STUFF:
    # subscribe to all messages
    
        mqtt_client.subscribe(topic)


# Process a message as it arrives
def on_message(client, userdata, msg):
    print msg.topic
    print('[{}] - {}: {} '.format(time_now(), msg.topic, msg.payload))
    session_id = parse_session_id(msg)
    if msg.topic =='hermes/hotword/default/detected':  
        print('[{}] - {}: {} '.format(time_now(), msg.topic, msg.payload))
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(acksound)
        pygame.mixer.music.play()
        
    else:
        slots = parse_slots(msg) 
       
       
    if msg.topic == 'hermes/intent/lightsTurnOnSet':
         glist = group_split(slots)
         room = slots.get("house_room")
         if str(room) != 'None':
                 response = 'Turning lights on in the ' + str(room)
                 say (session_id, response)
         else:        
                 response = 'Turning lights on'
                 say (session_id, response)
         for index, item in enumerate(glist, start=0):
               item.set_power("on", rapid=True)

    elif msg.topic == 'hermes/intent/lightsTurnDown':
         glist = group_split(slots)
         room = slots.get("house_room")
         response = 'Turning lights down'
         say (session_id, response)    
         for index, item in enumerate(glist, start=0):
              color = item.get_color()
              HSBK = list(color)
              HSBK[2] = int(HSBK[2]/2)
              item.set_color(HSBK,500, rapid=True)
             

    elif msg.topic == 'hermes/intent/rxe1:lightschangecolour':
           room = slots.get("house_room")
     
         
           colour = slots.get("colour")
      



           if colour == 'warm white':
                temp = 2700
                for index, item in enumerate(devices, start=0):
                    color = item.get_color()
                    HSBK = list(color)              
                    HSBK[3] = temp
                    item.set_color(HSBK,500, rapid=True)
           if colour == 'cool white':
                temp = 6000
                for index, item in enumerate(devices, start=0):
                    color = item.get_color()
                    HSBK = list(color)              
                    HSBK[3] = temp
                    item.set_color(HSBK,500, rapid=True)


           
           
    elif msg.topic == 'hermes/intent/lightsTurnUp':
           room = slots.get("house_room")
           colour = slots.get("colour")
           response = 'Turning lights up'
           say (session_id, response)    
           for index, item in enumerate(devices, start=0):
             if str(room) != 'None':
                  color = item.get_color()
                  HSBK = list(copy(color))
                  HSBK[2] = int(HSBK[2]*2)
                  if (HSBK[2] > 65535):
                       HSBK[2] = 65535
                  item.set_color(HSBK,500, rapid=True)
             else:  
                  color = item.get_color()
                  HSBK = list(copy(color))
                  HSBK[2] = int(HSBK[2]*2)
                  if (HSBK[2] > 65535):
                       HSBK[2] = 65535
                  item.set_color(HSBK,500, rapid=True)
                              
    elif msg.topic == 'hermes/intent/lightsTurnOff': 
         glist = group_split(slots)
         room = slots.get("house_room")
         if str(room) != 'None':
                 response = 'Turning lights off in the ' + str(room)
                 say (session_id, response)
         else:        
                 response = 'Turning lights on'
                 say (session_id, response)
         for index, item in enumerate(glist, start=0):
               item.set_power("off", rapid=True)


def parse_slots(msg):
    '''
    We extract the slots as a dict
    '''
    data = json.loads(msg.payload)
    return {slot['slotName']: slot['rawValue'] for slot in data['slots']}

def parse_session_id(msg): 
    '''
    Extract the session id from the message
    '''
    data = json.loads(msg.payload)
    return data['sessionId']

def say(session_id, text):
    '''
    Print the output to the console and to the TTS engine
    '''
    print(text)
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'text': text, "sessionId" : session_id}))

def group_split(slots):
      # parses the master device list to return members of the group requested                      
      group_list = []
      room = slots.get("house_room")
      
      print(room)
      for index, item in enumerate(devices, start=0):
         if str(room) != 'None':
              group = item.get_group()
              print (group)
              if group == room:
                 group_list.append(devices[index])
         else:
                 group_list.append(devices[index])

      return group_list                

determine_LIFX_environment()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(HOST, PORT)
mqtt_client.loop_forever()


'''

           room = slots.get("house_room")
           level = slots.get("number")
           print(room)
           print(level)
               
           payload = {
               "power" : "on"
                
           }    
           headers = {
              "Authorization": "Bearer %s" % lifx_auth,
              
           }
           print ('https://api.lifx.com/v1/lights/location:%s/state' % location)
           response = requests.put('https://api.lifx.com/v1/lights/location:%s/state' % base_location, data=payload, headers=headers)
           print(response)
           '''
