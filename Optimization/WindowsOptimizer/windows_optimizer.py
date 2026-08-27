"""
Windows Gaming Optimizer: Fine-tunes Game Mode, DVR, Multimedia SystemProfile, and latency registry flags.
Every optimization supports inspection, risk profiling, safe application, and rollback.
"""
import winreg
from typing import Dict, Any, List
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

TWEAKS_REGISTRY_MAP = [
    {
        "id": "game_mode",
        "name": "Windows Game Mode",
        "category": "RECOMMENDED",
        "risk": "NONE",
        "description": "Prioritizes CPU and GPU resources for active gaming processes while suspending low-priority background tasks.",
        "hive": winreg.HKEY_CURRENT_USER,
        "key_path": r"Software\Microsoft\GameBar",
        "val_name": "AllowAutoGameMode",
        "type": winreg.REG_DWORD,
        "target_value": 1,
        "default_value": 1
    },
    {
        "id": "disable_game_dvr",
        "name": "Disable Background Game DVR Recording",
        "category": "RECOMMENDED",
        "risk": "LOW",
        "description": "Disables constant background video encoding buffer in Windows Game Bar, saving GPU encoder bandwidth and CPU cycles.",
        "hive": winreg.HKEY_CURRENT_USER,
        "key_path": r"System\GameConfigStore",
        "val_name": "GameDVR_Enabled",
        "type": winreg.REG_DWORD,
        "target_value": 0,
        "default_value": 1
    },
    {
        "id": "system_responsiveness",
        "name": "Multimedia Gaming Latency Index",
        "category": "ADVANCED",
        "risk": "LOW",
        "description": "Reduces Windows Multimedia scheduler CPU reserve from default 20% down to 10%, giving 90% priority to gaming threads.",
        "hive": winreg.HKEY_LOCAL_MACHINE,
        "key_path": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "val_name": "SystemResponsiveness",
        "type": winreg.REG_DWORD,
        "target_value": 10,
        "default_value": 20
    },
    {
        "id": "network_throttling_disable",
        "name": "Disable Network Multimedia Throttling",
        "category": "ADVANCED",
        "risk": "LOW",
        "description": "Disables Windows packet throttling on high throughput network sockets during media playback.",
        "hive": winreg.HKEY_LOCAL_MACHINE,
        "key_path": r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "val_name": "NetworkThrottlingIndex",
        "type": winreg.REG_DWORD,
        "target_value": 0xFFFFFFFF,
        "default_value": 10
    },
    {
        "id": "priority_separation",
        "name": "Foreground Process Quantum Priority",
        "category": "EXPERIMENTAL",
        "risk": "MEDIUM",
        "description": "Configures Win32 priority separation to give short, variable high-priority quanta to foreground games.",
        "hive": winreg.HKEY_LOCAL_MACHINE,
        "key_path": r"SYSTEM\CurrentControlSet\Control\PriorityControl",
        "val_name": "Win32PrioritySeparation",
        "type": winreg.REG_DWORD,
        "target_value": 38,
        "default_value": 2
    }
]

def get_windows_tweaks_status() -> List[Dict[str, Any]]:
    """Scan and return status of all supported Windows tweaks."""
    results = []
    for tweak in TWEAKS_REGISTRY_MAP:
        current_val = None
        is_applied = False
        try:
            k = winreg.OpenKey(tweak["hive"], tweak["key_path"], 0, winreg.KEY_READ)
            current_val, _ = winreg.QueryValueEx(k, tweak["val_name"])
            winreg.CloseKey(k)
            is_applied = (current_val == tweak["target_value"])
        except Exception:
            current_val = "Not Set (Default)"

        results.append({
            "id": tweak["id"],
            "name": tweak["name"],
            "category": tweak["category"],
            "risk": tweak["risk"],
            "description": tweak["description"],
            "current_value": current_val,
            "target_value": tweak["target_value"],
            "is_applied": is_applied
        })
    return results

def apply_tweak(tweak_id: str, enable: bool = True) -> Dict[str, Any]:
    """Apply or restore a specific Windows registry tweak."""
    target_tweak = next((t for t in TWEAKS_REGISTRY_MAP if t["id"] == tweak_id), None)
    if not target_tweak:
        return {"result": "NOT_SUPPORTED", "message": f"Tweak ID {tweak_id} not found"}

    val_to_set = target_tweak["target_value"] if enable else target_tweak["default_value"]

    try:
        k = winreg.CreateKeyEx(target_tweak["hive"], target_tweak["key_path"], 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
        
        # Read old value for change history
        old_val = "Default"
        try:
            old_val, _ = winreg.QueryValueEx(k, target_tweak["val_name"])
        except Exception:
            pass

        winreg.SetValueEx(k, target_tweak["val_name"], 0, target_tweak["type"], val_to_set)
        winreg.CloseKey(k)

        status = "SUCCESS"
        record_change(
            feature="Windows Optimizer",
            setting=target_tweak["name"],
            prev_val=old_val,
            new_val=val_to_set,
            result=status,
            details=f"State: {'Enabled' if enable else 'Restored'}"
        )

        return {
            "result": status,
            "tweak_id": tweak_id,
            "name": target_tweak["name"],
            "applied_value": val_to_set
        }
    except PermissionError:
        record_change("Windows Optimizer", target_tweak["name"], "N/A", val_to_set, "FAILED", "Access Denied: Requires Administrator privileges")
        return {"result": "FAILED", "error": "Administrator privileges required to modify this setting."}
    except Exception as e:
        record_change("Windows Optimizer", target_tweak["name"], "N/A", val_to_set, "FAILED", str(e))
        return {"result": "FAILED", "error": str(e)}
