#!/bin/bash

IP="192.168.1.2"
MASK="255.255.255.0"
SSID="atsecilthebest"
CHANNEL=4

# Désactiver le service DHCP pour éviter les conflits
sudo systemctl stop NetworkManager
sudo systemctl stop dhcpcd
sudo systemctl disable dhcpcd

# Configurer l'interface WiFi en mode Adhoc
sudo ip link set wlan0 down  # Désactiver temporairement l'interface
sudo iwconfig wlan0 mode ad-hoc  # Passer en mode Adhoc
sudo iwconfig wlan0 essid $(SSID)  # Définir le SSID
sudo iwconfig wlan0 channel $(CHANNEL)  # Définir le canal 4 (2.427 GHz)
sudo ip link set wlan0 up  # Réactiver l'interface

# Assigner une adresse IP statique
sudo ifconfig wlan0 $(IP) netmask $(MASK) up

# Vérifier la configuration du WiFi
iwconfig wlan0
ifconfig wlan0

# Activer le service réseau pour appliquer la configuration au redémarrage
echo -e "interface wlan0\nstatic ip_address=XXX.XXX.XXX.1/24\nnohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf

# Redémarrer le service réseau pour appliquer les modifications
sudo systemctl restart networking
sudo systemctl restart dhcpcd

echo "Configuration Adhoc terminée. Vérifiez avec 'iwconfig' et 'ifconfig'."
