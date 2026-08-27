"""
Sanitized diagnostic logging for INFINITY Tweaker.
Logs application lifecycle, hardware operations, optimizations, and errors without exposing sensitive secrets.
"""
import logging
import os
import re
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"infinity_tweaker_{datetime.now().strftime('%Y%m%d')}.log")

# Regex to sanitize potential activation codes or tokens
CODE_REGEX = re.compile(r'INF-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}', re.IGNORECASE)

class SanitizedFormatter(logging.Formatter):
    def format(self, record):
        original = super().format(record)
        sanitized = CODE_REGEX.sub("INF-****-****-****", original)
        return sanitized

logger = logging.getLogger("INFINITY_Tweaker")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(SanitizedFormatter('[%(asctime)s] [%(levelname)s] [%(module)s]: %(message)s'))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SanitizedFormatter('[%(levelname)s] %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_logger():
    return logger
