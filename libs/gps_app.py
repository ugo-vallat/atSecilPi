from gps_simulator import *
from time import sleep
import threading
import queue
import json
import sys
from enum import Enum

import matplotlib.cm as cm
from colorist import ColorRGB
import numpy as np


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
DISPLAY = False

PATH_SIZE = 5
TRUE_SIZE = 10
SIZE = TRUE_SIZE *2

# ___ GLOBAL VAR ___
## Network
network = None
buffer = queue.Queue()
## Display
points = []
colors = []
grid = []
rainbow_colors = cm.rainbow(np.linspace(0, 1, 20))
rainbow_colors = np.delete(rainbow_colors, 3, axis=1 )
rainbow_colors = 255 * rainbow_colors

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

    printl(f"APP_MODE : {APP_MODE}")
    printl(f"NETWORK_MODE : {NETWORK_MODE}")
    printl(f"ID : {ID}")
    printl(f"log : {log.PRINT_LOG}")

#__________________________________ DISPLAY __________________________________

def rgb_color(color, text):
    r, g, b = color.astype(int)
    real_color = ColorRGB(r, g, b)

    colored_text = f"{real_color}{text}{real_color.OFF}"
    return colored_text


def create_grid():
    return [[" " for _ in range(SIZE)] for _ in range(SIZE)]

def print_grid(grid):
    print("       " + "   ".join( str(i+1) for i in range(TRUE_SIZE)))
    print("    +" + "----" * TRUE_SIZE + "+")

    for i, row in enumerate(grid):
        i = i+1
        if i%2 != 0 : 
            print("    |" + " ".join(row) + " |") 
        else : 
            print("{: >3d} |".format(int((i+1)/2)) + " ".join(row) + " |") 
    print("    +" + "----" * TRUE_SIZE + "+")

def clear_plot():
    global grid
    global SIZE
    for _ in range(SIZE+3):
        print("\033[F", end='')
        print("\033[K", end='')

    grid = create_grid()

def place_marker(grid, row, col, color, marker="O",):
    grid[row][col] = rgb_color(color, marker)


def display(fix, lat, lon, altitude):
    global points
    global colors
    global grid
    global PATH_SIZE

    if(fix > 0):
        
        clear_plot()

        points.append((lat, lon))
        colors.append(rainbow_colors[int(altitude*2)-1])

        if len(points) > PATH_SIZE : 
            points = list(np.delete(points, 0, axis=0))
            colors = list(np.delete(colors, 0, axis=0))
        
        for i, point in enumerate(points) : 
            lat =  int(point[0]*2)-1
            lon = int(point[1]*2)-1
            color = colors[i]
            if (i == len(points) -1):
                place_marker(grid,  lat, lon, color, "@")
            elif i == len(points) -1 or  i == len(points) -2 :
                place_marker(grid, lat, lon, color, "O")
            elif (i == 0) :
                place_marker(grid, lat, lon, color, ".")
            else :
                place_marker(grid, lat, lon, color, "o")
           

        print_grid(grid)

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
    global APP_MODE
    global DISPLAY
    try:
        printl("start...")
        while True:
            pos = buffer.get()
            if not DISPLAY:
                print(f"[gps_app.adhoc_sender] send pos \t : {pos}")
            pos = json.dumps(pos)
            network.broadcast(pos)
    except:
        printl("[adhoc_sender] Thread STOP...")

def adhoc_receiver(network:AdhocNetwork):
    global grid
    global DISPLAY
    try:
        printl("start...")
        if DISPLAY:
            grid = create_grid()
            print_grid(grid)
        while True:
            pos = network.read_data()
            (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
            pos = (fix, lat, lon, altitude)
            printl(f"[gps_app.adhoc_receiver] received pos \t : {pos}")
            if DISPLAY :
                display(fix, lat, lon, altitude)
    except:
        printl("[adhoc_receiver] Thread STOP...")

#__________________________________ MAIN __________________________________

get_args()
display_args()

if APP_MODE != AppMode.SENDER and not log.PRINT_LOG :
    DISPLAY = True

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





