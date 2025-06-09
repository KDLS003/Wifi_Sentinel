import os
import re
import time 
import subprocess
import csv
from pathlib import Path
from rich.align import Align
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()

def menu(interface: str) -> None:
    """Display the sniffer menu and route to the selected sniffer module."""
    while True:
        console.print("\n[bold yellow]WiFi Sniffers[/]")
        console.print("[cyan]1.[/] Probe Sniffer")
        console.print("[cyan]2.[/] Beacon Sniffer")
        console.print("[cyan]3.[/] Deauth Sniffer")
        console.print("[cyan]4.[/] Scan APs")
        console.print("[cyan]5.[/] Return to Main Menu")

        choice = Prompt.ask("Select sniffer")
        if choice == "1":
            sniff_probes(interface)
        elif choice == "2":
            sniff_beacons(interface)
        elif choice == "3":
            sniff_deauth(interface)
        elif choice == "4":
            scan_aps(interface)
        elif choice == "5":
            break
        else:
            console.print("[bold red]Invalid choice[/]")

def sniff_probes(interface: str) -> None:
    """Sniff and log WiFi probe requests in real time on the given interface."""
    console.print(Panel("[bold green]📡 Real-Time Probe Request Viewer (CTRL+C to stop)[/]"))

    data = []

    table = Table(title="Probe Requests", expand=True)
    table.add_column("Time", justify="center")
    table.add_column("SSID", style="cyan", overflow="fold")
    table.add_column("Signal", style="green")

    log_dir = Path("logs/sniffers")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = log_dir / f"probe_{timestamp}.csv"

    def extract_probe(line: str) -> tuple[str, str]:
        """Extract SSID and signal from a tcpdump probe request line."""
        try:
            ssid_match = re.search(r'Probe Request \((.*?)\)', line)
            ssid = ssid_match.group(1) if ssid_match else "Hidden"
            signal_match = re.search(r'(-\d+dBm)', line)
            signal = signal_match.group(1) if signal_match else "N/A"
            return ssid.strip(), signal
        except:
            return None, None

    with Live(table, refresh_per_second=4):
        try:
            proc = subprocess.Popen(
                ["sudo", "tcpdump", "-l", "-i", interface, "-e", "-s", "256", "type mgt subtype probe-req"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True
            )

            for line in proc.stdout:
                ssid, signal = extract_probe(line)
                if ssid:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    table.add_row(timestamp, ssid if ssid else "Hidden", signal)
                    data.append([timestamp, ssid, signal])
        except KeyboardInterrupt:
            proc.terminate()
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "SSID", "Signal"])
                writer.writerows(data)
            console.print(f"\n[bold green]✅ Log saved to:[/] [cyan]{csv_path}[/]")
            console.print(f"[bold cyan]🔎 Total probes captured:[/] [bold yellow]{len(data)}[/]")
            
            
            
            

def sniff_beacons(interface: str = "wlan0") -> None:
    """Sniff and log WiFi beacon frames in real time on the given interface."""
    from pathlib import Path
    import csv

    console.clear()
    console.print(Panel("[bold cyan]📡 Real-Time Beacon Sniffer Viewer (CTRL+C to stop)[/]"))

    beacon_data = []
    seen = set()

    log_dir = Path("logs/sniffers")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = log_dir / f"beacon_{timestamp}.csv"

    table = Table(title="Beacon Frames", show_header=True, header_style="bold magenta")
    table.add_column("Time", style="dim", width=10)
    table.add_column("SSID", style="cyan")
    table.add_column("Channel", justify="center")
    table.add_column("Signal", justify="right")

    def parse_beacon_output(output_line: str) -> dict:
        """Parse a tcpdump beacon output line into a dict of info."""
        time_match = re.match(r"^(\d{2}:\d{2}:\d{2})", output_line)
        signal_match = re.search(r"(-\d{2,3}dBm)", output_line)
        ssid_match = re.search(r"Beacon\s+\((.*?)\)", output_line)
        channel_match = re.search(r"CH:\s*(\d+)", output_line)

        if time_match and ssid_match and signal_match:
            return {
                "time": time_match.group(1),
                "ssid": ssid_match.group(1) or "Hidden",
                "signal": signal_match.group(1),
                "channel": channel_match.group(1) if channel_match else "N/A"
            }
        return None

    def render_table() -> Align:
        """Render the beacon table for live display."""
        tbl = Table(show_header=True, header_style="bold magenta")
        tbl.add_column("Time", style="dim", width=10)
        tbl.add_column("SSID", style="cyan", no_wrap=True)
        tbl.add_column("Channel", justify="center")
        tbl.add_column("Signal", justify="right")

        for entry in beacon_data[-30:][::-1]:  # display latest 30
            tbl.add_row(entry["time"], entry["ssid"], entry["channel"], entry["signal"])
        return Align.center(tbl)

    live = Live(render_table(), refresh_per_second=4, console=console)
    live.start()

    try:
        proc = subprocess.Popen(
            ["sudo", "tcpdump", "-l", "-e", "-s", "256", "-i", interface, "type mgt subtype beacon"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        for line in proc.stdout:
            parsed = parse_beacon_output(line)
            if parsed:
                key = (parsed["ssid"], parsed["channel"])
                if key not in seen:
                    seen.add(key)
                    beacon_data.append(parsed)
                    live.update(render_table())
    except KeyboardInterrupt:
        proc.terminate()
        live.stop()
        console.clear()  # Clean up visual glitches
        final_table = render_table()
        console.print(final_table)

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "SSID", "Channel", "Signal"])
            for entry in beacon_data:
                writer.writerow([entry["time"], entry["ssid"], entry["channel"], entry["signal"]])

        console.print(f"\n[bold green]✅ Log saved to:[/] [cyan]{csv_path}[/]")
        console.print(f"[bold cyan]📡 Unique beacon sources captured:[/] [bold yellow]{len(seen)}[/]")


            
            
            
            
            

