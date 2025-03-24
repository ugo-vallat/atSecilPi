from gps_simulator import *
from time import sleep
import threading
import queue
import json
import sys
from enum import Enum

from libgps import *
from libnetwork import *
import log

# -------- GLOBAL VARIABLES -------- 

log.PRINT_LOG = False


class Mode(Enum):
    PI=1
    LOCAL_HOST=2

MODE = Mode.LOCAL_HOST
ID = 1

# ----------------------------------


def gps_simulator() :
    printl("start...")
    run_simulator()


def gps_handler(buffer:queue.Queue):
    printl("start...")
    device = gps_get_device()
    if device == None:
        exitl("failed to get device")

    printl(f"start reading GPS data on {device}")
    while True:
        line = gps_read_trame(device)
        printl(f"new line = {line}")
        if line and line[:6] == "$GPGGA":
            buffer.put(gps_gga_to_coord(line))

def adhoc_sender(network:AdhocNetwork, buffer:queue.Queue):
    printl("start...")
    while True:
        pos = buffer.get()
        print(f"[gps_app.adhoc_sender] send pos \t : {pos}")
        pos = json.dumps(pos)
        network.broadcast(pos)


def adhoc_receiver(network:AdhocNetwork):
    printl("start...")
    while True:
        pos = network.read_data()
        (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
        pos = (fix, lat, lon, altitude)
        print(f"[gps_app.adhoc_receiver] received pos \t : {pos}")


def usage():
    return f"usage : {sys.argv[0]} <mode> \n\n mode\t[pi,local_host]"

if len(sys.argv) != 2 : 
    exitl(usage())


if (sys.argv[1] == "pi"):
    MODE = Mode.PI
elif (sys.argv[1] == "local_host"):
    MODE = Mode.LOCAL_HOST
else:
    exitl(usage())

network = AdhocNetwork(id=ID, local_host=(MODE == Mode.LOCAL_HOST))
buffer = queue.Queue()

p_gps_simulator = threading.Thread(target=gps_simulator)
p_gps_handler = threading.Thread(target=gps_handler, args=(buffer,))
p_adhoc_sender = threading.Thread(target=adhoc_sender, args=(network,buffer,))
p_adhoc_receiver = threading.Thread(target=adhoc_receiver, args=(network,))


p_gps_simulator.start()
sleep(1)
p_gps_handler.start()
p_adhoc_sender.start()
p_adhoc_receiver.start()




