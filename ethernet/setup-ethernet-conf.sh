#!/bin/bash

# Définir une IP statique et un masque (le masque et le nom du réseau doit être le même que celui de l'appareil connecté en ethernet)
IP=169.254.120.10
MASK=16

# suppression des anciennes connexions
sudo nmcli connection delete ethStatic

# création profil ethernet (ethStatic)
sudo nmcli connection add type ethernet ifname eth0 con-name ethStatic ipv4.addresses $(IP)/$(MASK) ipv4.method manual connection.autoconnect yes

sudo nmcli connection up ethStatic
