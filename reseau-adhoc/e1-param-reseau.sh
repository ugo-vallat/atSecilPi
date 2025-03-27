#!/bin/bash

IFACE="wlan0"

# Vérifie que l'interface existe
if ! ip link show "$IFACE" &> /dev/null; then
    echo "Interface $IFACE non trouvée"
    exit 1
fi

# Infos générales sur l'interface
echo "État de l'interface $IFACE :"
iwconfig "$IFACE"
echo ""

# Scan des réseaux pour voir les canaux et interférences
echo "Scan des réseaux WiFi (canaux et qualité) :"
sudo iwlist "$IFACE" scan | grep -E "Cell|Frequency|Quality|ESSID" | sed 's/^[ \t]*//'
echo ""

# Affichage du canal actuel
echo "Canal utilisé par $IFACE :"
iwlist "$IFACE" channel | grep "Current Frequency"
echo ""

# Informations détaillées sur les interfaces réseau
echo "Interfaces réseau actives :"
ip -br address
echo ""

# Statistiques TX/RX
echo "Statistiques de l'interface :"
cat /proc/net/dev 
echo ""

#----------------------------------------------------------------------

# Canaux WiFi utilisés
echo "Canaux WiFi utilisés :"
iwlist  channel
echo ""

# Interférences WiFi (Autres réseaux sur le même canal)
echo "Interférences WiFi (Autres réseaux sur le même canal) :"
iwlist wlan0 scan | grep -E "Channel|ESSID"
echo ""

# Taux de perte de paquets
echo "Taux de perte de paquets :"
ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'
echo ""