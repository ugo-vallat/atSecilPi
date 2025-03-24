import sys
import subprocess
import socket

from log import *


class AdhocNetwork:
    def __init__(self, id=1, local_host=False) :
        # netwrok
        if local_host:
            self._IP = f"127.0.0.1"
            self._MASK = "255.0.0.0"
            self._BROADCAST = "127.255.255.255"
        else :
            if not (1 <= id <= 255):
                exitl(f"invalid id : {id}")
            self._IP = f"192.168.1.{id}"
            self._MASK = "255.255.255.0"
            self._BROADCAST = "192.168.1.255"

        self._PORT = 5555
        self._SSID = "atsecilthebest"
        self._CHANNEL = 4
        self._INTERFACE = "wlan0"
        
        # other
        self.data_size_max = 2048


    def _run_cmd(self, cmd):
        printl(f" $ {cmd}")
        subprocess.run(cmd, shell=True, check=True)

    def setup_adhoc(self):
        try:
            # Stop NetworkManager
            self._run_cmd("sudo systemctl stop NetworkManager")

            # Configure self._INTERFACE in Ad-Hoc mode
            self._run_cmd(f"sudo ip link set {self._INTERFACE} down")
            self._run_cmd(f"sudo iwconfig {self._INTERFACE} mode ad-hoc")
            self._run_cmd(f"sudo iwconfig {self._INTERFACE} essid {self._SSID}")
            self._run_cmd(f"sudo iwconfig {self._INTERFACE} channel {self._CHANNEL}")
            self._run_cmd(f"sudo ip link set {self._INTERFACE} up")

            # Set static IP
            self._run_cmd(f"sudo ifconfig {self._INTERFACE} {self._IP} netmask {self._MASK} up")

            # Show config
            self._run_cmd(f"iwconfig {self._INTERFACE}")
            self._run_cmd(f"ifconfig {self._INTERFACE}")

            

        except subprocess.CalledProcessError as e:
            exitl(f"erreur commande : {e}")

    def broadcast(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')

        if len(data) > self.data_size_max :
            warnl(f"data size > {self.data_size_max}")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(data, (self._BROADCAST, self._PORT))


    def read_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self._PORT))

            printl(f"Listening on port {self._PORT}...")
            try:
                data, addr = s.recvfrom(self.data_size_max)
                data = data.decode('utf-8', errors='ignore')
                printl(f"Reçu de {addr[0]} : {data}")
                return data
            except Exception as e:
                warnl(f"Erreur lecture socket : {e}")
                return None


