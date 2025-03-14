import socket
import json
import os
import argparse
import time

local_ip = None
local_port = None
distant_ip = None
distant_port = None
file_to_send = None

MAX_LOOP = 100
WAITING_TIME=1

def send_file_name(s, file_size) :
    data = json.dumps([local_ip, local_port, file_to_send, file_size])
    s.send(data.encode())
    
def send_file(s, file_size, received_bytes) :
    with open(file_to_send, "rb") as file :
        send_bytes = s.sendfile(file, offset=received_bytes)
        if(send_bytes != file_size-received_bytes) :
            print("ERROR : filesize = ", file_size, " send_bytes = ", send_bytes)
            exit(1)
    

def receive_server_response():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('', local_port))
        serversocket.listen(10)
        serversocket.settimeout(3)

        try: 
            (clientsocket, address) = serversocket.accept()
            data = clientsocket.recv(1024)
            if data == b'':
                print("ERROR : Empty response given ! ")

            ack, received_bytes = json.loads(data.decode())
            return bool(ack), received_bytes
        except socket.timeout:
            print("ACK TIMEOUT")
            return False
    

# 
def send_executable(file_size):
    compt = 0
    received_bytes = 0
    send_complete = False

    while (received_bytes < file_size and compt < MAX_LOOP) : 
        try : 
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((distant_ip, distant_port))

                print("Requesting ack ...")
                send_file_name(s, file_size)

                ack, received_bytes = receive_server_response()
                print("---> Server ack received, it is waiting for ", file_size-received_bytes, " bytes",  flush=True)
                if ack and received_bytes != file_size :
                    print("Sending file bytes ...")
                    send_file(s, file_size, received_bytes)
        except :  
            print("---> Connexion Closed, trying to send again in ", WAITING_TIME, " seconds ...")
            compt += 1
            time.sleep(WAITING_TIME)

    if received_bytes == file_size : 
        print("---> Transmission Successful !")
    else : 
        print("---> Transmission Failure")

def send_command_instruction(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((distant_ip, distant_port))

        print("--Sending command instruction...")
        data = json.dumps([command])
        s.send(data.encode())
        print("---> command well send ! ")

def parse_file(file):
    global file_to_send
    global local_ip
    global local_port

    file_to_send = file
    local_port = 9000 + os.getpid()%1000

    try : 
        file_size = os.path.getsize(file_to_send)
    except :
        print("ERROR : file " + file_to_send + " not found")
        exit(1)

    send_executable(file_size)



def parse_command(command):
    command = (" ").join(command)
    send_command_instruction(command)



def parse_args():
    global distant_ip
    global distant_port
    global local_ip

    parser = argparse.ArgumentParser()
    parser.add_argument('local_ip', type=str)
    parser.add_argument('distant_ip', type=str)
    parser.add_argument('distant_port', type=int)
    parser.add_argument('-c', '--command', nargs='+', type=str, metavar=('command'))
    parser.add_argument('-f', '--file', type=str, metavar=('file_path'))

    args = parser.parse_args()
    local_ip = args.local_ip
    distant_ip = args.distant_ip
    distant_port = args.distant_port

    if(args.file) :
        parse_file(args.file)

    if(args.command) :
        parse_command(args.command)


parse_args()
