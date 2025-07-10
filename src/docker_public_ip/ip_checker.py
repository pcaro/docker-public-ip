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

    def check_ip(self):
        service = random.choice(IP_SERVICES)
        logger.debug(f"Checking IP using {service}")
        
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
                    self.db.record_check(
                        service=service,
                        ip_address=ip_address,
                        response_time_ms=response_time_ms,
                        success=True,
                    )
                    
                    if ip_address != self.last_ip:
                        if self.last_ip is not None:
                            logger.warning(
                                f"IP changed from {self.last_ip} to {ip_address}"
                            )
                        else:
                            logger.info(f"Initial IP: {ip_address}")
                        self.last_ip = ip_address
                    
                    logger.debug(
                        f"Check successful: {ip_address} ({response_time_ms:.0f}ms)"
                    )
                else:
                    error_msg = f"Invalid IP format: {ip_address}"
                    logger.error(error_msg)
                    self.db.record_check(
                        service=service,
                        response_time_ms=response_time_ms,
                        success=False,
                        error_message=error_msg,
                    )
            else:
                error_msg = f"HTTP {response.status_code}"
                logger.error(f"Check failed: {error_msg}")
                self.db.record_check(
                    service=service,
                    response_time_ms=response_time_ms,
                    success=False,
                    error_message=error_msg,
                )
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Check failed: {error_msg}")
            self.db.record_check(
                service=service, success=False, error_message=error_msg
            )

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