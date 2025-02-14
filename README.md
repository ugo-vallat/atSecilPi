
# Config ssh  

## Attribution d'un nom
```bash
# changer le hostname (facultatif)
sudo hostname <new-hostname>
sudo hostnamectl set-hostname <new-hostname>
sudo vim /etc/hosts # puis changer le hostname

# activer mDNS pour diffuser son nom
sudo apt install avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

## Connection via ethernet  
1. Connecter par ethernet l'ordinateur(Ord) et la raspberry(Rpi)
2. Récupérer adresse ip/mask de Ord (ifconfig ou ipconfig)
3. Compléter le script ethernet/setup-ethernet-conf.sh (le nom de réseau doit être identique pour Ord et Rpi)
4. lancer le script sur Rpi


# Étapes du projet  

## Étape 1 

- Canaux WiFi utilisés : `iwlist wlan0 channel`
- Interférences WiFi (Autres réseaux sur le même canal) : `iwlist wlan0 scan | grep -E "Channel|ESSID"`
- Taux de perte de paquets : `ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'`

## Étape 2  

En cours (réussi manuellement mais pas avec nmcli)