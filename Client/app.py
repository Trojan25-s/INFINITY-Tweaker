"""
INFINITY Tweaker Desktop Client Entry Point.
Launches the local hardware bridge server and launches the UI window.
"""
import uvicorn
import webbrowser
import threading
import time
import os
import sys

# Ensure root directory in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from UI.server import client_app
from Core.Logging.logger import get_logger

logger = get_logger()

CLIENT_HOST = "127.0.0.1"
CLIENT_PORT = 5000

def _open_browser():
    time.sleep(1.2)
    url = f"http://{CLIENT_HOST}:{CLIENT_PORT}"
    logger.info(f"Opening INFINITY Tweaker Desktop Interface: {url}")
    webbrowser.open(url)

def main():
    logger.info("Initializing INFINITY Tweaker Client Desktop Application...")
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(client_app, host=CLIENT_HOST, port=CLIENT_PORT, log_level="warning")

if __name__ == "__main__":
    main()
