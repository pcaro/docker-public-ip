import os
from pathlib import Path
from loguru import logger

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
DB_PATH = Path(os.getenv("DB_PATH", "/data/ip_history.db"))
WEB_PORT = int(os.getenv("WEB_PORT", "8080"))
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
SERVICES_FILE = Path(os.getenv("SERVICES_FILE", "/config/services.txt"))

# Default IP services (fallback if file doesn't exist)
DEFAULT_IP_SERVICES = [
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


def load_ip_services():
    """Load IP services from configuration file"""
    if SERVICES_FILE.exists():
        try:
            services = []
            with open(SERVICES_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        # Ensure URL has protocol
                        if not line.startswith(("http://", "https://")):
                            line = "https://" + line
                        services.append(line)

            if services:
                logger.info(f"Loaded {len(services)} IP services from {SERVICES_FILE}")
                return services
            else:
                logger.warning(
                    f"No valid services found in {SERVICES_FILE}, using defaults"
                )
                return DEFAULT_IP_SERVICES

        except Exception as e:
            logger.error(f"Error reading services file {SERVICES_FILE}: {e}")
            logger.info("Using default IP services")
            return DEFAULT_IP_SERVICES
    else:
        logger.info(f"Services file {SERVICES_FILE} not found, using defaults")
        return DEFAULT_IP_SERVICES


# Load IP services on module import
IP_SERVICES = load_ip_services()
