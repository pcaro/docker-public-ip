import random
import time
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from .config import CHECK_INTERVAL, IP_SERVICES
from .database import Database


class IPChecker:
    def __init__(self):
        self.db = Database()
        self.scheduler = BackgroundScheduler()
        self.last_ip = None

    def check_ip_single(self, service):
        """Check IP using a single service"""
        try:
            start_time = time.time()
            response = requests.get(service, timeout=10)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                ip_address = response.text.strip()

                # Basic IP validation
                parts = ip_address.split(".")
                if len(parts) == 4 and all(
                    p.isdigit() and 0 <= int(p) <= 255 for p in parts
                ):
                    return ip_address, response_time_ms, None
                else:
                    return None, response_time_ms, f"Invalid IP format: {ip_address}"
            else:
                return None, response_time_ms, f"HTTP {response.status_code}"

        except Exception as e:
            return None, 0, str(e)

    def check_ip(self):
        """Check IP with retry logic up to 5 times"""
        services = IP_SERVICES.copy()
        random.shuffle(services)

        for attempt in range(min(5, len(services))):
            service = services[attempt]

            ip_address, response_time_ms, error_msg = self.check_ip_single(service)

            if ip_address:
                # Success - record and check for changes
                self.db.record_check(
                    service=service,
                    ip_address=ip_address,
                    response_time_ms=response_time_ms,
                    success=True,
                )

                if ip_address != self.last_ip:
                    if self.last_ip is not None:
                        logger.info(f"IP changed from {self.last_ip} to {ip_address}")
                    else:
                        logger.info(f"Initial IP detected: {ip_address}")
                    self.last_ip = ip_address

                return  # Success, exit retry loop
            else:
                # Failed - record error
                self.db.record_check(
                    service=service,
                    response_time_ms=response_time_ms,
                    success=False,
                    error_message=error_msg,
                )

                if attempt < min(4, len(services) - 1):
                    logger.debug(
                        f"Service {service} failed ({error_msg}), trying next service"
                    )
                else:
                    logger.error(f"All {attempt + 1} services failed on this check")

    def start(self):
        logger.info(f"Starting IP checker with {CHECK_INTERVAL}s interval")

        # Run first check immediately
        self.check_ip()

        # Schedule periodic checks
        self.scheduler.add_job(
            self.check_ip,
            "interval",
            seconds=CHECK_INTERVAL,
            id="ip_check",
            replace_existing=True,
        )
        self.scheduler.start()

    def stop(self):
        logger.info("Stopping IP checker")
        self.scheduler.shutdown(wait=True)
