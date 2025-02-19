import sys
import socket
import json
import os

if len(sys.argv) != 5:
    print("Usage : server.py local_ip local_port distant_ip distant_port ")
    sys.exit(0)

file_to_send = "do_something.sh"
local_ip = sys.argv[1]
local_port = int(sys.argv[2])
distant_ip = sys.argv[2]
distant_port = int(sys.argv[3])

def send_file_name(file_size) :
    print("Sending the file name and size ...")

    data = json.dumps([file_to_send, file_size])
    s.send(data.encode())
    
    print("Sending complete")

def send_file(file_size) :
    print("Sending the file ...")
    with open(file_to_send, "rb") as file :
        send_bytes = s.sendfile(file)
        if(send_bytes != file_size) :
            print("ERROR : filesize = ", file_size, " send_bytes = ", send_bytes)
            exit(1)
        print("Transmission success ! (Yay)")

def send_executable():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print("Connection to Socket ...")
        s.connect((local_ip, port))

        file_size = os.path.getsize(file_to_send)
        
        send_file_name(file_size)
        send_file(file_size)

