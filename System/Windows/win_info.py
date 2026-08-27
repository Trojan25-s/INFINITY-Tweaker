"""
Windows OS specs, Game Mode status, HAGS, DirectX version, display mode and refresh rate.
"""
import winreg
import platform
import subprocess
import ctypes
from typing import Dict, Any

def get_game_mode_status() -> bool:
    """Check if Windows Game Mode is enabled in Registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\GameBar", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "AllowAutoGameMode")
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        # Default in Windows 10/11 is enabled (True)
        return True

def get_hags_status() -> Dict[str, Any]:
    """Check if Hardware Accelerated GPU Scheduling (HAGS) is supported and enabled."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "HwSchMode")
        winreg.CloseKey(key)
        # 2 = Enabled, 1 = Disabled
        return {
            "supported": True,
            "enabled": (val == 2),
            "raw_value": val
        }
    except Exception:
        return {
            "supported": False,
            "enabled": False,
            "raw_value": 0
        }

def get_display_settings() -> Dict[str, Any]:
    """Get active display resolution and refresh rate via user32."""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        
        # Try powershell for refresh rate
        cmd = "powershell -NoProfile -Command \"(Get-CimInstance -Class Win32_VideoController).CurrentRefreshRate\""
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=2)
        hz = 60
        if out.strip():
            hz = int(out.strip().splitlines()[0])
            
        return {
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "refresh_rate_hz": hz
        }
    except Exception:
        return {
            "width": 1920,
            "height": 1080,
            "resolution": "1920x1080",
            "refresh_rate_hz": 60
        }

def get_windows_overview() -> Dict[str, Any]:
    """Get full Windows environment overview."""
    display = get_display_settings()
    game_mode = get_game_mode_status()
    hags = get_hags_status()

    # Motherboard info
    mb_name = "NOT AVAILABLE"
    try:
        cmd = "powershell -NoProfile -Command \"(Get-CimInstance Win32_BaseBoard).Product\""
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=2)
        if out.strip():
            mb_name = out.strip()
    except Exception:
        pass

    return {
        "os_name": f"{platform.system()} {platform.release()}",
        "os_build": platform.version(),
        "architecture": platform.machine(),
        "motherboard": mb_name,
        "directx_version": "DirectX 12 Ultimate" if int(platform.release().split('.')[0] if '.' in platform.release() else 10) >= 10 else "DirectX 11",
        "game_mode_enabled": game_mode,
        "hags": hags,
        "resolution": display["resolution"],
        "refresh_rate": f"{display['refresh_rate_hz']} Hz"
    }
