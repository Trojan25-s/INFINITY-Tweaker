"""
Client-side update checker with cryptographic SHA-256 integrity verification.
"""
import hashlib
import requests
from typing import Dict, Any
from Core.Configuration.config_manager import config
from Core.Logging.logger import get_logger

logger = get_logger()

CURRENT_VERSION = "1.0.0"

def check_for_updates() -> Dict[str, Any]:
    backend_url = config.get("network", "backend_url", "http://127.0.0.1:8000")
    endpoint = f"{backend_url}/api/v1/updates/check?version={CURRENT_VERSION}"
    try:
        res = requests.get(endpoint, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data
        return {"update_available": False, "error": f"HTTP {res.status_code}"}
    except Exception as e:
        logger.warning(f"Update check failed: {e}")
        return {"update_available": False, "error": str(e)}

def verify_download_integrity(file_path: str, expected_sha256: str) -> bool:
    """Verify SHA-256 hash of a downloaded installer package before execution."""
    if not expected_sha256 or len(expected_sha256) != 64:
        return False
    try:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        calculated = sha256.hexdigest().lower()
        match = calculated == expected_sha256.lower()
        if not match:
            logger.error(f"Checksum mismatch! Expected {expected_sha256}, got {calculated}")
        return match
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        return False
