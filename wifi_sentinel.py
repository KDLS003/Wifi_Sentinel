import logging
import subprocess
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from modules import monitor, sniffers, attacks, fake_ap, handshake, utils

console = Console()

# Set up logging
logging.basicConfig(
    filename='logs/wifi_sentinel.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# --- Interface Detection ---
def detect_interfaces() -> List[str]:
    """Detect available wireless interfaces using 'iw dev' or 'ifconfig'."""
    try:
        result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.splitlines():
            if line.strip().startswith('Interface'):
                iface = line.strip().split()[-1]
                interfaces.append(iface)
        if interfaces:
            return interfaces
    except Exception as e:
        logging.warning(f"Failed to use 'iw dev': {e}")
    # Fallback to ifconfig
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.splitlines():
            if line and not line.startswith(' '):
                iface = line.split(':')[0]
                if iface.startswith('wl') or iface.startswith('wlan'):
                    interfaces.append(iface)
        return interfaces
    except Exception as e:
        logging.error(f"Failed to detect interfaces: {e}")
        return []

banner = """
[bold red]

 █     █░ ██▓  █████▒██▓     ██████ ▓█████  ███▄    █ ▄▄▄█████▓ ██▓ ███▄    █ ▓█████  ██▓    
▓█░ █ ░█░▓██▒▓██   ▒▓██▒   ▒██    ▒ ▓█   ▀  ██ ▀█   █ ▓  ██▒ ▓▒▓██▒ ██ ▀█   █ ▓█   ▀ ▓██▒    
▒█░ █ ░█ ▒██▒▒████ ░▒██▒   ░ ▓██▄   ▒███   ▓██  ▀█ ██▒▒ ▓██░ ▒░▒██▒▓██  ▀█ ██▒▒███   ▒██░    
░█░ █ ░█ ░██░░▓█▒  ░░██░     ▒   ██▒▒▓█  ▄ ▓██▒  ▐▌██▒░ ▓██▓ ░ ░██░▓██▒  ▐▌██▒▒▓█  ▄ ▒██░    
░░██▒██▓ ░██░░▒█░   ░██░   ▒██████▒▒░▒████▒▒██░   ▓██░  ▒██▒ ░ ░██░▒██░   ▓██░░▒████▒░██████▒
░ ▓░▒ ▒  ░▓   ▒ ░   ░▓     ▒ ▒▓▒ ▒ ░░░ ▒░ ░░ ▒░   ▒ ▒   ▒ ░░   ░▓  ░ ▒░   ▒ ▒ ░░ ▒░ ░░ ▒░▓  ░
  ▒ ░ ░   ▒ ░ ░      ▒ ░   ░ ░▒  ░ ░ ░ ░  ░░ ░░   ░ ▒░    ░     ▒ ░░ ░░   ░ ▒░ ░ ░  ░░ ░ ▒  ░
  ░   ░   ▒ ░ ░ ░    ▒ ░   ░  ░  ░     ░      ░   ░ ░   ░       ▒ ░   ░   ░ ░    ░     ░ ░   
    ░     ░          ░           ░     ░  ░         ░           ░           ░    ░  ░    ░  ░
                                                                                                   
[/bold red]
[bold green]   WiFi Sentinel - Kali Edition [ESP32 Marauder Style][/]

[bold yellow]A toolkit for WiFi security research, penetration testing, and education.[/]

[bold red]DISCLAIMER:[/]
[white]This tool is for authorized testing and educational purposes only.
The author is NOT responsible for any misuse or illegal activities.
Do NOT use this tool for unauthorized or illegal actions.[/]
"""

def main() -> None:
    """Main entry point for WiFi Sentinel. Handles menu and user navigation."""
    console.print(Panel(banner))
    interfaces = detect_interfaces()
    interface: Optional[str] = None
    if interfaces:
        console.print("[bold cyan]Detected wireless interfaces:[/]")
        for idx, iface in enumerate(interfaces, 1):
            console.print(f"[cyan]{idx}.[/] {iface}")
        idx = Prompt.ask("Select interface", choices=[str(i) for i in range(1, len(interfaces)+1)], default="1")
        interface = interfaces[int(idx)-1]
    else:
        interface = Prompt.ask("Enter WiFi interface (e.g. wlan0)", default="wlan0")
    logging.info(f"Selected interface: {interface}")

    while True:
        console.print("\n[bold blue]Main Menu[/]")
        menu_options = [
            ("1", "🔍 Sniffers", sniffers.menu),
            ("2", "💥 Attacks", attacks.menu),
            ("3", "⚙️  General", general_menu),
            ("4", "❌ Exit", None)
        ]
        for key, label, _ in menu_options:
            console.print(f"[cyan]{key}.[/] {label}")
        choice = Prompt.ask("Choose a category", choices=[opt[0] for opt in menu_options])
        try:
            if choice == "1":
                sniffers.menu(interface)
            elif choice == "2":
                # Confirm before running attacks
                confirm = Prompt.ask("[red]Are you sure you want to run attack modules? (y/n)[/]", choices=["y","n"], default="n")
                if confirm == "y":
                    attacks.menu(interface)
                else:
                    console.print("[yellow]Attack cancelled.[/]")
            elif choice == "3":
                general_menu(interface)
            elif choice == "4":
                console.print("[bold red]Exiting WiFi Sentinel...[/]")
                logging.info("User exited WiFi Sentinel.")
                break
        except Exception as e:
            logging.error(f"Error in main menu: {e}")
            console.print(f"[bold red]An error occurred: {e}[/]")

def general_menu(interface: str) -> None:
    """General options menu for monitor mode, wordlist, and logs."""
    while True:
        console.print("\n[bold magenta]General Options[/]")
        menu_options = [
            ("1", "Enable Monitor Mode", monitor.enable_monitor_mode),
            ("2", "Disable Monitor Mode", monitor.disable_monitor_mode),
            ("3", "Generate Wordlist", utils.generate_wordlist),
            ("4", "View Logs", utils.live_log_view),
            ("5", "Go Back", None)
        ]
        for key, label, _ in menu_options:
            console.print(f"[cyan]{key}.[/] {label}")
        choice = Prompt.ask("Select option", choices=[opt[0] for opt in menu_options])
        try:
            if choice == "1":
                monitor.enable_monitor_mode(interface)
            elif choice == "2":
                monitor.disable_monitor_mode(interface)
            elif choice == "3":
                utils.generate_wordlist()
            elif choice == "4":
                utils.live_log_view()
            elif choice == "5":
                break
        except Exception as e:
            logging.error(f"Error in general menu: {e}")
            console.print(f"[bold red]An error occurred: {e}[/]")

if __name__ == "__main__":
    main()
