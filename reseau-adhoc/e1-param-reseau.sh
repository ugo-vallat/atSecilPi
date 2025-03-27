#!/bin/bash

IFACE="wlan0"

# Informations détaillées sur les interfaces réseau
echo "Interfaces réseau actives :"
ip -br address
echo -e "\n+--------------------------------------------------+\n"

# Vérifie que l'interface existe
echo -n "Recherche interface $IFACE... "
if ! ip link show "$IFACE" &> /dev/null; then
    echo -e "\033[38;5;196mKO\033[0m"
    exit 1
fi
echo -e "\033[38;5;46mOK\033[0m"
echo -e "\n+--------------------------------------------------+\n"

# Infos générales sur l'interface
echo "État de l'interface $IFACE :"
iwconfig "$IFACE"
iwlist "$IFACE" channel | grep "Current Frequency"
echo -e "\n+--------------------------------------------------+\n"

# Canaux WiFi utilisés
echo "Liste des canaux disponnibles :"
iwlist  channel
echo -e "\n+--------------------------------------------------+\n"

# Scan des réseaux pour voir les canaux et interférences
echo "Scan des canaux wifi :"
sudo iwlist "$IFACE" scan | grep -E "Cell|Frequency|Quality|ESSID" | sed 's/^[ \t]*//'
echo -e "\n+--------------------------------------------------+\n"

# Statistiques TX/RX
echo "Statistiques de l'interface :"
cat /proc/net/dev 
echo -e "\n+--------------------------------------------------+\n"

# Taux de perte de paquets
echo "Taux de perte de paquets :"
ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'
echo -e "\n+--------------------------------------------------+\n"