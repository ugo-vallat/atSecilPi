import sys
import socket
import json
import argparse
import subprocess

local_ip = sys.argv[1]
local_port = int(sys.argv[2])

file_directory_path = "./received_instructions/"

def get_file_infos(clientsocket):
    data = ''

    tmp = clientsocket.recv(1024)
    data = tmp.decode()

    return json.loads(data)

def write_file(clientsocket, file_name, file_size):
    
    with open(file_directory_path + file_name, "wb") as new_file :
        while True:
            tmp = clientsocket.recv(min(file_size, 1024))
            if tmp == b'':
                break
            new_file.write(tmp)


def send_ack(distant_ip, distant_port, ack):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.connect((distant_ip, distant_port))

        data = json.dumps([ack])
        s.send(data.encode())

def receive_file(clientsocket, distant_ip, distant_port, file_name, file_size):

    print("--Sending ack ...")
    send_ack(distant_ip, distant_port, True)

    print("--Receiving file content ... ")
    write_file(clientsocket, file_name, file_size)

def execute_command(command):
    print("-- Executing command : " + command)
    subprocess.Popen(command, shell=True)

def listening_loop():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serversocket.bind(('', local_port))
            serversocket.listen(10)

            while True :
                print("Waiting for connection requests ...",  flush=True)
                (clientsocket, address) = serversocket.accept()

                print("--Connection request received, decoding the connexion data ...")
                infos = get_file_infos(clientsocket)
                match len(infos):

                    case 1 : 
                        execute_command(infos[0])
                    case 4 : 
                        receive_file(clientsocket, infos[0], infos[1], infos[2], infos[3])
                    case _ : 
                        print("ERROR : websocket connexion data does not match usage ")
                        print("usage1: command ")
                        print("usage2: local_ip, local_port, file_to_send, file_size ")


def parse_args():
    global local_ip
    global local_port

    parser = argparse.ArgumentParser()
    parser.add_argument('local_ip', type=str)
    parser.add_argument('local_port', type=int)
    args = parser.parse_args()
    local_ip = args.local_ip
    local_port = args.local_port

    listening_loop()


parse_args()  
