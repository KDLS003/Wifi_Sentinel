#!/bin/bash

echo -e "\n🧹 Uninstalling WiFi Sentinel traces…"

read -p "⚠️  This will delete all logs, configs, and captured credentials. Continue? (y/N): " confirm
if [[ "$confirm" != "y" ]]; then
  echo "❌ Cancelled."
  exit 1
fi

# Remove files and directories
rm -rf logs wordlists credentials.txt
rm -f phish_server.py dnsmasq.conf wifi_sentinel.py
rm -rf templates/phishing/router-update

# Optional: Uncomment to remove installed tools
# apt remove --purge -y aircrack-ng mdk4 tcpdump hashcat crunch dnsmasq python3-pip

echo -e "\n✅ Cleaned up local traces."
echo "Done."
