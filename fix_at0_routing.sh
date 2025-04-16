#!/bin/bash

echo -e "\n[+] Enabling IP forwarding…"
sudo sysctl -w net.ipv4.ip_forward=1

echo -e "\n[+] Flushing existing iptables NAT rules…"
sudo iptables -t nat -F

echo -e "\n[+] Adding NAT masquerade rule for outbound interface (wlan0)…"
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE

echo -e "\n[+] Disabling NetworkManager control over at0 (if active)…"
sudo nmcli dev set at0 managed no 2>/dev/null

echo -e "\n[+] Optional: Disabling IPv6 (some devices get stuck)…"
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1

echo -e "\n[✔] Routing and NAT fix applied for at0."
