import serial.tools.list_ports
import serial
from datetime import datetime
from log import *

#________________________________ GPS DEVICE ________________________________

def gps_get_device():
    """Liste tous les périphériques série connectés et tente d'identifier un module GPS."""
    devices = serial.tools.list_ports.comports()
        
    if not devices:
        exitl("device not detected")
    
    gps_device = None
    for port in devices:
        print("Device :")
        print(f" - Port : {port.device}\n - Description : {port.description}\n - Identifiant : {port.hwid}")

        if "GPS" in port.description or "GPS" in port.device:
            print(f" - GPS = {COK}YES{CRST}")
            gps_device = port.device
        else :
            print(f" - GPS = {CKO}NO{COK}")

    if gps_device is None:
        exitl("No gps device found")
    return gps_device

def gps_read_trame(gps_port, baudrate=9600, timeout=2):
    """
    Lit et retourne une trame NMEA depuis le port série du module GPS.
    
    :param gps_port: Port série (ex: '/dev/ttyUSB0' ou 'COM3')
    :param baudrate: Baudrate du module GPS (par défaut 9600)
    :param timeout: Timeout de lecture en secondes
    :return: Une ligne NMEA (str) ou None si erreur
    """
    line = None
    try:
        with serial.Serial(gps_port, baudrate, timeout=timeout) as ser:
            while not line:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
        return line
    except serial.SerialException as e:
        warnl("Failed to connect to serial port")
    return line

#________________________________ TRAMES GGA ________________________________

def _decimal_degrees_to_nmea(coord, is_latitude=True):
    """
    Convertit une coordonnée en degrés décimaux au format NMEA GGA.
    Ex: 48.1173 -> '4807.038', 'N'
    """
    direction = ''
    if is_latitude:
        direction = 'N' if coord >= 0 else 'S'
    else:
        direction = 'E' if coord >= 0 else 'W'

    coord = abs(coord)
    degrees = int(coord)
    minutes = (coord - degrees) * 60

    if is_latitude:
        nmea_coord = f"{degrees:02d}{minutes:06.3f}"
    else:
        nmea_coord = f"{degrees:03d}{minutes:06.3f}"

    return nmea_coord, direction

def _nmea_to_decimal_degrees(value, direction):
    """
    Convertit un format NMEA (ddmm.mmm ou dddmm.mmm) en degrés décimaux
    """
    if not value:
        return None
    degrees_len = 2 if direction in ['N', 'S'] else 3
    degrees = int(value[:degrees_len])
    minutes = float(value[degrees_len:])
    decimal = degrees + minutes / 60
    return decimal if direction in ['N', 'E'] else -decimal


def _calculate_checksum(nmea_str):
    """Calcule le checksum d'une trame NMEA (sans le $ et sans le *)."""
    checksum = 0
    for c in nmea_str:
        checksum ^= ord(c)
    return f"{checksum:02X}"

def gps_coord_to_gga(fix, latitude, longitude, altitude):
    """
    Converti des coordonnées en trame GGA
    """
    # Heure actuelle UTC au format hhmmss
    time_utc = datetime.utcnow().strftime("%H%M%S")

    if fix == 0:
        # Trame vide (pas de position)
        body = f"GPGGA,{time_utc},,,,,0,00,1.0,,M,,M,,"
    else:
        lat_str, lat_dir = _decimal_degrees_to_nmea(latitude, is_latitude=True)
        lon_str, lon_dir = _decimal_degrees_to_nmea(longitude, is_latitude=False)
        # Valeurs arbitraires pour les champs manquants
        nb_satellites = 8
        hdop = 0.9
        geoid_height = 46.9

        body = f"GPGGA,{time_utc},{lat_str},{lat_dir},{lon_str},{lon_dir},{fix},{nb_satellites:02d},{hdop:.1f},{altitude:.1f},M,{geoid_height:.1f},M,,"

    checksum = _calculate_checksum(body)
    trame = f"${body}*{checksum}\n"
    return trame

def gps_gga_to_coord(trame):
    """
    Converti une trame GGA en coordonées
    """
    if not trame.startswith('$') or '*' not in trame:
        return None

    body, checksum = trame[1:].split('*')
    if _calculate_checksum(body) != checksum.upper():
        return None

    parts = body.split(',')
    if parts[0] != 'GPGGA':
        return None

    fix = int(parts[6])
    if fix == 0:
        return (0, None, None, None)

    lat = _nmea_to_decimal_degrees(parts[2], parts[3])
    lon = _nmea_to_decimal_degrees(parts[4], parts[5])
    altitude = float(parts[9]) if parts[9] else None

    return (fix, lat, lon, altitude)

