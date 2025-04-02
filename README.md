# Lancement des étapes du projet

### Prérequis

- Les applications peuvent être lancées en localhost ou à travers une connexion par réseau ad-hoc
- De nombreuses applications tournent sur python3

## Étape 1 (Informations réseau)

Pour voir les informations du réseau :

`./e1-param-reseau.sh`

Les commandes utilisées sont :

- Canaux WiFi utilisés : `iwlist wlan0 channel`
- Interférences WiFi (Autres réseaux sur le même canal) : `iwlist wlan0 scan | grep -E "Channel|ESSID"`
- Taux de perte de paquets : `ping -c 10 google.com | grep -oP '\d+(?=% packet loss)'`

## Étape 2 (Réseau Ad-Hoc)

Lancement du réseau ad-hoc sur une Raspberry Pi:

`./setup-manual-adhoc.sh`

### Étape 2Bis (Changement de Canal)

Lancement du changement de canal :

`python3 app_adhoc.py -i <id> -m <is_master> [-l <log_activated>]`

- **id** : id of the node in [1,255]
- **is_master** : is the master that scan the network [true,false]
- **log_activated** : enable log of infos [true,false]

## Étapes 3 et 6 (Application TCP - Wifi )

### Serveur

Lancement de l'application côté serveur :

`sudo python3 server.py <local_port>`

- **local_port** : le port sur lequel écoute le serveur

Le lancement du serveur en sudo est important pour pouvoir rendre les fichiers reçus executables !

### Client

Lancement de l'application côté client :

`python3 client.py <local_ip> <server_ip> <server_port> [-f <file_name>] [-c <command>]`

- **local_ip** : ip du client
- **server_ip** : ip du serveur
- **server_port** : le port sur lequel écoute le serveur
- **file_name** : le nom du fichier à transmettre.
- **command** : la commande à faire executer sur le serveur.

## Étape 5 (Communication de Commandes - Bluetooth)

Cette partie du projet permet la transmission de commandes via Bluetooth entre deux appareils, où l'un agit comme serveur (émetteur de commandes) et l'autre comme client (exécuteur de commandes).

### Prérequis

- Python 3.6+
- Module Python requis : `watchdog`
  ```bash
  pip install watchdog
  ```
- Bluetooth activé sur les deux appareils
- Commande `bluetoothctl` disponible (généralement fournie par le package bluez) :

  ```bash
  # Vérifier si bluetoothctl est installé
  which bluetoothctl

  # Si non installé, installer le package bluez
  sudo apt-get install bluez
  ```

### Fonctionnement

- **Mode serveur** : Surveille un fichier texte pour de nouvelles lignes, les "consomme" (supprime après lecture) et les envoie via Bluetooth
- **Mode client** : Reçoit des commandes via Bluetooth et les exécute dans un répertoire spécifié

### Utilisation

#### Mode Serveur

```bash
python3 bt_command_relay.py server NOM_APPAREIL NOM_CLIENT_CIBLE /path/to/commands_file.txt
```

- **NOM_APPAREIL** : Nom de l'appareil serveur (visible en Bluetooth)
- **NOM_CLIENT_CIBLE** : Nom de l'appareil client à rechercher
- **fichier_commandes.txt** : Fichier à surveiller pour les nouvelles commandes

#### Mode Client

```bash
python3 bt_command_relay.py client NOM_APPAREIL NOM_SERVEUR_CIBLE /chemin/vers/repertoire_execution
```

- **NOM_APPAREIL** : Nom de l'appareil client (visible en Bluetooth)
- **NOM_SERVEUR_CIBLE** : Nom de l'appareil serveur à rechercher
- **repertoire_execution** : Répertoire où les commandes seront exécutées

## Étape GPS

### Prérequis

- Avant de lancer l'application GPS , l'utilisateur doit effectuer les commandes suivantes :

```bash
sudo su
source /path/to/env/bin/activate
```

- Enfin, si elles ne sont pas encore installées, les bibliothèques pythons requises sont :

- - matplotlib
- - colorist
- - numpy

### Application GPS

Pour lancer l'application GPS, il faut se placer dans le répertoire source du projet ( atSecilPi ) puis executer la commande suivante :

`python3 -m gps.gps_app -i <id> -s <simulator_enabled> [-m <app_mode>] [-n <network_mode>] [-l <log_enabled>]`

- **id** : id of the node in [1, 255]
- **simulator_enabled** : enable gps simulator [true, false]
- **app_mode** : app mode in [sender, receiver, loopback]
- **network_mode** : network mode in [adhoc, localhost]
- **log_enabled** : le nom du fichier à transmettre.

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

