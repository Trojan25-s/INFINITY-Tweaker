"""
GPU Optimization Engine: Configures High-Performance GPU preferences, DirectX graphics hints, and shader cache parameters.
"""
import winreg
import os
from typing import Dict, Any, List
from System.Hardware.gpu_info import get_gpu_telemetry
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

DIRECTX_GPU_PREFS_KEY = r"Software\Microsoft\DirectX\UserGpuPreferences"

def set_game_gpu_preference(executable_path: str, preference_level: int = 2) -> Dict[str, Any]:
    """
    Set Windows Graphics Preference for an executable.
    0 = Let Windows decide
    1 = Power saving
    2 = High performance (Dedicated GPU)
    """
    if not os.path.exists(executable_path) and not executable_path.endswith('.exe'):
        return {"result": "FAILED", "message": "Executable not found"}

    value_str = f"GpuPreference={preference_level};"
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, DIRECTX_GPU_PREFS_KEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ)
        
        # Read old value if exists
        prev_val = "Default"
        try:
            prev_val, _ = winreg.QueryValueEx(key, executable_path)
        except Exception:
            pass

        winreg.SetValueEx(key, executable_path, 0, winreg.REG_SZ, value_str)
        winreg.CloseKey(key)

        record_change(
            feature="GPU Optimizer",
            setting=f"DirectX GPU Preference ({os.path.basename(executable_path)})",
            prev_val=prev_val,
            new_val=value_str,
            result="SUCCESS"
        )

        return {
            "result": "SUCCESS",
            "executable": executable_path,
            "gpu_preference": "High Performance" if preference_level == 2 else "Power Saving"
        }
    except Exception as e:
        record_change("GPU Optimizer", "DirectX GPU Preference", "Default", value_str, "FAILED", str(e))
        return {"result": "FAILED", "error": str(e)}

def get_gpu_optimization_status() -> Dict[str, Any]:
    """Analyze current GPU vendor configuration and supported tweaks."""
    gpu = get_gpu_telemetry()
    vendor = gpu.get("vendor", "Unknown")

    recommendations = []
    if vendor == "NVIDIA":
        recommendations.append({
            "title": "NVIDIA Shader Cache Size",
            "description": "Ensure Shader Cache is set to 10GB or Unlimited in NVIDIA Control Panel for modern open-world titles.",
            "risk": "None"
        })
        recommendations.append({
            "title": "Power Management Mode",
            "description": "Set to 'Prefer maximum performance' on high-end desktop rigs during gaming.",
            "risk": "Low"
        })
    elif vendor == "AMD":
        recommendations.append({
            "title": "AMD Radeon Anti-Lag",
            "description": "Reduces input latency by pacing CPU frame production with GPU render pipeline.",
            "risk": "None"
        })
    elif vendor == "Intel":
        recommendations.append({
            "title": "Intel Arc / Iris Xe Performance Mode",
            "description": "Verify high performance graphics power allocation in Windows Graphics Settings.",
            "risk": "Low"
        })

    return {
        "active_gpu": gpu,
        "vendor": vendor,
        "recommendations": recommendations,
        "directx_hags_supported": True
    }
