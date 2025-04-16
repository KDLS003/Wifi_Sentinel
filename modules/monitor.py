import os
from rich.console import Console
from rich.panel import Panel

console = Console()

def enable_monitor_mode(interface):
    console.print(Panel(f"[bold cyan]Enabling monitor mode on {interface}...[/]"))
    os.system(f"sudo ip link set {interface} down")
    os.system(f"sudo iw dev {interface} set type monitor")
    os.system(f"sudo ip link set {interface} up")

def disable_monitor_mode(interface):
    console.print(Panel(f"[bold cyan]Disabling monitor mode on {interface}...[/]"))
    os.system(f"sudo ip link set {interface} down")
    os.system(f"sudo iw dev {interface} set type managed")
    os.system(f"sudo ip link set {interface} up")
