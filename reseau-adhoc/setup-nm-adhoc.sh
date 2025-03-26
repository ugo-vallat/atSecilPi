#!/bin/bash

name="adhocAtSecil"
ip="192.168.1.1/24"
channel=6
interface="wlan0"
ssid="atsecilthebest"

echo "Vérification de l'interface Wi-Fi..."
if ! nmcli device status | grep -q "$interface"; then
    echo "Erreur : Interface $interface introuvable."
    exit 1
fi

echo "Désactivation temporaire du Wi-Fi..."
sudo nmcli radio wifi off
sleep 2  # Évite les conflits

echo "Suppression des anciennes connexions ($name)..."
sudo nmcli connection delete "$name" 2>/dev/null

echo "Création du réseau Ad-hoc ($ssid)..."
sudo systemctl start NetworkManager
sudo ip link set "$interface" up
sudo systemctl stop wpa_supplicant
sudo nmcli connection add type wifi ifname "$interface" con-name "$name" \
    ssid "$ssid" mode adhoc wifi.band bg wifi.channel "$channel" \
    ipv4.addresses "$ip" ipv4.method manual connection.autoconnect no

echo "Réactivation du Wi-Fi..."
sudo rfkill unblock wifi
sudo nmcli radio wifi on
sleep 2  # Stabilise la connexion

echo "Lancement de la connexion Ad-hoc ($name)..."
sudo nmcli connection up "$name"

echo "Réseau Ad-hoc '$ssid' actif avec IP $ip sur $interface."
nmcli device show "$interface"