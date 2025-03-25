
# GPS  

## Recherche du port  

Emplacements connus pour la clé GPS :
- /dev/ttyACM0
- /dev/serial/by-path/platform-3f980000.usb-usb-0\:1.1.3\:1.0
- /dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_7_-_GPS_GNSS_Receiver-if00

```bash
# Lire un fichier en continu
tail -f /chemin/vers/fichier
```

## Format des données  

### Trames  
- `GPTXT` : informations
- `GPRMC` : Recommended Minimum Specific GNSS Data (heure, position, vitesse, ...)
- `GPVTG` : Course et Vitesse
- `GPGGA` : Global Positioning System Fix Data


### Output brut

```bash
# Commande
> tail -f /dev/ttyACM0

# output
$GPTXT,01,01,02,u-blox ag - www.u-blox.com*50 # le fabricant
$GPTXT,01,01,02,HW  UBX-G70xx   00070000 FF7FFFFFo*69 # le modèle du chipset
$GPTXT,01,01,02,ROM CORE 1.00 (59842) Jun 27 2012 17:43:52*59 # la version du firmware
$GPTXT,01,01,02,PROTVER 14.00*1E
$GPTXT,01,01,02,ANTSUPERV=AC SD PDoS SR*20
$GPTXT,01,01,02,ANTSTATUS=OK*3B # Etat de l'antenne
$GPTXT,01,01,02,LLC FFFFFFFF-FFFFFFFF-FFFFFFFF-FFFFFFFF-FFFFFFFD*2C

$GPRMC,093908.00,V,,,,,,,140325,,,N*77 # Heure UTC : 09:39:08 / Status : V (valide) / Pas de position /  Date : 14/03/25 / Pas de vitesse ni de cap / Mode de positionnement (N = Non disponible)
$GPVTG,,,,,,,,,N*30
$GPGGA,093908.00,,,,,0,00,99.99,,,,,,*6D
$GPGSA,A,1,,,,,,,,,,,,,99.99,99.99,99.99*30
$GPGSV,1,1,02,11,,,28,12,,,28*78
$GPGLL,,,,,093908.00,V,N*41
```

```bash
INPUT="/dev/serial/by-path/platform-3f980000.usb-usb-0\:1.3\:1.0"

# reade pos input  
cat $INPUT

# display gps pos
sudo apt install gpsd gpsd-clients python3-gps
sudo systemctl stop gpsd.socket
sudo gpsd $INPUT -F /var/run/gpsd.sock
gpsmon # ou cgps -s


```