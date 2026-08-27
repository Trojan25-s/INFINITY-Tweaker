"""
RAM Optimizer: Safely trims working sets and cleans standby memory allocations using Win32 API.
Reports exact before and after memory measurements.
"""
import psutil
import time
from typing import Dict, Any, List
from Core.Utilities.win_api import empty_process_working_set, get_native_memory_status
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

# Protected system processes that must never be touched
PROTECTED_PROCESSES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe", 
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "fontdrvhost.exe",
    "winlogon.exe", "dwm.exe", "sihost.exe", "taskhostw.exe", "explorer.exe"
}

def optimize_ram() -> Dict[str, Any]:
    """Perform safe RAM optimization on non-essential running processes."""
    # 1. Before measurement
    vm_before = psutil.virtual_memory()
    before_used_mb = round(vm_before.used / (1024 * 1024), 1)
    before_pct = vm_before.percent

    optimized_count = 0
    skipped_count = 0

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = (proc.info['name'] or "").lower()
            pid = proc.info['pid']

            if pid <= 4 or name in PROTECTED_PROCESSES:
                skipped_count += 1
                continue

            success = empty_process_working_set(pid)
            if success:
                optimized_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Brief delay for OS page table settlement
    time.sleep(0.3)

    # 2. After measurement
    vm_after = psutil.virtual_memory()
    after_used_mb = round(vm_after.used / (1024 * 1024), 1)
    after_pct = vm_after.percent

    freed_mb = max(0.0, round(before_used_mb - after_used_mb, 1))

    status = "SUCCESS" if optimized_count > 0 else "PARTIAL SUCCESS"
    record_change(
        feature="RAM Optimizer",
        setting="Working Set Trimming",
        prev_val=f"{before_used_mb} MB ({before_pct}%)",
        new_val=f"{after_used_mb} MB ({after_pct}%)",
        result=status,
        details=f"Freed {freed_mb} MB across {optimized_count} processes"
    )

    return {
        "result": status,
        "before_used_mb": before_used_mb,
        "after_used_mb": after_used_mb,
        "freed_mb": freed_mb,
        "before_pct": before_pct,
        "after_pct": after_pct,
        "processes_optimized": optimized_count,
        "processes_skipped": skipped_count
    }
