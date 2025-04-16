import os
import shutil
import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()
handshake_dir = "logs/wifite_handshake"
hs_source_dir = "hs"

def auto_attack(interface):
    console.print(Panel("[bold magenta]🚀 Starting Wifite for automatic handshake capture[/]"))
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_folder = os.path.join(handshake_dir, f"capture_{timestamp}")
    os.makedirs(capture_folder, exist_ok=True)

    # Run Wifite (will save to /hs)
    os.system(f"sudo wifite -i {interface} --wpa --kill")

    # Copy .cap files from hs/
    if not os.path.exists(hs_source_dir):
        console.print("[bold red]❌ Handshake source folder (hs/) not found![/]")
        return

    cap_files = [f for f in os.listdir(hs_source_dir) if f.endswith(".cap")]
    if not cap_files:
        console.print("[bold red]❌ No .cap files found in hs/![/]")
        return

    for f in cap_files:
        shutil.copy2(os.path.join(hs_source_dir, f), os.path.join(capture_folder, f))

    console.print(f"[bold green]✅ Saved {len(cap_files)} .cap file(s) to:[/] [cyan]{capture_folder}[/]")