def sniff_deauth(interface: str) -> None:
    """Sniff and log WiFi deauthentication frames in real time on the given interface."""
    console.clear()
    console.print(Panel("[bold red]💥 Real-Time Deauth Sniffer Viewer (CTRL+C to stop)[/]"))

    table = Table(title="Deauth Frames", show_header=True, header_style="bold red")
    table.add_column("Time", style="dim", width=10)
    table.add_column("Source", style="yellow")
    table.add_column("Destination", style="green")
    table.add_column("Signal", justify="right")

    log_dir = Path("logs/sniffers")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = log_dir / f"deauth_{timestamp}.csv"
    data = []

    def parse_deauth(line: str) -> dict:
        """Parse a tcpdump deauth output line into a dict of info."""
        try:
            time_match = re.search(r"^(\d{2}:\d{2}:\d{2})", line)
            signal_match = re.search(r"(-\d+dBm)", line)
            src_match = re.search(r"SA:([0-9A-Fa-f:]{17})", line)
            dst_match = re.search(r"DA:([0-9A-Fa-f:]{17})", line)

            return {
                "time": time_match.group(1) if time_match else "N/A",
                "signal": signal_match.group(1) if signal_match else "N/A",
                "source": src_match.group(1) if src_match else "Unknown",
                "destination": dst_match.group(1) if dst_match else "Broadcast"
            }
        except:
            return None

    with Live(table, refresh_per_second=4) as live:
        try:
            proc = subprocess.Popen(
                ["sudo", "tcpdump", "-l", "-i", interface, "-e", "-s", "256", "type mgt subtype deauth"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )

            for line in proc.stdout:
                parsed = parse_deauth(line)
                if parsed:
                    table.add_row(parsed["time"], parsed["source"], parsed["destination"], parsed["signal"])
                    data.append([parsed["time"], parsed["source"], parsed["destination"], parsed["signal"]])
        except KeyboardInterrupt:
            proc.terminate()
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Time", "Source", "Destination", "Signal"])
                writer.writerows(data)
            console.print(f"\n[bold green]✅ Log saved to:[/] [cyan]{csv_path}[/]")
            console.print(f"[bold red]🔐 Total deauth frames captured:[/] [bold yellow]{len(data)}[/]")
            
            


def scan_aps(interface: str) -> None:
    """Scan for nearby access points and log the results using airodump-ng."""
    console.clear()
    console.print(Panel("[bold cyan]📶 Scanning Nearby Access Points (CTRL+C to stop)[/]"))

    log_dir = Path("logs/scans")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_prefix = log_dir / f"airodump_scan_{timestamp}"

    try:
        subprocess.call([
            "sudo", "airodump-ng",
            "--write", str(csv_prefix),
            "--output-format", "csv",
            interface
        ])
    except KeyboardInterrupt:
        pass

    csv_path = f"{csv_prefix}-01.csv"

    # ✅ Show confirmation to the user
    console.print(f"\n[bold green]✅ Scan ended. Log saved to:[/] [cyan]{csv_path}[/]")


