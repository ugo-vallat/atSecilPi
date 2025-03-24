from gps_simulator import *
from libgps import *
from time import sleep

device = gps_get_device()

if device == None:
    exitl("failed to get device")

while True :
    line = gps_read_trame(device)
    if line:
        print(line)

