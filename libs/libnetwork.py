import sys
import subprocess
import socket
from time import sleep
from libs.log import *


class AdhocNetwork:
    def __init__(self, id=1, localhost=False, port=5555, ssid="atsecilthebest", channel=1) :
        # netwrok
        self.localhost = localhost
        if localhost:
            self._IP = f"127.0.0.1"
            self._MASK = "255.0.0.0"
            self._BROADCAST = "127.255.255.255"
        else :
            if not (1 <= id <= 255):
                exitl(f"invalid id : {id}")
            self._IP = f"192.168.2.{id}"
            self._MASK = "255.255.255.0"
            self._BROADCAST = "192.168.2.255"

        self._PORT = port
        self._SSID = ssid
        self._CHANNEL = channel
        self._INTERFACE = "wlan0"
        
        # other
        self.data_size_max = 2048


    def _run_cmd(self, cmd):
        printl(f" $ {cmd}")
        subprocess.run(cmd, shell=True, check=True)

    def setup_adhoc(self):
        if self.localhost :
            printl("Network in localhost mode, ignore setup_hadoc")
            return
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

    def _get_available_channels(self):
        """Récupère la liste des canaux disponibles avec iwlist channel"""
        result = subprocess.run(
            ["iwlist", self._INTERFACE, "channel"],
            capture_output=True,
            text=True
        )
        
        channels = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Channel") and ":" in line:
                try:
                    channel = int(line.split()[1])
                    if channel not in channels:
                        channels.append(channel)
                except ValueError:
                    continue

        return sorted(channels)

    def _scan_network(self, channels):
        """
        Effectue un scan WiFi unique et compte le nombre de réseaux par canal.
        Retourne une liste de tuples : (nombre_reseaux, channel)
        """
        # Scan complet des réseaux visibles
        result = subprocess.run(
            ["sudo","iwlist",self._INTERFACE,"scan"],
            capture_output=True,
            text=True
        )
        sleep(5)
        scan_output = result.stdout
        printl(f"Scan output : {scan_output}")
        channel_counts = []

        for ch in channels:
            count = scan_output.count(f"Channel:{ch}")
            channel_counts.append((count,ch))

        return channel_counts


    def get_free_channel(self):
        """
        Renvoie le canal disponible avec le moins de réseaux détectés.
        S'il y a plusieurs canaux ex æquo, retourne le premier dans la liste triée.
        """
        available_channels = self._get_available_channels()
        printl(f"Available channels : {available_channels}")
        scan_results = self._scan_network(available_channels)
        printl(f"Scan result (nb_network, channel) : {scan_results}")

        if not scan_results:
            return None

        # Trie les résultats par nombre de réseaux (croissant), puis par numéro de canal (croissant)
        scan_results.sort()

        # retourne le premier de la liste
        return scan_results[0][1]

        
