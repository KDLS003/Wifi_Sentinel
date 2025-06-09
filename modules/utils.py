import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

def generate_wordlist() -> None:
    """Prompt user for wordlist parameters and generate a custom wordlist using crunch."""
    min_len = Prompt.ask("[green]Min length", default="8")
    max_len = Prompt.ask("[green]Max length", default="10")
    charset = Prompt.ask("[green]Charset (e.g. abc123)", default="abc123")
    out_file = os.path.join("wordlists", Prompt.ask("Output file", default="custom.txt"))
    os.makedirs("wordlists", exist_ok=True)
    console.print(f"[cyan]Generating wordlist to {out_file}...[/]")
    os.system(f"crunch {min_len} {max_len} {charset} -o {out_file}")

def live_log_view() -> None:
    """Prompt user for a log file path and display a live tail of the log."""
    log_path = Prompt.ask("[cyan]Enter path to log file", default="logs/handshakes")
    os.system(f"tail -f {log_path}")
