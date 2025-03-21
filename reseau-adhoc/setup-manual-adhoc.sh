#!/bin/bash

if [[ -z "$1" || "$1" -lt 1 || "$1" -gt 255 ]]; then
  echo "Usage: $0 <ID (1-255)>"
  exit 1
fi

ID=$1
IP="192.168.1.${ID}"
MASK="255.255.255.0"
SSID="atsecilthebest"
CHANNEL=4

# Désactiver le service DHCP pour éviter les conflits
## V1 : Stop NetworkManager
sudo systemctl stop NetworkManager    

## V2 : Unmanage wlan0 for NetworkManager
# sudo nmcli dev set wlan0 managed no

# Configurer l'interface WiFi en mode Adhoc
sudo ip link set wlan0 down  # Désactiver temporairement l'interface
sudo iwconfig wlan0 mode ad-hoc  # Passer en mode Adhoc
sudo iwconfig wlan0 essid $SSID  # Définir le SSID
sudo iwconfig wlan0 channel $CHANNEL  # Définir le canal 4 (2.427 GHz)
sudo ip link set wlan0 up  # Réactiver l'interface

# Assigner une adresse IP statique
sudo ifconfig wlan0 $IP netmask $MASK up

# Vérifier la configuration du WiFi
iwconfig wlan0
ifconfig wlan0

# Activer le service réseau pour appliquer la configuration au redémarrage
# echo -e "interface wlan0\nstatic ip_address=$IP/24\nnohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf

# Redémarrer le service réseau pour appliquer les modifications

echo "Config Done"
