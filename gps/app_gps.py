from libs.gps_simulator import *
from time import sleep
import threading
import queue
import json
import sys
from enum import Enum

import matplotlib.cm as cm
from colorist import ColorRGB
import numpy as np


from libs.libgps import *
from libs.libnetwork import *
import libs.log as log

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
ID = -1
APP_MODE = AppMode.LOOPBACK
NETWORK_MODE = NetworkMode.LOCALHOST
ENABLE_SIMU_GPS = True
ENABLE_DISPLAY = False
log.PRINT_LOG = False

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
    usage_text += f" -s <value>\t enable gps simulator [true,false] "
    usage_text += f"\n OPTIONS :\n"
    usage_text += f" -m <mode> \t app mode in [sender, receiver, loopback]\n"
    usage_text += f" -n <mode> \t network mode in [adhoc, localhost]\n"
    usage_text += f" -l <value>\t enable log of infos [true,false]\n"
    usage_text += f" -d <value>\t enable display [true,false] (only if using gps simulator)"
    return usage_text

def get_args():
    global ID
    global APP_MODE
    global NETWORK_MODE
    global ENABLE_SIMU_GPS
    global ENABLE_DISPLAY

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
        elif opt == "-s":
            if value == "true":
                ENABLE_SIMU_GPS = True
            elif value == "false":
                ENABLE_SIMU_GPS = False
            else:
                exitl(f"invalid value for gps simulator : {value}")
        elif opt == "-d":
            if value == "true":
                ENABLE_DISPLAY = True
            elif value == "false":
                ENABLE_DISPLAY = False
            else:
                exitl(f"invalid value for display : {value}")
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

#__________________________________ ENABLE_DISPLAY __________________________________

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


def gps_simulator(simu:GPS_Simulator) :
    try:
        printl("start...")
        simu.run_simulator()
    except:
        printl("Thread STOP...")

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
        printl("Thread STOP...")

def network_sender(network:AdhocNetwork, buffer:queue.Queue):
    global ENABLE_DISPLAY
    try:
        printl("start...")
        while True:
            pos = buffer.get()
            if not ENABLE_DISPLAY:
                print(f"send pos \t : {pos}")
            pos = json.dumps(pos)
            network.broadcast(pos)
    except:
        printl("Thread STOP...")

def network_receiver(network:AdhocNetwork):
    global grid
    global ENABLE_DISPLAY
    try:
        printl("start...")
        if ENABLE_DISPLAY:
            grid = create_grid()
            print_grid(grid)
        while True:
            pos = network.read_data()
            (fix, lat, lon, altitude) = json.loads(pos) # (fix, lat, lon, altitude)
            pos = (fix, lat, lon, altitude)
            printl(f"received pos \t : {pos}")
            if ENABLE_DISPLAY :
                display(fix, lat, lon, altitude)
    except:
        printl("Thread STOP...")

#__________________________________ MAIN __________________________________

# Récupération des arguments
get_args()

# Vérification de la configuration
if log.PRINT_LOG and ENABLE_DISPLAY :
    exitl("Can't enable logger and display at the same time")


threads_to_join = []

# Initialisation du Simulateur GPS
if ENABLE_SIMU_GPS:
    print("Start GPS Simulator...")
    simu = GPS_Simulator()
    simu.init_simulator()
    p_gps_simulator = threading.Thread(target=gps_simulator, args=(simu,))
    p_gps_simulator.daemon = True
    threads_to_join.append(p_gps_simulator)
    p_gps_simulator.start()

# Initialisation du réseau
print("Init network...")
network = AdhocNetwork(id=ID, localhost=(NETWORK_MODE == NetworkMode.LOCALHOST))
if NETWORK_MODE == NetworkMode.ADHOC:
    network.setup_adhoc()

# Lancement threads handler et sender
if APP_MODE in [AppMode.SENDER, AppMode.LOOPBACK]:
    print("Start gps handler...")
    p_gps_handler = threading.Thread(target=gps_handler, args=(buffer,))
    p_gps_handler.daemon = True
    threads_to_join.append(p_gps_handler)
    p_gps_handler.start()

    print("Start network sender...")
    p_network_sender = threading.Thread(target=network_sender, args=(network,buffer,))
    p_network_sender.daemon = True
    threads_to_join.append(p_network_sender)
    p_network_sender.start()

# Lancement thread receiver
if APP_MODE in [AppMode.RECEIVER, AppMode.LOOPBACK]:
    print("Start network receiver...")
    p_network_receiver = threading.Thread(target=network_receiver, args=(network,))
    p_network_receiver.daemon = True
    threads_to_join.append(p_network_receiver)
    p_network_receiver.start()

# Récupération des threads morts
try:
    for t in threads_to_join:
        t.join()
except KeyboardInterrupt as e:
    printl("Close app...")
    sys.exit(0)





