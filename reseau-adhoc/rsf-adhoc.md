
# Étape 1 
- Canaux WiFi utilisés : `iwlist wlan0 channel`
- Interférences WiFi (Autres réseaux sur le même canal) : `iwlist wlan0 scan | grep -E "Channel|ESSID"`
- Taux de perte de paquets : `ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'`


# Configuration d'un réseau Adhoc sur Raspberry Pi  

## Comment ça marche ?  

1. **Mode Adhoc**  
   - Contrairement au mode **Infrastructure** (utilisé pour les réseaux WiFi classiques), le mode **Adhoc** permet aux appareils de se connecter directement, sans passer par un point d'accès ou un routeur.

2. **Canal et SSID**  
   - Tous les appareils doivent être configurés sur le **même canal WiFi** et utiliser le **même SSID** pour pouvoir se détecter et communiquer entre eux.

3. **Attribution des adresses IP**  
   - Comme il n'y a pas de serveur DHCP par défaut dans un réseau Adhoc, il faut attribuer **manuellement** des adresses IP fixes à chaque appareil.  
   - Une autre solution consiste à installer un **serveur DHCP** sur l'un des appareils pour distribuer les adresses IP dynamiquement.

### SSID 
- Un SSID est une chaîne de caractères (jusqu'à 32 caractères) utilisée pour nommer un réseau WiFi.
- Tous les appareils connectés à un réseau doivent utiliser le même SSID pour communiquer entre eux.
- Mode Adhoc : Les appareils doivent manuellement configurer et utiliser le même SSID pour pouvoir communiquer directement entre eux.

## Préparation
### Fichiers de configuration à modifier
/etc/network/interfaces ou /etc/dhcpcd.conf	-> Configuration des adresses IP statiques
/etc/wpa_supplicant/wpa_supplicant.conf	-> Paramétrage du WiFi en mode Adhoc
/etc/hosts (optionnel) -> Définition des noms d'hôte pour faciliter l'accès entre les machines
/etc/sysctl.conf (optionnel) -> Activation du routage si nécessaire

## Mise en place

### Sans NetworkManager
```bash
#!/bin/bash

# Désactiver le service DHCP pour éviter les conflits
sudo systemctl stop NetworkManager
sudo systemctl stop dhcpcd
sudo systemctl disable dhcpcd

# Configurer l'interface WiFi en mode Adhoc
sudo ip link set wlan0 down  # Désactiver temporairement l'interface
sudo iwconfig wlan0 mode ad-hoc  # Passer en mode Adhoc
sudo iwconfig wlan0 essid "atsecilthebest"  # Définir le SSID
sudo iwconfig wlan0 channel 4  # Définir le canal 4 (2.427 GHz)
sudo ip link set wlan0 up  # Réactiver l'interface

# Assigner une adresse IP statique
sudo ifconfig wlan0 192.168.1.2 netmask 255.255.255.0 up

# Vérifier la configuration du WiFi
iwconfig wlan0
ifconfig wlan0

# Activer le service réseau pour appliquer la configuration au redémarrage
echo -e "interface wlan0\nstatic ip_address=XXX.XXX.XXX.1/24\nnohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf

# Redémarrer le service réseau pour appliquer les modifications
sudo systemctl restart networking
sudo systemctl restart dhcpcd

echo "Configuration Adhoc terminée. Vérifiez avec 'iwconfig' et 'ifconfig'."

```

### Avec NetworkManager  
voir setup-nm-adhoc.sh