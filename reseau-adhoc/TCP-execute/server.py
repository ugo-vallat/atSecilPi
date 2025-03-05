import sys
import socket
import json

if len(sys.argv) != 3:
    print("Usage : server.py local_ip local_port")
    sys.exit(0)

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


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('', local_port))
        serversocket.listen(10)

        while True :
            print("Waiting for connection requests ...",  flush=True)
            (clientsocket, address) = serversocket.accept()

            print("Connection request received, decoding of connexion data ...")
            distant_ip, distant_port, file_name, file_size = get_file_infos(clientsocket)

            print("Sending ack ...")
            send_ack(distant_ip, distant_port, True)

            print("Receiving file content ... ")
            write_file(clientsocket, file_name, file_size)
