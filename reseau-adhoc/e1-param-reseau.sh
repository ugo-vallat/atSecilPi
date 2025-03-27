#!/bin/bash

IFACE="wlan0"

# Informations détaillées sur les interfaces réseau
echo -e "Interfaces réseau actives :"
echo -e "\033[38;5;45m $ ip -br address\033[0m"
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
echo -e "État de l'interface $IFACE :"
echo -e "\033[38;5;45m $ iwconfig $IFACE; iwlist $IFACE channel | grep Current Frequency \033[0m"
iwconfig "$IFACE"
iwlist "$IFACE" channel | grep "Current Frequency"
echo -e "\n+--------------------------------------------------+\n"

# Canaux WiFi utilisés
echo -e "Liste des canaux disponnibles :"
echo -e "\033[38;5;45m $ \033[0m"
iwlist  channel
echo -e "\n+--------------------------------------------------+\n"

# Scan des réseaux pour voir les canaux et interférences
echo -e "Scan des canaux wifi :"
echo -e "\033[38;5;45m $ sudo iwlist $IFACE scan | grep -E Cell|Frequency|Quality|ESSID \033[0m"
sudo iwlist "$IFACE" scan | grep -E "Cell|Frequency|Quality|ESSID" | sed 's/^[ \t]*//'
echo -e "\n+--------------------------------------------------+\n"

# Statistiques TX/RX
echo -e "Statistiques de l'interface :"
echo -e "\033[38;5;45m $ cat /proc/net/dev \033[0m"
cat /proc/net/dev 
echo -e "\n+--------------------------------------------------+\n"

# Taux de perte de paquets
echo -e "Taux de perte de paquets :"
echo -e "\033[38;5;45m $ ping -c 10 google.com | grep -oP '\d+(?=% packet loss)' \033[0m"
ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'
echo -e "\n+--------------------------------------------------+\n"