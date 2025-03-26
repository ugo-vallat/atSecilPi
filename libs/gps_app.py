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

#__________________________________ TYPE DEF __________________________________

class NetworkMode(Enum):
    ADHOC=1
    LOCALHOST=2

class AppMode(Enum):
    SENDER=1
    RECEIVER=2
    LOOPBACK=3


#_________________________________ VARS _________________________________

# ___ CONFIG VAR ___
APP_MODE = AppMode.LOOPBACK
NETWORK_MODE = NetworkMode.LOCALHOST
ID = -1
log.PRINT_LOG = False

# ___ GLOBAL VAR ___
network = None
buffer = queue.Queue()

#_________________________________ GET ARGS _________________________________

def usage():
    usage_text = f"usage : {sys.argv[0]} [agrs][option]\n"
    usage_text += f"\n ARGS :\n"
    usage_text += f" -i <id> \t id of the node in [1,255]\n"
    usage_text += f"\n OPTIONS :\n"
    usage_text += f" -m <mode> \t app mode in [sender, receiver, loopback]\n"
    usage_text += f" -n <mode> \t network mode in [adhoc, localhost]\n"
    usage_text += f" -l <value>\t enable log of infos [true,false] "
    return usage_text

def get_args():
    global ID
    global APP_MODE
    global NETWORK_MODE

    if (len(sys.argv) % 2) == 0:
        warnl("invalid args")
        print(usage())
        exit(1)
    
    for i in range(1,len(sys.argv),2):
        opt,value = sys.argv[i], sys.argv[i+1]
        if opt == "-i":
            ID = int(value)
        elif opt == "-m":
            if value == "sender":
                APP_MODE = AppMode.SENDER
            elif value == "receiver":
                APP_MODE = AppMode.RECEIVER
            elif value == "loopback":
                APP_MODE = AppMode.LOOPBACK
            else:
                exitl(f"invalid value for app mode : {value}")
        elif opt == "-n":
            if value == "adhoc":
                NETWORK_MODE = NetworkMode.ADHOC
            elif value == "localhost":
                NETWORK_MODE = NetworkMode.LOCALHOST
            else:
                exitl(f"invalid value for network mode : {value}")
        elif opt == "-l":
            if value == "true":
                log.PRINT_LOG = True
            elif value == "false":
                log.PRINT_LOG = False
            else:
                exitl(f"invalid value for network mode : {value}")
        else :
            exitl(f"invalid flag : {opt}")
    
    if ID < 0:
        print(usage())
        exitl("ID not specified (-i <id>)")
    if not (1 <= ID <= 255):
        exitl(f"invalid ID ({ID}), must be in [1,255]")

def display_args():
    global ID
    global APP_MODE
    global NETWORK_MODE

    print(f"APP_MODE : {APP_MODE}")
    print(f"NETWORK_MODE : {NETWORK_MODE}")
    print(f"ID : {ID}")
    print(f"log : {log.PRINT_LOG}")


#________________________________ GPS DEVICE ________________________________


def gps_simulator() :
    try:
        printl("start...")
        run_simulator()
    except:
        printl("[gps_simulator] Thread STOP...")

def gps_handler(buffer:queue.Queue):
    try:
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
    except:
        printl("[gps_handler] Thread STOP...")

def adhoc_sender(network:AdhocNetwork, buffer:queue.Queue):
    try:
        printl("start...")
        while True:
            pos = buffer.get()
            print(f"[gps_app.adhoc_sender] send pos \t : {pos}")
            pos = json.dumps(pos)
            network.broadcast(pos)
    except:
        printl("[adhoc_sender] Thread STOP...")

def adhoc_receiver(network:AdhocNetwork):
    try:
        printl("start...")
        while True:
            pos = network.read_data()
            (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
            pos = (fix, lat, lon, altitude)
            print(f"[gps_app.adhoc_receiver] received pos \t : {pos}")
    except:
        printl("[adhoc_receiver] Thread STOP...")


#__________________________________ MAIN __________________________________

get_args()
display_args()

network = AdhocNetwork(id=ID, localhost=(NETWORK_MODE == NetworkMode.LOCALHOST))
network.setup_adhoc()


p_gps_simulator = threading.Thread(target=gps_simulator)
p_gps_handler = threading.Thread(target=gps_handler, args=(buffer,))
p_adhoc_sender = threading.Thread(target=adhoc_sender, args=(network,buffer,))
p_adhoc_receiver = threading.Thread(target=adhoc_receiver, args=(network,))

p_gps_simulator.daemon = True
p_gps_handler.daemon = True
p_adhoc_sender.daemon = True
p_adhoc_receiver.daemon = True


threads_to_join = []

if APP_MODE == AppMode.SENDER :
    p_gps_simulator.start()
    sleep(1)
    p_gps_handler.start()
    p_adhoc_sender.start()
    
    threads_to_join.append(p_gps_simulator)
    threads_to_join.append(p_gps_handler)
    threads_to_join.append(p_adhoc_sender)
elif APP_MODE == AppMode.RECEIVER :
    p_adhoc_receiver.start()

    threads_to_join.append(p_adhoc_receiver)
elif APP_MODE == AppMode.LOOPBACK :
    p_gps_simulator.start()
    sleep(1)
    p_gps_handler.start()
    p_adhoc_sender.start()
    p_adhoc_receiver.start()

    threads_to_join.append(p_adhoc_receiver) 
    threads_to_join.append(p_gps_simulator)
    threads_to_join.append(p_gps_handler)
    threads_to_join.append(p_adhoc_sender)


try:
    for t in threads_to_join:
        t.join()
except KeyboardInterrupt as e:
    printl("Close app...")
    sys.exit(0)





