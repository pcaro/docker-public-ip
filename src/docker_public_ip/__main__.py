import signal
import sys
import threading
import time

from loguru import logger

from .ip_checker import IPChecker
from .web import run_web_server


def signal_handler(signum, frame):
    logger.info("Received signal to terminate")
    sys.exit(0)


def main():
    logger.info("Starting Docker Public IP Monitor")

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start IP checker
    checker = IPChecker()
    checker.start()

    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, args=(checker,), daemon=True)
    web_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        checker.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
