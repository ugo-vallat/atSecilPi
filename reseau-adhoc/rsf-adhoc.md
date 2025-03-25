
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
voir `setup-manual-adhoc.sh`

### Avec NetworkManager  

#### Documentation  
WPA Supplicant config file explanations : https://gist.github.com/penguinpowernz/ce4ed0e64ce0fa99a5e335c1a4c954b3

```
# mode: IEEE 802.11 operation mode
# 0 = infrastructure (Managed) mode, i.e., associate with an AP (default)
# 1 = IBSS (ad-hoc, peer-to-peer)
# 2 = AP (access point)
# Note: IBSS can only be used with key_mgmt NONE (plaintext and static WEP) and
# WPA-PSK (with proto=RSN). In addition, key_mgmt=WPA-NONE (fixed group key
# TKIP/CCMP) is available for backwards compatibility, but its use is
# deprecated. WPA-None requires following network block options:
# proto=WPA, key_mgmt=WPA-NONE, pairwise=NONE, group=TKIP (or CCMP, but not
# both), and psk must also be set.





```

#### Trucs à pas faire  

- WPA-NONE is deprecated !!
- key-mgmt none (utilise uniquement channel 36)

#### Code  
voir `setup-nm-adhoc.sh`

```/etc/wpa_supplicant-adhoc.conf
ctrl_interface=DIR=/run/wpa_supplicant GROUP=wheel

# use 'ap_scan=2' on all devices connected to the network
# this is unnecessary if you only want the network to be created when no other networks are available
# ap_scan=2

network={
    ssid="adhocAtSecil"
    mode=1
    frequency=2427
    proto=RSN
    key_mgmt=WPA-PSK
    pairwise=CCMP
    group=CCMP
    psk="12345678"
}
```

puis `wpa_supplicant -B -i interface -c /etc/wpa_supplicant-adhoc.conf -D nl80211,wext`