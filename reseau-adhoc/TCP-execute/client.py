import socket
import json
import os
import argparse

local_ip = None
local_port = None
distant_ip = None
distant_port = None
file_to_send = None

def send_file_name(s, file_size) :
    data = json.dumps([local_ip, local_port, file_to_send, file_size])
    s.send(data.encode())
    
def send_file(s, file_size) :
    with open(file_to_send, "rb") as file :
        send_bytes = s.sendfile(file)
        if(send_bytes != file_size) :
            print("ERROR : filesize = ", file_size, " send_bytes = ", send_bytes)
            exit(1)

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

        (clientsocket, address) = serversocket.accept()
        return read_response(clientsocket)

def send_executable(file_size):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Connection to Socket ...")
        s.connect((distant_ip, distant_port))

        print("--Sending Connexion Informations...")
        send_file_name(s, file_size)

        print("--Waiting for server ack ...",  flush=True)
        if response_ok() :
            print("--Sending the file ...")
            send_file(s, file_size)
        else : 
            print("ERROR : server could not read file")

    print("--Connection to Socket Closed")

def send_command_instruction(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Connection to Socket ...")
        s.connect((distant_ip, distant_port))

        print("--Sending command instruction...")
        data = json.dumps([command])
        s.send(data.encode())

    print("--Connection to Socket Closed")


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
