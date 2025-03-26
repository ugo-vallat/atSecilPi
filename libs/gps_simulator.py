import time
import serial
import subprocess
import re
import os
import signal
from log import *
from libgps import *



def _init_simulator():
    # --- 1. Lancer socat pour créer deux pty connectés ---
    printl("Lancement de socat...")
    socat_proc = subprocess.Popen(
        ["socat", "-d", "-d", "pty,raw,echo=0", "pty,raw,echo=0"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    time.sleep(0.5)
    if socat_proc.poll() is not None :
        exitl("Failed to run socat (fix : install socat and run in sudo mode)")

    # --- 2. Lire les deux ports /dev/pts/N depuis la sortie de socat ---
    ports = []
    while len(ports) < 2:
        line = socat_proc.stdout.readline()
        print("[SOCAT]", line.strip())
        match = re.search(r"PTY is (/dev/pts/\d+)", line)
        if match:
            ports.append(match.group(1))

    # --- 3. Déterminer le port de lecture (le plus haut numéro) ---
    port_nums = [int(p.split("/")[-1]) for p in ports]
    read_port = ports[port_nums.index(max(port_nums))]
    write_port = ports[port_nums.index(min(port_nums))]

    printl(f"Port lecture (simulé par GPS réel) : {read_port}")
    printl(f"Port écriture (utilisé par ce script) : {write_port}")

    # --- 4. Créer le lien symbolique vers le port de lecture ---
    symlink_path = "/dev/ttyACM1_GPS"
    try:
        if os.path.exists(symlink_path) or os.path.islink(symlink_path):
            os.remove(symlink_path)
        printl(f"Check if {symlink_path} exist ? {os.path.exists(symlink_path)}")
        printl(f"Create {symlink_path}")   
        subprocess.run(["ln", "-s", read_port, symlink_path], check=True)
        printl(f"Check if {symlink_path} exist ? {os.path.exists(symlink_path)}")
        printl(f"Lien symbolique créé ? : {symlink_path} → {read_port}")
    except Exception as e:
        warnl(f"Impossible de créer le lien symbolique : {e}")
        socat_proc.terminate()
        exit(1)
    
    return socat_proc, write_port




def _send_data(socat_proc, write_port):
    pos = [(float(x),1.0,float(x)/2.0) for x in range(2,11)]
    pos = pos + [(10.0,float(x),float(x)/2.0 + 5.0) for x in range(2,11)]
    pos = pos + [(float(x),10.0,float(x)/2.0 + 5.0) for x in range(9,0,-1)]
    pos = pos + [(1.0,float(x),float(x)/2.0) for x in range(9,0,-1)]

    try:
        printl(f"Check if write_port {write_port} exist ? {os.path.exists(write_port)}")
        printl(f"Try ouverture port serie : {write_port}")
        with serial.Serial(write_port, 9600, timeout=1) as ser:
            printl(f"Envoi des trames GPS vers {write_port}...")
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
        printl(f"socat_proc poll: {socat_proc.poll()}")
        printl("Fermeture de socat...")
        socat_proc.send_signal(signal.SIGINT)
        socat_proc.wait()
        printl("Terminé proprement.")
    print(pos)



def run_simulator():
    socat_proc, write_port = _init_simulator()
    _send_data(socat_proc, write_port)


if __name__ == "__main__":
    run_simulator()    