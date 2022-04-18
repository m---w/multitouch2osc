# Python script to access raw multitouch data and send via OSC.
# 2020 Marian Weger

# Explanations:
# https://www.kernel.org/doc/html/latest/input/multi-touch-protocol.html
# https://stackoverflow.com/questions/28841139/how-to-get-coordinates-of-touchscreen-rawdata-using-linux#28845362
# https://stackoverflow.com/questions/52124027/python-evdev-reading-axes-x-and-y-of-a-gamepad-simultaneously

from evdev import InputDevice, categorize, ecodes
import argparse
import math
from pythonosc import udp_client


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--ip", default="127.0.0.1",
      help="The ip of the OSC server")
  parser.add_argument("--port", type=int, default=5015,
      help="The port the OSC server is listening on")
  parser.add_argument("--device", default="/dev/input/by-id/usb-Multi_touch_Multi_touch_overlay_device_6C698AD81038-event-if01",
      help="The absolute path to the device")
  args = parser.parse_args()

  client = udp_client.SimpleUDPClient(args.ip, args.port)
  device = InputDevice(args.device)
  print(device)

# set sensor address by name (find out and test in terminal with evtest)
# Terminal: sudo evtest --grab /dev/input/by-id/usb-Multi_touch_Multi_touch_overlay_device_6C698AD81038-event-if01
# device = InputDevice("/dev/input/by-id/usb-Multi_touch_Multi_touch_overlay_device_6C698AD81038-event-if01")
# device = InputDevice("/dev/input/event8")

device.grab()  # become the sole recipient of all incoming input events


slot = 0
data = {}
updated = {}
nslots = 1
# initslot = [-1, -1, -1.0, -1.0, -1, -1.0, -1.0]
data[0] = [-1, -1, -1.0, -1.0, -1, -1.0, -1.0]
ar = 16.0/9.0 # set aspect ratio of the sensor
resolution = 32768.0 # set resolution of the sensor
diagonal = math.sqrt(resolution**2 * 2)

for event in device.read_loop():
  absevent = categorize(event)
  # print(ecodes.bytype[absevent.event.type][absevent.event.code])
  # print("%d %d %d" % (event.type, event.code, event.value) )
  # client.send_message("/multitouch", [event.type, event.code, event.value])
  code = ecodes.bytype[absevent.event.type][absevent.event.code]
  # print("%s %d" % (code, event.value) )
  
  if code == 'ABS_MT_SLOT':
    slot = event.value
    if slot+1 > nslots:
      nslots = slot+1
      data[slot] = [-1, -1, -1.0, -1.0, -1, -1.0, -1.0]
      
  elif code == 'ABS_MT_TRACKING_ID':
    updated[slot] = True
    if event.value == -1:
      data[slot] = [slot, -1, -1.0, -1.0, -1, -1.0, -1.0]
      # print(data[slot])
    else:
      data[slot][0] = slot
      data[slot][1] = event.value
    
      
  elif code == 'ABS_MT_POSITION_X':
    data[slot][2] = event.value / resolution
    updated[slot] = True
    
  elif code == 'ABS_MT_POSITION_Y':
    data[slot][3] = event.value / resolution
    updated[slot] = True
    
  elif code == 'ABS_MT_ORIENTATION':
    data[slot][4] = event.value
    updated[slot] = True
    
  elif code == 'ABS_MT_TOUCH_MAJOR':
    data[slot][5] = event.value / diagonal
    updated[slot] = True
    
  elif code == 'ABS_MT_TOUCH_MINOR':
    data[slot][6] = ar * event.value  / diagonal
    updated[slot] = True


  if code == 'SYN_REPORT':
    for i in data:
      if updated[i]:
          client.send_message("/mt", data[i])
          # print(data)
          # client.send_message("/mt/%d" % (i), data[i])
          updated[i] = False
    # for i in updated:
    #   updated[i] = False



