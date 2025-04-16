import os
import platform
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()
log_dir = Path("logs/handshakes")
log_dir.mkdir(parents=True, exist_ok=True)

def is_vm():
    try:
        output = subprocess.check_output("systemd-detect-virt", text=True).strip()
        return output != "none"
    except Exception:
        return False

def crack_handshake():
    console.print(Panel("[bold magenta]🔐 WPA Handshake Cracker[/]"))

    # 💡 Show tip only if running in a VM
    if is_vm():
        console.print(Panel(
            "[yellow]⚠️ Running in a virtual machine detected.\n"
            "For better performance, crack on your host OS with GPU.\n\n"
            "📁 To do that:\n"
            "1. Copy the .hc22000 file from logs/handshakes to your host.\n"
            "2. Run one of the following:\n"
            "[green]hashcat -m 22000 -a 3 handshake.hc22000 ?d?d?d?d?d?d?d?d[/green]\n"
            "[green]hashcat -m 22000 -a 0 handshake.hc22000 rockyou.txt[/green]",
            title="⚡ GPU Cracking Tip",
            border_style="yellow"
        ))

    # List all .cap and .hc22000 files
    cap_files = list(log_dir.glob("*.cap"))
    hash_files = list(log_dir.glob("*.hc22000"))

    if not cap_files and not hash_files:
        console.print("[bold red]❌ No handshake files found in logs/handshakes[/]")
        return

    all_files = cap_files + hash_files
    for i, file in enumerate(all_files, 1):
        console.print(f"[cyan]{i}.[/] {file.name}")

    choice = Prompt.ask("Choose file to crack", choices=[str(i) for i in range(1, len(all_files) + 1)])
    selected = all_files[int(choice) - 1]

    # Convert to hc22000 if it's a .cap
    if selected.suffix == ".cap":
        hc_path = selected.with_suffix(".hc22000")
        console.print(f"[bold yellow]🛠 Converting {selected.name} to .hc22000...[/]")
        os.system(f"hcxpcapngtool -o \"{hc_path}\" \"{selected}\"")
        selected = hc_path
        console.print(f"[bold green]✅ Saved as:[/] {hc_path.name}")

    # Run Hashcat
    mode = Prompt.ask("Crack mode", choices=["wordlist", "brute"], default="wordlist")
    if mode == "wordlist":
        wordlist = Prompt.ask("Enter wordlist path", default="/usr/share/wordlists/rockyou.txt")
        os.system(f"hashcat -m 22000 -a 0 \"{selected}\" \"{wordlist}\"")
    else:
        mask = Prompt.ask("Enter brute mask (e.g. ?d?d?d?d?d?d?d?d)", default="?d?d?d?d?d?d?d?d")
        os.system(f"hashcat -m 22000 -a 3 \"{selected}\" \"{mask}\"")
