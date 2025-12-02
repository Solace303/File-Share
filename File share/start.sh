#!/bin/bash

# Get the IP address of wlan0
WLAN_IP=$(ip a show wlan0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

# Check if IP was found
if [ -z "$WLAN_IP" ]; then
    echo "Error: Could not find IP address for wlan0"
    exit 1
fi

# Run the Python script with the detected IP
python3 "/home/solace/Bot/File share/server3.py" --bind "$WLAN_IP"

exec bash
