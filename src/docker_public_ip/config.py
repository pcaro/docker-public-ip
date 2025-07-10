import os
from pathlib import Path

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
DB_PATH = Path(os.getenv("DB_PATH", "/data/ip_history.db"))
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")

IP_SERVICES = [
    "https://icanhazip.com",
    "https://checkip.amazonaws.com",
    "https://ipinfo.io/ip",
    "https://wtfismyip.com/text",
    "https://api.ipify.org",
    "https://ifconfig.io/ip",
    "https://www.moanmyip.com/simple",
    "https://ifconfig.co/ip",
    "https://ifconfig.me/ip",
    "https://ipecho.net/plain",
]
