import serial.tools.list_ports
from libs.log import *

def list_serial_devices():
    """Liste tous les périphériques série connectés et tente d'identifier un module GPS."""
    devices = serial.tools.list_ports.comports()
        
    if not devices:
        exitl("device not detected")
    
    gps_device = None
    for port in devices:
        printl("Device :")
        printl(f" - Port : {port.device}\n - Description : {port.description}\n - Identifiant : {port.hwid}")

        if "GPS" in port.description:
            printl(" - GPS = YES")
            gps_device = port.device
        else :
            printl(" - GPS = NO")

    return gps_device

if __name__ == "__main__":
    list_serial_devices()
