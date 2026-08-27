"""
Windows Services Manager for Gaming Optimization.
Enforces strict protection of critical system services while offering safe toggling of optional telemetry and background tasks.
"""
import subprocess
import json
from typing import Dict, Any, List, Optional
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

# Hardcoded protected blacklist - CANNOT be disabled by INFINITY Tweaker
PROTECTED_SERVICES = {
    "rpcss", "dcomlaunch", "lsass", "samss", "winlogon", "windefend", "mpssvc",
    "dhcp", "dnscache", "audiosrv", "audioendpointbuilder", "plugplay", "eventlog",
    "cryptsvc", "lanmanworkstation", "lanmanserver", "profsvc", "gpsvc", "bfe"
}

# Known optional services that can be safely paused for gaming
RECOMMENDED_GAMING_SERVICES = [
    {
        "name": "SysMain",
        "recommended_startup": "Manual",
        "description": "Maintains and improves system performance over time by preloading apps. Disabling can reduce random disk hitches during gaming on SSDs."
    },
    {
        "name": "DiagTrack",
        "recommended_startup": "Disabled",
        "description": "Connected User Experiences and Diagnostic Telemetry. Sends usage data to Microsoft."
    },
    {
        "name": "WSearch",
        "recommended_startup": "Manual",
        "description": "Windows Search indexing service. Can trigger background drive I/O while gaming."
    },
    {
        "name": "XblAuthManager",
        "recommended_startup": "Manual",
        "description": "Xbox Live Auth Manager. Only needed if using Xbox app or Xbox Live games."
    }
]

def list_services() -> List[Dict[str, Any]]:
    """Query all installed Windows services via PowerShell CIM."""
    services = []
    try:
        cmd = """powershell -NoProfile -Command "Get-CimInstance Win32_Service | Select-Object Name, DisplayName, State, StartMode, Description | ConvertTo-Json -Depth 2" """
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=8)
        if out.strip():
            items = json.loads(out)
            if isinstance(items, dict):
                items = [items]
            for item in items:
                name = item.get("Name") or ""
                is_protected = name.lower() in PROTECTED_SERVICES
                is_gaming_target = any(g["name"].lower() == name.lower() for g in RECOMMENDED_GAMING_SERVICES)

                services.append({
                    "name": name,
                    "display_name": item.get("DisplayName") or name,
                    "status": item.get("State") or "Unknown",
                    "startup_type": item.get("StartMode") or "Unknown",
                    "description": item.get("Description") or "No description available",
                    "is_protected": is_protected,
                    "is_gaming_target": is_gaming_target
                })
    except Exception as e:
        logger.error(f"Error listing services: {e}")

    # Sort so recommended gaming targets and active services come first
    services.sort(key=lambda s: (not s["is_gaming_target"], s["is_protected"], s["name"]))
    return services

def change_service_startup(service_name: str, startup_type: str) -> Dict[str, Any]:
    """
    Safely modify service startup type (Auto, Demand/Manual, Disabled).
    Rejects changes to protected critical system services.
    """
    name_clean = service_name.lower().strip()
    if name_clean in PROTECTED_SERVICES:
        return {
            "result": "NOT_SUPPORTED",
            "message": f"Service '{service_name}' is a critical Windows security/system component and is protected."
        }

    # Map startup types
    # sc config accepts: boot, system, auto, demand, disabled
    mode_map = {
        "automatic": "auto",
        "auto": "auto",
        "manual": "demand",
        "demand": "demand",
        "disabled": "disabled"
    }
    sc_type = mode_map.get(startup_type.lower(), "demand")

    try:
        # Get previous state for logging
        cmd_prev = f"sc qc {service_name}"
        prev_out = subprocess.check_output(cmd_prev, shell=True, text=True, stderr=subprocess.DEVNULL)
        
        # Execute modification
        cmd = f"sc config {service_name} start= {sc_type}"
        subprocess.check_call(cmd, shell=True)

        record_change(
            feature="Services Manager",
            setting=f"Service Startup: {service_name}",
            prev_val="Previous config",
            new_val=sc_type,
            result="SUCCESS"
        )

        return {"result": "SUCCESS", "service": service_name, "new_startup_type": sc_type}
    except subprocess.CalledProcessError as e:
        record_change("Services Manager", f"Service Startup: {service_name}", "N/A", sc_type, "FAILED", "Elevated privileges required")
        return {"result": "FAILED", "error": "Access Denied. Administrator privileges required."}
    except Exception as e:
        return {"result": "FAILED", "error": str(e)}

def control_service(service_name: str, action: str) -> Dict[str, Any]:
    """Start, Stop, or Restart a Windows service."""
    name_clean = service_name.lower().strip()
    if name_clean in PROTECTED_SERVICES and action.lower() in ["stop", "pause"]:
        return {
            "result": "NOT_SUPPORTED",
            "message": f"Stopping critical service '{service_name}' is prohibited."
        }

    act = action.lower()
    try:
        if act == "restart":
            subprocess.call(f"net stop {service_name}", shell=True)
            subprocess.check_call(f"net start {service_name}", shell=True)
        elif act == "start":
            subprocess.check_call(f"net start {service_name}", shell=True)
        elif act == "stop":
            subprocess.check_call(f"net stop {service_name}", shell=True)

        record_change("Services Manager", f"Service State: {service_name}", "Action", act, "SUCCESS")
        return {"result": "SUCCESS", "service": service_name, "action": act}
    except Exception as e:
        return {"result": "FAILED", "error": str(e)}
