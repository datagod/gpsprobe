#!/bin/bash

clear


RED="\e[31m"
ORANGE="\e[33m"
BLUE="\e[94m"
GREEN="\e[92m"
STOP="\e[0m"




cd /home/pi/gpsprobe
printf "${GREEN}"
figlet "Launching Airmon"
sudo airmon-ng start wlan1

echo "checking for interfering processes"
sudo airmon-ng check kill

#echo "renaming old logfile"
#mv gpslog.txt  "gpslog$(date +%Y%m%d_%H%M).txt"


echo "Launch GPSProbe"
#sudo python gpsprobe.py -i wlan1mon -t iso  -o  gpslog.txt -f -s -r -l -u -g 
(sudo python gpsprobe.py -i wlan1mon -t iso  -o  gpslog.txt -f -s -r -u -g ) || stty sane || (sleep 0.5s) || (source ../gpsprobe.sh)

stty sane


printf "${STOP}"
