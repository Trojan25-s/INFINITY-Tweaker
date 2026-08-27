"""
Disk drive health, partitions, free space, and real-time I/O telemetry.
"""
import psutil
from typing import Dict, Any, List

def get_storage_telemetry() -> Dict[str, Any]:
    """Inspect all mounted storage drives and physical disk activity."""
    drives = []
    total_space_all = 0
    used_space_all = 0

    partitions = psutil.disk_partitions(all=False)
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            total_gb = round(usage.total / (1024 ** 3), 1)
            used_gb = round(usage.used / (1024 ** 3), 1)
            free_gb = round(usage.free / (1024 ** 3), 1)
            
            total_space_all += usage.total
            used_space_all += usage.used

            drives.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "opts": p.opts,
                "total_gb": total_gb,
                "used_gb": used_gb,
                "free_gb": free_gb,
                "usage_pct": usage.percent
            })
        except (PermissionError, OSError):
            continue

    io_counters = psutil.disk_io_counters()
    read_mb = round(io_counters.read_bytes / (1024 * 1024), 1) if io_counters else 0.0
    write_mb = round(io_counters.write_bytes / (1024 * 1024), 1) if io_counters else 0.0

    overall_pct = round((used_space_all / total_space_all) * 100, 1) if total_space_all > 0 else 0.0

    return {
        "drives": drives,
        "overall_usage_pct": overall_pct,
        "total_storage_gb": round(total_space_all / (1024 ** 3), 1),
        "used_storage_gb": round(used_space_all / (1024 ** 3), 1),
        "read_mb_lifetime": read_mb,
        "write_mb_lifetime": write_mb
    }
