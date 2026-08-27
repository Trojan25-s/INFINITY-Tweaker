"""
Startup Application Manager: Reads, enables, disables, and audits Windows autostart entries across Registry and Startup folders.
"""
import winreg
import os
from typing import Dict, Any, List
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

RUN_KEYS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM Run")
]

DISABLED_BACKUP_KEY = r"Software\INFINITY_Tweaker\DisabledStartup"

def list_startup_entries() -> List[Dict[str, Any]]:
    """Enumerate active and disabled startup applications."""
    items = []
    
    # 1. Registry Run Keys
    for hive, subkey, loc_name in RUN_KEYS:
        try:
            k = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
            num_values = winreg.QueryInfoKey(k)[1]
            for i in range(num_values):
                try:
                    name, val, _ = winreg.EnumValue(k, i)
                    items.append({
                        "name": name,
                        "command": val,
                        "location": loc_name,
                        "is_enabled": True,
                        "hive_id": "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM",
                        "subkey": subkey
                    })
                except Exception:
                    continue
            winreg.CloseKey(k)
        except Exception:
            continue

    # 2. Disabled Backup Entries
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY, 0, winreg.KEY_READ)
        num_values = winreg.QueryInfoKey(k)[1]
        for i in range(num_values):
            try:
                name, val, _ = winreg.EnumValue(k, i)
                items.append({
                    "name": name,
                    "command": val,
                    "location": "Disabled by INFINITY",
                    "is_enabled": False,
                    "hive_id": "HKCU",
                    "subkey": DISABLED_BACKUP_KEY
                })
            except Exception:
                continue
        winreg.CloseKey(k)
    except Exception:
        pass

    return items

def toggle_startup_item(name: str, enable: bool) -> Dict[str, Any]:
    """Safely disable or enable an autostart item."""
    if not enable:
        # Move from HKCU/HKLM to Disabled Backup
        # Try finding in HKCU first
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            val, _ = winreg.QueryValueEx(k, name)
            winreg.DeleteValue(k, name)
            winreg.CloseKey(k)

            # Store in backup
            k_bak = winreg.CreateKey(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY)
            winreg.SetValueEx(k_bak, name, 0, winreg.REG_SZ, val)
            winreg.CloseKey(k_bak)

            record_change("Startup Manager", f"Disable Startup: {name}", val, "Disabled", "SUCCESS")
            return {"result": "SUCCESS", "item": name, "enabled": False}
        except Exception as e:
            return {"result": "FAILED", "error": str(e)}
    else:
        # Restore from Disabled Backup to HKCU Run
        try:
            k_bak = winreg.OpenKey(winreg.HKEY_CURRENT_USER, DISABLED_BACKUP_KEY, 0, winreg.KEY_ALL_ACCESS)
            val, _ = winreg.QueryValueEx(k_bak, name)
            winreg.DeleteValue(k_bak, name)
            winreg.CloseKey(k_bak)

            k_run = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            winreg.SetValueEx(k_run, name, 0, winreg.REG_SZ, val)
            winreg.CloseKey(k_run)

            record_change("Startup Manager", f"Enable Startup: {name}", "Disabled", val, "SUCCESS")
            return {"result": "SUCCESS", "item": name, "enabled": True}
        except Exception as e:
            return {"result": "FAILED", "error": str(e)}
