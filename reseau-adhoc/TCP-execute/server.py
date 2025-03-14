import sys
import socket
import json
import argparse
import subprocess

file_directory_path = "./received_inst/"

def get_file_infos(clientsocket):
    data = ''

    tmp = clientsocket.recv(1024)
    data = tmp.decode()

    return json.loads(data)

def write_file(clientsocket, file_name, file_size):
    
    try : 
        subprocess.check_call("chmod 777 " + file_name, shell=True)
        with open(file_directory_path + file_name, "wb") as new_file :
            while True:
                tmp = clientsocket.recv(min(file_size, 1024))
                if tmp == b'':
                    break
                new_file.write(tmp)
    except subprocess.CalledProcessError as e:
        print(e.returncode, flush=True)
        if e.returncode == 126 :
            print("No permission to give execution mode on file. Be sure to be in sudo mode")
            print("The file could not be received")


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
    try : #before: Popen(command, shell=True)
        subprocess.check_call(command, shell=True)
        print("command executed successfully !")
    except subprocess.CalledProcessError as e:
        if e.returncode == 127 : 
            print("be sure that the file on server side is located inside the directory " + file_directory_path + " in the command.")
    


def listening_loop(local_port):
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
    global local_port

    parser = argparse.ArgumentParser()
    parser.add_argument('local_port', type=int)
    args = parser.parse_args()
    local_port = args.local_port

    listening_loop(local_port)


parse_args()