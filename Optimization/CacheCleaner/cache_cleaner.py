"""
Comprehensive Storage & Cache Cleaner for INFINITY Tweaker.
Performs real scanning, size calculation, safe cleaning, and detailed audit reporting.
"""
import os
import shutil
from typing import Dict, Any, List
from Core.Utilities.win_api import query_recycle_bin, empty_recycle_bin
from Core.Logging.logger import get_logger
from Restore.change_history import record_change

logger = get_logger()

def _scan_directory(path: str) -> Dict[str, Any]:
    total_bytes = 0
    file_count = 0
    if not os.path.exists(path):
        return {"bytes": 0, "count": 0, "path": path, "exists": False}
    
    try:
        for root, dirs, files in os.walk(path, topdown=True, onerror=None):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    if not os.path.islink(fp):
                        total_bytes += os.path.getsize(fp)
                        file_count += 1
                except (PermissionError, OSError):
                    continue
    except Exception:
        pass

    return {
        "bytes": total_bytes,
        "count": file_count,
        "path": path,
        "exists": True
    }

def _clean_directory(path: str) -> Dict[str, Any]:
    cleaned_bytes = 0
    deleted_files = 0
    failed_files = 0

    if not os.path.exists(path):
        return {"cleaned_bytes": 0, "deleted_count": 0, "failed_count": 0, "result": "NOT_SUPPORTED"}

    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            fp = os.path.join(root, f)
            try:
                size = os.path.getsize(fp)
                os.remove(fp)
                cleaned_bytes += size
                deleted_files += 1
            except (PermissionError, OSError):
                failed_files += 1

        for d in dirs:
            dp = os.path.join(root, d)
            try:
                os.rmdir(dp)
            except (PermissionError, OSError):
                pass

    res_status = "SUCCESS" if failed_files == 0 and deleted_files > 0 else ("PARTIAL SUCCESS" if deleted_files > 0 else ("SUCCESS" if deleted_files == 0 else "FAILED"))
    return {
        "cleaned_bytes": cleaned_bytes,
        "deleted_count": deleted_files,
        "failed_count": failed_files,
        "result": res_status
    }

class CacheCleaner:
    @staticmethod
    def get_cleaner_targets() -> Dict[str, List[str]]:
        local_app = os.environ.get("LOCALAPPDATA", "")
        app_data = os.environ.get("APPDATA", "")
        user_temp = os.environ.get("TEMP", "")
        win_dir = os.environ.get("WINDIR", "C:\\Windows")

        return {
            "user_temp": [user_temp] if user_temp else [],
            "windows_temp": [os.path.join(win_dir, "Temp")],
            "shader_cache": [
                os.path.join(local_app, "D3DSCache"),
                os.path.join(local_app, "NVIDIA", "DXCache"),
                os.path.join(local_app, "NVIDIA", "GLCache"),
                os.path.join(local_app, "AMD", "DxCache"),
                os.path.join(local_app, "Intel", "ShaderCache")
            ],
            "browser_cache": [
                os.path.join(local_app, "Google", "Chrome", "User Data", "Default", "Cache"),
                os.path.join(local_app, "Microsoft", "Edge", "User Data", "Default", "Cache"),
                os.path.join(local_app, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Cache"),
                os.path.join(local_app, "Mozilla", "Firefox", "Profiles")
            ],
            "windows_logs": [
                os.path.join(win_dir, "Logs"),
                os.path.join(local_app, "CrashDumps")
            ]
        }

    @classmethod
    def scan_all(cls) -> Dict[str, Any]:
        targets = cls.get_cleaner_targets()
        results = {}
        total_scan_bytes = 0
        total_scan_files = 0

        for cat, paths in targets.items():
            cat_bytes = 0
            cat_files = 0
            for p in paths:
                scan = _scan_directory(p)
                cat_bytes += scan["bytes"]
                cat_files += scan["count"]

            results[cat] = {
                "bytes": cat_bytes,
                "mb": round(cat_bytes / (1024 * 1024), 2),
                "count": cat_files
            }
            total_scan_bytes += cat_bytes
            total_scan_files += cat_files

        # Scan Recycle Bin
        rb = query_recycle_bin()
        results["recycle_bin"] = {
            "bytes": rb["total_bytes"],
            "mb": round(rb["total_bytes"] / (1024 * 1024), 2),
            "count": rb["num_items"]
        }
        total_scan_bytes += rb["total_bytes"]
        total_scan_files += rb["num_items"]

        # Prefetch status (informative, safe policy)
        results["prefetch"] = {
            "status": "MANAGED BY WINDOWS",
            "message": "Windows Superfetch/SysMain automatically indexes prefetch files for optimal app loading. Blind deletion is technically counterproductive."
        }

        results["total"] = {
            "bytes": total_scan_bytes,
            "mb": round(total_scan_bytes / (1024 * 1024), 2),
            "count": total_scan_files
        }
        return results

    @classmethod
    def clean_category(cls, category: str) -> Dict[str, Any]:
        targets = cls.get_cleaner_targets()
        if category == "recycle_bin":
            success = empty_recycle_bin()
            res_str = "SUCCESS" if success else "FAILED"
            record_change("CacheCleaner", "RecycleBin", "Full", "Empty", res_str)
            return {"category": "recycle_bin", "result": res_str, "cleaned_mb": 0}

        if category not in targets:
            return {"category": category, "result": "NOT_SUPPORTED", "message": "Unknown category"}

        total_cleaned = 0
        total_deleted = 0
        total_failed = 0

        for path in targets[category]:
            report = _clean_directory(path)
            total_cleaned += report["cleaned_bytes"]
            total_deleted += report["deleted_count"]
            total_failed += report["failed_count"]

        status = "SUCCESS" if total_failed == 0 and total_deleted > 0 else ("PARTIAL SUCCESS" if total_deleted > 0 else ("SUCCESS" if total_deleted == 0 else "FAILED"))
        cleaned_mb = round(total_cleaned / (1024 * 1024), 2)
        
        record_change("CacheCleaner", category, "Uncleaned", f"{cleaned_mb} MB Cleaned", status, f"Deleted {total_deleted} files, {total_failed} locked/skipped")

        return {
            "category": category,
            "result": status,
            "cleaned_bytes": total_cleaned,
            "cleaned_mb": cleaned_mb,
            "deleted_count": total_deleted,
            "failed_count": total_failed
        }

    @classmethod
    def clean_all(cls) -> Dict[str, Any]:
        results = {}
        total_mb = 0
        categories = ["user_temp", "windows_temp", "shader_cache", "browser_cache", "recycle_bin"]
        for cat in categories:
            res = cls.clean_category(cat)
            results[cat] = res
            total_mb += res.get("cleaned_mb", 0)

        results["total_cleaned_mb"] = round(total_mb, 2)
        return results
