#!/bin/bash

echo -e "\n🔧 Setting up WiFi Sentinel…"

# Must be root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root."
  exit 1
fi

echo -e "\n📦 Installing dependencies…"
apt update
apt install -y aircrack-ng mdk4 tcpdump hashcat crunch dnsmasq python3-pip
pip3 install flask rich

echo -e "\n📂 Creating directories…"
mkdir -p logs/handshakes wordlists templates/phishing/router-update

echo -e "\n✅ Setup complete. Run the tool using: ./run.sh"
