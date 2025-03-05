import sys
import socket
import json
import os
import time

if len(sys.argv) != 6:
    print("Usage : client.py local_ip local_port distant_ip distant_port filename")
    sys.exit(0)


local_ip = sys.argv[1]
local_port = int(sys.argv[2])
distant_ip = sys.argv[3]
distant_port = int(sys.argv[4])
file_to_send = sys.argv[5]
try : 
    file_size = os.path.getsize(file_to_send)
except :
    print("ERROR : file " + file_to_send + "not found")
    exit(1)

def send_file_name(s, file_size) :
    data = json.dumps([local_ip, local_port, file_to_send, file_size])
    s.send(data.encode())
    
    print("Sending Connexion Informations...")

def send_file(s, file_size) :
    print("Sending the file ...")
    with open(file_to_send, "rb") as file :
        send_bytes = s.sendfile(file)
        if(send_bytes != file_size) :
            print("ERROR : filesize = ", file_size, " send_bytes = ", send_bytes)
            exit(1)
        print("Transmission success ! (Yay)")


def read_response(clientsocket):

    data = clientsocket.recv(1024)
    if data == b'':
        print("ERROR : Empty response given ! ")

    return bool(json.loads(data.decode()))


def response_ok():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('', local_port))
        serversocket.listen(10)

        print("Waiting for server connection response...",  flush=True)
        (clientsocket, address) = serversocket.accept()
        return read_response(clientsocket)

def send_executable():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Connection to Socket ...")
        s.connect((distant_ip, distant_port))
        
        send_file_name(s, file_size)

        if response_ok() :
            send_file(s, file_size)
        else : 
            print("ERROR : server could not read file")

        print("Connection to Socket Closed")
        

send_executable()