"""
Hardware Identification (HWID) generator.
Calculates a unique SHA-256 fingerprint based on Motherboard UUID, CPU ID, and OS Volume serial.
"""
import hashlib
import subprocess
import os
import platform
from Core.Logging.logger import get_logger

logger = get_logger()

def _run_cmd(cmd: str) -> str:
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True, timeout=5)
        return output.strip()
    except Exception:
        return ""

def get_motherboard_uuid() -> str:
    # Try wmic or powershell
    res = _run_cmd("powershell -NoProfile -Command \"(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID\"")
    if res and len(res) > 5 and "error" not in res.lower():
        return res
    res = _run_cmd("wmic csproduct get uuid")
    lines = [line.strip() for line in res.splitlines() if line.strip() and "UUID" not in line]
    if lines:
        return lines[0]
    return "UNKNOWN_MB_UUID"

def get_cpu_id() -> str:
    res = _run_cmd("powershell -NoProfile -Command \"(Get-CimInstance -Class Win32_Processor).ProcessorId\"")
    if res and len(res) > 3:
        return res
    return platform.processor() or "UNKNOWN_CPU_ID"

def get_drive_serial() -> str:
    res = _run_cmd("powershell -NoProfile -Command \"(Get-CimInstance -Class Win32_LogicalDisk -Filter 'DeviceID=\"\"C:\"\"').VolumeSerialNumber\"")
    if res and len(res) > 2:
        return res
    return "UNKNOWN_DRIVE_SERIAL"

def get_hardware_fingerprint() -> str:
    """Generate deterministic, irreversible 64-char SHA-256 hardware identifier."""
    mb = get_motherboard_uuid()
    cpu = get_cpu_id()
    drive = get_drive_serial()
    
    raw = f"INFINITY_HWID|{mb}|{cpu}|{drive}"
    hwid = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    logger.debug(f"Generated HWID fingerprint: {hwid[:16]}...")
    return hwid

def get_machine_name() -> str:
    return platform.node() or "Windows Gaming PC"

def get_os_string() -> str:
    return f"{platform.system()} {platform.release()} (Build {platform.version()})"
