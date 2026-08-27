"""
Configuration and settings manager for INFINITY Tweaker Desktop Client.
"""
import os
import json
from typing import Any, Dict

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

DEFAULT_SETTINGS = {
    "general": {
        "start_with_windows": False,
        "minimize_to_tray": True,
        "notifications_enabled": True,
        "language": "en",
        "theme": "cyberpunk_dark"
    },
    "performance": {
        "monitor_interval_ms": 1000,
        "overlay_enabled": False,
        "ram_auto_clean": False,
        "ram_threshold_pct": 85
    },
    "network": {
        "backend_url": "https://infinity-tweaker-production.up.railway.app",
        "auto_check_updates": True
    },
    "security": {
        "verify_update_checksums": True,
        "log_level": "DEBUG"
    }
}

class ConfigManager:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self._settings = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(CONFIG_FILE):
            self._save(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # merge with defaults
                merged = DEFAULT_SETTINGS.copy()
                for cat, val in data.items():
                    if isinstance(val, dict) and cat in merged:
                        merged[cat].update(val)
                    else:
                        merged[cat] = val
                return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()

    def _save(self, data: Dict[str, Any]):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def get(self, category: str, key: str, default: Any = None) -> Any:
        return self._settings.get(category, {}).get(key, default)

    def set(self, category: str, key: str, value: Any):
        if category not in self._settings:
            self._settings[category] = {}
        self._settings[category][key] = value
        self._save(self._settings)

    def get_all(self) -> Dict[str, Any]:
        return self._settings

config = ConfigManager()
