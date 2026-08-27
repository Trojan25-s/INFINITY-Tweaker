"""
Windows Administrator permission check and UAC elevation utilities.
"""
import ctypes
import sys
import os

def is_admin() -> bool:
    """Check if the current process is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def request_elevation():
    """Prompt UAC dialog to restart current process with elevated admin privileges."""
    if is_admin():
        return True
    try:
        # Re-run python script with admin verb
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1  # SW_SHOWNORMAL
        )
        return ret > 32
    except Exception:
        return False
