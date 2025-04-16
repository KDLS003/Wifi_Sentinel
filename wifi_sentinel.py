from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from modules import monitor, sniffers, attacks, fake_ap, handshake, utils

console = Console()

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
"""

def main():
    console.print(Panel(banner))
    interface = Prompt.ask("Enter WiFi interface (e.g. wlan0)", default="wlan0")

    while True:
        console.print("\n[bold blue]Main Menu[/]")
        console.print("[cyan]1.[/] 🔍 Sniffers")
        console.print("[cyan]2.[/] 💥 Attacks")
        console.print("[cyan]3.[/] ⚙️  General")
        console.print("[cyan]4.[/] ❌ Exit")

        choice = Prompt.ask("Choose a category")

        if choice == "1":
            sniffers.menu(interface)
        elif choice == "2":
            attacks.menu(interface)
        elif choice == "3":
            general_menu(interface)
        elif choice == "4":
            console.print("[bold red]Exiting WiFi Sentinel...[/]")
            break
        else:
            console.print("[bold red]Invalid choice[/]")

def general_menu(interface):
    while True:
        console.print("\n[bold magenta]General Options[/]")
        console.print("[cyan]1.[/] Enable Monitor Mode")
        console.print("[cyan]2.[/] Disable Monitor Mode")
        console.print("[cyan]3.[/] Generate Wordlist")
        console.print("[cyan]4.[/] View Logs")
        console.print("[cyan]5.[/] Go Back")

        choice = Prompt.ask("Select option")
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
        else:
            console.print("[bold red]Invalid choice[/]")

if __name__ == "__main__":
    main()
