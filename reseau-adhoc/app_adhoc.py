from time import sleep
import json
import sys


from libs.libnetwork import *
import libs.log as log

#_________________________________ VARS _________________________________

# ___ CONFIG VAR ___
ID = -1
IS_MASTER=None
log.PRINT_LOG = False

# ___ GLOBAL VAR ___
## Network
network = None
new_channel = -1

#_________________________________ GET ARGS _________________________________

def usage():
    usage_text = f"usage : {sys.argv[0]} [agrs][option]\n"
    usage_text += f"\n ARGS :\n"
    usage_text += f" -i <id> \t id of the node in [1,255]\n"
    usage_text += f" -m <value>\t master that scan the network [true,false] "
    usage_text += f"\n OPTIONS :\n"
    usage_text += f" -l <value>\t enable log of infos [true,false] "
    return usage_text

def get_args():
    global ID
    global IS_MASTER

    if (len(sys.argv) % 2) == 0:
        warnl("invalid args")
        print(usage())
        exit(1)
    
    for i in range(1,len(sys.argv),2):
        opt,value = sys.argv[i], sys.argv[i+1]
        if opt == "-i":
            ID = int(value)
        elif opt == "-m":
            if value == "true":
                IS_MASTER = True
            elif value == "false":
                IS_MASTER = False
            else:
                exitl(f"invalid value for master mode : {value}")
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

    if IS_MASTER is None:
        exitl("Master mode not specifiede (-m <value>)")

def display_args():
    global ID
    global IS_MASTER

    printl(f"ID : {ID}")
    printl(f"IS_MASTER : {IS_MASTER}")
    printl(f"log : {log.PRINT_LOG}")

def adhoc_sender(network:AdhocNetwork):
    global new_channel
    try:
        printl(f"Send new channel {new_channel}")
        ch = json.dumps(new_channel)
        for _ in range(3):
            network.broadcast(ch)
            sleep(0.5)
    except Exception as e:
        printl(f"failled with {e}")
        exit(1)
    finally:
        printl(f"channel sent")

def adhoc_receiver(network:AdhocNetwork):
    global new_channel
    try:
        printl("Waiting new channel...")
        msg = network.read_data()
        (new_channel) = json.loads(msg) # (fix, lat, lon, altitude)
        printl(f"Received new channel : {new_channel}")
    except Exception as e:
        printl(f"Failed with {e}")

#__________________________________ MAIN __________________________________

get_args()
display_args()

print("Setup adhoc network...")
network = AdhocNetwork(id=ID, localhost=False)
network.setup_adhoc()

if IS_MASTER:
    print("Scan netwrok...")
    new_channel = network.get_free_channel()
    adhoc_sender(network=network)
    network = AdhocNetwork(id=ID, localhost=False, channel=new_channel)
    sleep(1)
    print(f"Send hello to other nodes...")
    network.broadcast(f"Hello from master {ID}")
else:
    adhoc_receiver()
    network = AdhocNetwork(id=ID, localhost=False, channel=new_channel)
    msg = network.read_data()
    print(f"Received message : {msg}")

print("Close app...bye")




