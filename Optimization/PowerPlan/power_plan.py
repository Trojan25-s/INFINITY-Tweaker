"""
Windows Power Plan scheme switcher and restoration manager.
Supports Balanced, High Performance, and Ultimate Performance (where unlocked/available).
"""
import subprocess
import re
from typing import Dict, Any, List, Optional
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

# Standard Windows Power Scheme GUIDs
KNOWN_SCHEMES = {
    "381b4222-f694-41f0-9685-ff5bb260df2e": "Balanced",
    "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c": "High Performance",
    "e9a42b02-d5df-448d-aa00-03f14749eb61": "Ultimate Performance",
    "a1841308-3541-4fab-bc81-f71556f20b4a": "Power Saver"
}

def get_active_power_plan() -> Dict[str, Any]:
    """Retrieve current active power plan GUID and friendly name."""
    try:
        out = subprocess.check_output("powercfg /getactivescheme", shell=True, text=True, timeout=3)
        match = re.search(r"([a-f0-9\-]{36})", out, re.IGNORECASE)
        if match:
            guid = match.group(1).lower()
            name_match = re.search(r"\((.*?)\)", out)
            name = name_match.group(1) if name_match else KNOWN_SCHEMES.get(guid, "Custom Plan")
            return {"guid": guid, "name": name, "raw": out.strip()}
    except Exception as e:
        logger.error(f"Error querying active power plan: {e}")
    return {"guid": "381b4222-f694-41f0-9685-ff5bb260df2e", "name": "Balanced", "raw": ""}

def list_available_power_plans() -> List[Dict[str, Any]]:
    """List all installed power schemes."""
    plans = []
    try:
        out = subprocess.check_output("powercfg /list", shell=True, text=True, timeout=3)
        for line in out.splitlines():
            match = re.search(r"([a-f0-9\-]{36})", line, re.IGNORECASE)
            if match:
                guid = match.group(1).lower()
                is_active = "*" in line
                name_match = re.search(r"\((.*?)\)", line)
                name = name_match.group(1) if name_match else KNOWN_SCHEMES.get(guid, "Custom Plan")
                plans.append({
                    "guid": guid,
                    "name": name,
                    "is_active": is_active
                })
    except Exception as e:
        logger.error(f"Error listing power plans: {e}")
    return plans

def enable_ultimate_performance_scheme() -> bool:
    """Duplicate Ultimate Performance scheme if not already present on Windows 10/11 Pro/Workstation."""
    try:
        subprocess.check_output(
            "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61",
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=3
        )
        return True
    except Exception:
        return False

def set_power_plan(plan_name_or_guid: str) -> Dict[str, Any]:
    """Switch active power scheme with automatic previous plan logging."""
    current = get_active_power_plan()
    target_guid = plan_name_or_guid.lower()

    if target_guid == "high" or target_guid == "high performance":
        target_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    elif target_guid == "ultimate" or target_guid == "ultimate performance":
        target_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        enable_ultimate_performance_scheme()
    elif target_guid == "balanced":
        target_guid = "381b4222-f694-41f0-9685-ff5bb260df2e"

    try:
        subprocess.check_call(f"powercfg /setactive {target_guid}", shell=True, timeout=3)
        new_active = get_active_power_plan()
        
        record_change(
            feature="Power Plan",
            setting="Active Power Scheme",
            prev_val=f"{current['name']} ({current['guid']})",
            new_val=f"{new_active['name']} ({new_active['guid']})",
            result="SUCCESS"
        )

        return {
            "result": "SUCCESS",
            "previous_plan": current,
            "current_plan": new_active,
            "warning": "High/Ultimate performance power plans keep CPU cores at higher clock states which may marginally increase power consumption and operating temperatures."
        }
    except Exception as e:
        record_change("Power Plan", "Active Power Scheme", current["name"], target_guid, "FAILED", str(e))
        return {
            "result": "FAILED",
            "error": str(e),
            "current_plan": current
        }
