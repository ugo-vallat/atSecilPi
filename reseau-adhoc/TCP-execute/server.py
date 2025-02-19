import sys
import socket
import json

if len(sys.argv) != 5:
    print("Usage : server.py local_ip local_port distant_ip distant_port ")
    sys.exit(0)

local_ip = sys.argv[1]
local_port = int(sys.argv[2])
distant_ip = sys.argv[2]
distant_port = int(sys.argv[3])

file_to_send = "do_something.sh"

def get_file_infos(clientsocket):
    data = ''
    while True:
        tmp = clientsocket.recv(1024)
        if tmp == b'':
            break
        data += tmp.decode()
    file_name, file_size = json.loads(data)
    return file_name, file_size

def write_file(clientsocket, file_name, file_size):
    
    with open(file_name, "w+") as new_file :
        while True:
            tmp = clientsocket.recv(1024)
            if tmp == b'':
                break
            new_file.write(tmp) # tmp.decode()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('', local_port))
        serversocket.listen(10)

        while True :
            (clientsocket, address) = serversocket.accept()
            file_name, file_size = get_file_infos(clientsocket)
            write_file(clientsocket, file_name, file_size)