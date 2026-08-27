"""
Physical and virtual RAM telemetry, pagefile metrics, and top memory-consuming processes.
"""
import psutil
from typing import Dict, Any, List
from Core.Utilities.win_api import get_native_memory_status

def get_ram_telemetry() -> Dict[str, Any]:
    """Return comprehensive RAM metrics."""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    native_stat = get_native_memory_status()

    total_gb = round(vm.total / (1024 ** 3), 2)
    used_gb = round(vm.used / (1024 ** 3), 2)
    avail_gb = round(vm.available / (1024 ** 3), 2)

    return {
        "total_gb": total_gb,
        "used_gb": used_gb,
        "available_gb": avail_gb,
        "usage_pct": vm.percent,
        "total_bytes": vm.total,
        "used_bytes": vm.used,
        "available_bytes": vm.available,
        "swap_total_gb": round(swap.total / (1024 ** 3), 2),
        "swap_used_gb": round(swap.used / (1024 ** 3), 2),
        "swap_pct": swap.percent,
        "native_load_pct": native_stat.get("load_pct", vm.percent)
    }

def get_top_memory_processes(limit: int = 8) -> List[Dict[str, Any]]:
    """Enumerate top memory-consuming userland processes."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'cpu_percent']):
        try:
            info = p.info
            mem_bytes = info['memory_info'].rss if info.get('memory_info') else 0
            procs.append({
                "pid": info['pid'],
                "name": info['name'] or f"PID-{info['pid']}",
                "memory_mb": round(mem_bytes / (1024 * 1024), 1),
                "memory_pct": round(info.get('memory_percent', 0.0), 1),
                "cpu_pct": round(info.get('cpu_percent', 0.0), 1)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x['memory_mb'], reverse=True)
    return procs[:limit]
