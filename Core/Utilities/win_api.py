"""
Windows Native Win32 API ctypes structures and system bindings.
"""
import ctypes
from ctypes import wintypes
import os

# --- Memory Status Structures ---
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]

def get_native_memory_status() -> dict:
    """Query high-precision memory status via Kernel32 GlobalMemoryStatusEx."""
    kernel32 = ctypes.windll.kernel32
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
        return {
            "load_pct": stat.dwMemoryLoad,
            "total_phys_bytes": stat.ullTotalPhys,
            "avail_phys_bytes": stat.ullAvailPhys,
            "used_phys_bytes": stat.ullTotalPhys - stat.ullAvailPhys,
            "total_page_bytes": stat.ullTotalPageFile,
            "avail_page_bytes": stat.ullAvailPageFile,
            "total_virt_bytes": stat.ullTotalVirtual,
            "avail_virt_bytes": stat.ullAvailVirtual
        }
    return {}

# --- Working Set Trimming ---
def empty_process_working_set(pid: int) -> bool:
    """Trim working set for a process using psapi.EmptyWorkingSet."""
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_SET_QUOTA = 0x0100
    
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA, False, pid)
    if not h_proc:
        return False
    try:
        ret = psapi.EmptyWorkingSet(h_proc)
        return bool(ret)
    finally:
        kernel32.CloseHandle(h_proc)

# --- Recycle Bin Query & Empty ---
class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]

def query_recycle_bin(drive_letter: str = "C:\\") -> dict:
    shell32 = ctypes.windll.shell32
    rb_info = SHQUERYRBINFO()
    rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    res = shell32.SHQueryRecycleBinW(drive_letter, ctypes.byref(rb_info))
    if res == 0:
        return {
            "total_bytes": rb_info.i64Size,
            "num_items": rb_info.i64NumItems
        }
    return {"total_bytes": 0, "num_items": 0}

def empty_recycle_bin(drive_letter: str = None) -> bool:
    """
    Empty Windows Recycle Bin via Shell32 SHEmptyRecycleBinW.
    Flags: SHERB_NOCONFIRMATION (0x1) | SHERB_NOPROGRESSUI (0x2) | SHERB_NOSOUND (0x4)
    """
    SHERB_NOCONFIRMATION = 0x00000001
    SHERB_NOPROGRESSUI = 0x00000002
    SHERB_NOSOUND = 0x00000004
    flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
    
    shell32 = ctypes.windll.shell32
    res = shell32.SHEmptyRecycleBinW(None, drive_letter, flags)
    return res == 0
