#!/bin/bash

# Title
echo -e "\n🛡️  [WiFi Sentinel] Environment Check & Launcher"

# Root check
if [ "$EUID" -ne 0 ]; then
  echo -e "\n❌ Please run this script as root (e.g. sudo ./run.sh)"
  exit 1
fi

# Required files and directories
declare -a required_files=("wifi_sentinel.py" "phish_server.py" "dnsmasq.conf")
declare -a required_dirs=("logs/handshakes" "templates/phishing/router-update")
missing=0

# File check
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "❌ Missing file: $file"
    missing=1
  fi
done

# Directory check
for dir in "${required_dirs[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "❌ Missing directory: $dir"
    missing=1
  fi
done

# Tool check
echo -e "\n🔍 Checking installed tools…"
declare -a tools=("aircrack-ng" "mdk4" "tcpdump" "hashcat" "crunch" "dnsmasq" "python3")
for tool in "${tools[@]}"; do
  if ! command -v "$tool" &>/dev/null; then
    echo "⚠️  Tool missing: $tool"
  fi
done

# Exit if anything's missing
if [ "$missing" -eq 1 ]; then
  echo -e "\n⚠️  One or more required components are missing. Please run ./setup.sh first."
  exit 1
fi

# Set permissions
chmod +x wifi_sentinel.py phish_server.py

# Launch
echo -e "\n🚀 Launching WiFi Sentinel…"
python3 wifi_sentinel.py
