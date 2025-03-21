import serial.tools.list_ports
import serial
from log import *


def get_gps_device():
    """Liste tous les périphériques série connectés et tente d'identifier un module GPS."""
    devices = serial.tools.list_ports.comports()
        
    if not devices:
        exitl("device not detected")
    
    gps_device = None
    for port in devices:
        print("Device :")
        print(f" - Port : {port.device}\n - Description : {port.description}\n - Identifiant : {port.hwid}")

        if "GPS" in port.description:
            print(f" - GPS = {COK}YES{CRST}")
            gps_device = port.device
        else :
            print(f" - GPS = {CKO}NO{COK}")

    if gps_device is None:
        exitl("No gps device found")
    return gps_device

def read_raw_gps_data(gps_port, baudrate=9600, timeout=2):
    """
    Lit et affiche en continu les données brutes envoyées par le module GPS.
    
    :param gps_port: Port série où est connecté le module GPS (ex: '/dev/ttyUSB0' ou 'COM3')
    :param baudrate: Débit en bauds du module GPS (par défaut 9600)
    :param timeout: Temps d'attente avant expiration de la lecture
    """
    try:
        with serial.Serial(gps_port, baudrate, timeout=timeout) as ser:
            print(f"\nLecture des données brutes du GPS sur {gps_port}...\n(CTRL+C pour arrêter)\n")
            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:  # Affiche seulement si une ligne est reçue
                    print(line)
    except serial.SerialException as e:
        warnl("Failed to connect to serial port")
    except KeyboardInterrupt:
        print("\n🚪 Arrêt de la lecture des données GPS.")

if __name__ == "__main__":
    gps_port = get_gps_device()
    read_raw_gps_data(gps_port)

