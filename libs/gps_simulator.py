import time
import serial
import subprocess
import re
import os
import signal
from libs.log import *
from libs.libgps import *


class GPS_Simulator:

    def __init__(self):
        self.socat_proc = None
        self.write_port = None
        self.symlink_path = "/dev/ttyACM1_GPS"

    def init_simulator(self):
        # --- 1. Lancer socat pour créer deux pty connectés ---
        printl("Lancement de socat...")
        self.socat_proc = subprocess.Popen(
            ["socat", "-d", "-d", "pty,raw,echo=0", "pty,raw,echo=0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        time.sleep(0.5)
        if self.socat_proc.poll() is not None :
            exitl("Failed to run socat (fix : install socat and run in sudo mode)")

        # --- 2. Lire les deux ports /dev/pts/N depuis la sortie de socat ---
        ports = []
        while len(ports) < 2:
            line = self.socat_proc.stdout.readline()
            print("[SOCAT]", line.strip())
            match = re.search(r"PTY is (/dev/pts/\d+)", line)
            if match:
                ports.append(match.group(1))

        # --- 3. Déterminer le port de lecture (le plus haut numéro) ---
        port_nums = [int(p.split("/")[-1]) for p in ports]
        read_port = ports[port_nums.index(max(port_nums))]
        self.write_port = ports[port_nums.index(min(port_nums))]

        printl(f"Port lecture (simulé par GPS réel) : {read_port}")
        printl(f"Port écriture (utilisé par ce script) : {self.write_port}")

        # --- 4. Créer le lien symbolique vers le port de lecture ---
        try:
            if os.path.exists(self.symlink_path) or os.path.islink(self.symlink_path):
                os.remove(self.symlink_path)
            printl(f"Check if {self.symlink_path} exist ? {os.path.exists(self.symlink_path)}")
            printl(f"Create {self.symlink_path}")   
            subprocess.run(["ln", "-s", read_port, self.symlink_path], check=True)
            printl(f"Check if {self.symlink_path} exist ? {os.path.exists(self.symlink_path)}")
            printl(f"Lien symbolique créé ? : {self.symlink_path} → {read_port}")
        except Exception as e:
            warnl(f"Impossible de créer le lien symbolique : {e}")
            self.socat_proc.terminate()
            exit(1)



    def run_simulator(self):
        pos = [(float(x),1.0,float(x)/2.0) for x in range(2,11)]
        pos = pos + [(10.0,float(x),float(x)/2.0 + 5.0) for x in range(2,11)]
        pos = pos + [(float(x),10.0,float(x)/2.0 + 5.0) for x in range(9,0,-1)]
        pos = pos + [(1.0,float(x),float(x)/2.0) for x in range(9,0,-1)]

        try:
            printl(f"Check if write_port {self.write_port} exist ? {os.path.exists(self.write_port)}")
            printl(f"Try ouverture port serie : {self.write_port}")
            ser = serial.Serial(self.write_port, 9600, timeout=1)
            printl(f"Serial port open : {ser}")
            printl(f"Envoi des trames GPS vers {self.write_port}...")
            while True:
                for coord in pos :
                    gga = gps_coord_to_gga(2,coord[0], coord[1], coord[2])
                    ser.write(gga.encode())
                    # printl(f"send {gga}")
                    time.sleep(1)
        except serial.SerialException as e:
            warnl(f"Erreur ouverture port série : {e}")
        except Exception as e:
            warnl(f"Erreur inattendue dans _send_data: {e}")
            import traceback
            warnl(traceback.format_exc())
        finally:
            printl(f"socat_proc poll: {self.socat_proc.poll()}")
            printl("Fermeture de socat...")
            self.socat_proc.send_signal(signal.SIGINT)
            self.socat_proc.wait()
            printl("Terminé proprement.")



if __name__ == "__main__":
    sim = GPS_Simulator()
    sim.init_simulator()
    sim.run_simulator()
