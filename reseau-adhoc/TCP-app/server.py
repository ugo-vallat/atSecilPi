import sys
import socket
import json
import argparse
import subprocess
import time

class Client() :
    def __init__(self, file_name : str, file_size : int, received_bytes : int = 0):
        self.file_name = file_name
        self.file_size = file_size
        self.received_bytes = received_bytes

file_directory_path = "./received_inst/"
memory_buffer = {}

def get_file_infos(clientsocket):
    data = ''
    time.sleep(0.5)
    tmp = clientsocket.recv(1024)
    data = tmp.decode()
    return json.loads(data)

def write_file(clientsocket, client : Client):
    
    try : 
        subprocess.check_call("chmod 777 " + client.file_name, shell=True) # verify for rasberry
        with open(file_directory_path + client.file_name, "wb") as new_file :
            try : 
                while True:
                    tmp = clientsocket.recv(min(client.file_size, 1024))
                    #clientsocket.close()
                    if tmp == b'':
                        break
                    new_file.write(tmp)
                    client.received_bytes += len(tmp)
            except : 
                pass
    except subprocess.CalledProcessError as e:
        print(e.returncode, flush=True)
        if e.returncode == 126 :
            print("No permission to give execution mode on file. Be sure to be in sudo mode")
            print("The file could not be received")

def append_file(clientsocket, client : Client):
    
    with open(file_directory_path + client.file_name, "ab") as new_file :
        try : 
            while True:
                tmp = clientsocket.recv(min(client.file_size, 1024))
                if tmp == b'':
                    break
                new_file.write(tmp)
                #clientsocket.close()
                client.received_bytes += len(tmp)
        except : 
            pass


def send_ack(distant_ip, distant_port, ack, received_bytes):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.connect((distant_ip, distant_port))

        data = json.dumps([ack, received_bytes])
        s.send(data.encode())

def receive_file(clientsocket, distant_ip, distant_port, file_name, file_size):
    global memory_buffer

    peer = clientsocket.getpeername()[0]
    if peer not in memory_buffer :
        print("---> Adding a new Client : ", peer , " with file ", file_name)
        memory_buffer[peer] = Client(file_name, file_size)
    
    if  memory_buffer[peer].file_name != file_name or memory_buffer[peer].file_size != file_size : 
        memory_buffer[peer].file_name = file_name
        memory_buffer[peer].file_size = file_size
        memory_buffer[peer].received_bytes = 0

    print("Sending ack ...")
    send_ack(distant_ip, distant_port, True, memory_buffer[peer].received_bytes)

    if  memory_buffer[peer].received_bytes != memory_buffer[peer].file_size : 
        if memory_buffer[peer].received_bytes > 0 and  memory_buffer[peer].received_bytes != memory_buffer[peer].file_size :
            print("Append content to existing file ...")
            append_file(clientsocket, memory_buffer[peer])
        else :
            print("Receiving file content ... ")
            write_file(clientsocket, memory_buffer[peer])


def execute_command(command):
    print("Executing command : " + command + " ....")
    try :
        subprocess.check_call(command, shell=True)
        print("---> command executed successfully !")
    except subprocess.CalledProcessError as e:
        if e.returncode == 127 : 
            print("---> command failure")
            print("be sure that the file on server side is located inside the directory " + file_directory_path + " in the command.")
    

def listening_loop(local_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as serversocket:
            serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serversocket.bind(('', local_port))
            serversocket.listen(10)

            while True :
                print("Waiting for connection requests ...",  flush=True)
                (clientsocket, address) = serversocket.accept()

                print("---> Connection request received, decoding the connexion data ...")
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
    global local_port

    parser = argparse.ArgumentParser()
    parser.add_argument('local_port', type=int)
    args = parser.parse_args()
    local_port = args.local_port

    listening_loop(local_port)


parse_args()