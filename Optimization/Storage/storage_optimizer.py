"""
Storage Optimizer: Discovers large space-consuming files (>500MB), analyzes drive fragmentation, and coordinates safe disk cleanup.
Never automatically deletes personal user files.
"""
import os
import subprocess
from typing import Dict, Any, List

def find_large_files(search_paths: List[str] = None, min_size_mb: int = 500, max_results: int = 20) -> List[Dict[str, Any]]:
    """Scan designated folders (Downloads, Videos, Documents) for large space-consuming files."""
    if not search_paths:
        user_profile = os.environ.get("USERPROFILE", "C:\\Users")
        search_paths = [
            os.path.join(user_profile, "Downloads"),
            os.path.join(user_profile, "Videos"),
            os.path.join(user_profile, "Documents")
        ]

    min_bytes = min_size_mb * 1024 * 1024
    large_files = []

    for base_dir in search_paths:
        if not os.path.exists(base_dir):
            continue
        try:
            for root, _, files in os.walk(base_dir):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        if not os.path.islink(fp):
                            size = os.path.getsize(fp)
                            if size >= min_bytes:
                                large_files.append({
                                    "filename": f,
                                    "filepath": fp,
                                    "size_mb": round(size / (1024 * 1024), 1),
                                    "size_gb": round(size / (1024 ** 3), 2),
                                    "extension": os.path.splitext(f)[1].lower()
                                })
                    except (PermissionError, OSError):
                        continue
        except Exception:
            continue

    large_files.sort(key=lambda x: x["size_mb"], reverse=True)
    return large_files[:max_results]

def get_trim_status() -> Dict[str, Any]:
    """Check if Windows NTFS TRIM is active for SSD optimization."""
    try:
        out = subprocess.check_output("fsutil behavior query DisableDeleteNotify", shell=True, text=True, stderr=subprocess.DEVNULL)
        # 0 = TRIM enabled, 1 = TRIM disabled
        is_enabled = "DisableDeleteNotify = 0" in out
        return {
            "trim_supported": True,
            "trim_enabled": is_enabled,
            "message": "SSD TRIM is enabled and actively maintaining drive endurance." if is_enabled else "TRIM appears disabled. Enable TRIM to maintain SSD write speeds."
        }
    except Exception:
        return {"trim_supported": False, "trim_enabled": False, "message": "Could not query TRIM status"}
