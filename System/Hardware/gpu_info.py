"""
GPU hardware detection, VRAM capacity, driver details, and vendor identification (NVIDIA, AMD, Intel).
"""
import subprocess
import json
import re
from typing import Dict, Any, List
from Core.Logging.logger import get_logger

logger = get_logger()

def _get_nvidia_smi_data() -> Dict[str, Any]:
    """Query nvidia-smi for NVIDIA GPUs if available."""
    try:
        cmd = "nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader,nounits"
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=2)
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if lines:
            parts = [p.strip() for p in lines[0].split(',')]
            if len(parts) >= 7:
                return {
                    "vendor": "NVIDIA",
                    "name": parts[0],
                    "driver_version": parts[1],
                    "vram_total_mb": float(parts[2]),
                    "vram_used_mb": float(parts[3]),
                    "vram_free_mb": float(parts[4]),
                    "usage_pct": float(parts[5]),
                    "temperature_c": float(parts[6]),
                    "source": "nvidia-smi"
                }
    except Exception:
        pass
    return {}

def _get_wmi_gpu_data() -> List[Dict[str, Any]]:
    """Fallback to Windows CIM Win32_VideoController query."""
    gpus = []
    try:
        cmd = "powershell -NoProfile -Command \"Get-CimInstance -Class Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM, VideoProcessor | ConvertTo-Json\""
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=4)
        if out.strip():
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                name = item.get("Name", "Generic Display Adapter")
                vendor = "Unknown"
                if "NVIDIA" in name.upper():
                    vendor = "NVIDIA"
                elif "AMD" in name.upper() or "RADEON" in name.upper():
                    vendor = "AMD"
                elif "INTEL" in name.upper():
                    vendor = "Intel"

                vram_bytes = item.get("AdapterRAM") or 0
                vram_mb = round(vram_bytes / (1024 * 1024), 1) if vram_bytes > 0 else 0.0

                gpus.append({
                    "vendor": vendor,
                    "name": name,
                    "driver_version": item.get("DriverVersion", "Unknown"),
                    "vram_total_mb": vram_mb,
                    "vram_used_mb": 0.0,
                    "vram_free_mb": vram_mb,
                    "usage_pct": 0.0,
                    "temperature_c": None,
                    "source": "Win32_VideoController"
                })
    except Exception as e:
        logger.debug(f"WMI GPU detection error: {e}")
    return gpus

def get_gpu_telemetry() -> Dict[str, Any]:
    """Get active primary gaming GPU details."""
    # First try NVIDIA-specific SMI
    nv = _get_nvidia_smi_data()
    if nv:
        return nv

    # Fallback to WMI
    wmi_gpus = _get_wmi_gpu_data()
    if wmi_gpus:
        # Prefer dedicated GPU (NVIDIA / AMD) over integrated Intel if both exist
        for gpu in wmi_gpus:
            if gpu["vendor"] in ["NVIDIA", "AMD"]:
                return gpu
        return wmi_gpus[0]

    return {
        "vendor": "NOT AVAILABLE",
        "name": "NOT AVAILABLE",
        "driver_version": "NOT AVAILABLE",
        "vram_total_mb": 0.0,
        "vram_used_mb": 0.0,
        "vram_free_mb": 0.0,
        "usage_pct": 0.0,
        "temperature_c": None,
        "source": "None"
    }
