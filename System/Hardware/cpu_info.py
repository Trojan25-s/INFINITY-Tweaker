"""
CPU telemetry and architecture inspection using native psutil and Windows CIM.
"""
import psutil
import platform
import subprocess
from typing import Dict, Any, List

def get_cpu_telemetry() -> Dict[str, Any]:
    """Retrieve real-time CPU performance metrics and static hardware specs."""
    freq = psutil.cpu_freq()
    per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
    total_cpu = psutil.cpu_percent(interval=None)

    brand = platform.processor() or "AMD / Intel Processor"
    
    # Try getting marketing brand string via powershell if available
    try:
        cmd = "powershell -NoProfile -Command \"(Get-CimInstance -Class Win32_Processor).Name\""
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=3)
        if out.strip():
            brand = out.strip().splitlines()[0]
    except Exception:
        pass

    return {
        "brand": brand,
        "architecture": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False) or 4,
        "logical_threads": psutil.cpu_count(logical=True) or 8,
        "current_frequency_mhz": round(freq.current, 1) if freq else 0.0,
        "max_frequency_mhz": round(freq.max, 1) if freq else 0.0,
        "usage_pct": total_cpu,
        "per_core_usage": per_cpu,
        "context_switches": psutil.cpu_stats().ctx_switches if hasattr(psutil, 'cpu_stats') else 0,
        "interrupts": psutil.cpu_stats().interrupts if hasattr(psutil, 'cpu_stats') else 0
    }
