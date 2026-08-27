"""
Driver Center: Discovers installed display, audio, network, and chipset drivers.
"""
import subprocess
import json
from typing import Dict, Any, List
from Core.Logging.logger import get_logger

logger = get_logger()

def get_installed_drivers() -> Dict[str, Any]:
    """Retrieve verified driver versions from Windows Driver Store."""
    drivers_summary = {
        "display": [],
        "audio": [],
        "network": [],
        "chipset": []
    }
    try:
        cmd = """powershell -NoProfile -Command "Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceClass -in @('DISPLAY', 'MEDIA', 'NET', 'SYSTEM') -and $_.DeviceName -ne $null } | Select-Object DeviceName, DeviceClass, DriverVersion, DriverDate, Manufacturer | ConvertTo-Json -Depth 2" """
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=6)
        if out.strip():
            items = json.loads(out)
            if isinstance(items, dict):
                items = [items]
            
            for d in items:
                cls = (d.get("DeviceClass") or "").upper()
                name = d.get("DeviceName") or "Unknown Device"
                ver = d.get("DriverVersion") or "Unknown"
                mfg = d.get("Manufacturer") or "Unknown"
                date_str = str(d.get("DriverDate") or "")[:10]

                entry = {
                    "device_name": name,
                    "version": ver,
                    "manufacturer": mfg,
                    "date": date_str
                }

                if cls == "DISPLAY":
                    drivers_summary["display"].append(entry)
                elif cls == "MEDIA":
                    drivers_summary["audio"].append(entry)
                elif cls == "NET":
                    drivers_summary["network"].append(entry)
                elif cls == "SYSTEM":
                    # Filter for chipset-relevant drivers
                    if any(k in name.upper() for k in ["CHIPSET", "PCI", "SMBUS", "BRIDGE", "IO"]):
                        drivers_summary["chipset"].append(entry)
    except Exception as e:
        logger.debug(f"Driver scan error: {e}")

    return drivers_summary
