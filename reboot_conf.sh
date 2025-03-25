#!/bin/bash

sudo systemctl start NetworkManager
sudo nmcli dev set wlan0 managed yes
sudo systemctl restart NetworkManager

echo "Reboot done"
