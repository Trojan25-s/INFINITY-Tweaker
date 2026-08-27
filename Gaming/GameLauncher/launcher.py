"""
Game Launcher: Applies pre-launch optimizations, sets safe process priority, tracks playtime, and safely restores state.
Strict adherence to gaming safety: Never touches memory, never injects DLLs, never interferes with anti-cheat.
"""
import subprocess
import threading
import time
import os
import psutil
from typing import Dict, Any, Optional
from Optimization.PowerPlan.power_plan import set_power_plan, get_active_power_plan
from Optimization.RamOptimizer.ram_optimizer import optimize_ram
from Optimization.GpuOptimizer.gpu_optimizer import set_game_gpu_preference
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

# Safe priority mapping - Strictly excludes REALTIME_PRIORITY_CLASS (0x00000100) to protect system stability
PRIORITY_MAP = {
    "NORMAL": psutil.NORMAL_PRIORITY_CLASS,
    "ABOVE_NORMAL": psutil.ABOVE_NORMAL_PRIORITY_CLASS,
    "HIGH": psutil.HIGH_PRIORITY_CLASS
}

_active_game_session = None

def _monitor_game_process(proc: subprocess.Popen, exe_name: str, original_power_plan: str):
    """Background monitor tracking game execution until exit."""
    global _active_game_session
    start_time = time.time()
    
    # Wait for process initialization
    time.sleep(2.0)
    
    # Find matching psutil process to set priority
    target_p = None
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if exe_name.lower() in p.info['name'].lower():
                target_p = p
                break
        except Exception:
            continue

    if target_p:
        try:
            target_p.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info(f"Set safe HIGH priority for {exe_name} (PID: {target_p.pid})")
        except Exception as e:
            logger.warning(f"Could not elevate game process priority: {e}")

    # Block until game terminates
    proc.wait()
    duration = round(time.time() - start_time, 1)
    
    # Restore power plan
    if original_power_plan:
        set_power_plan(original_power_plan)
        logger.info(f"Restored power plan to {original_power_plan}")

    record_change(
        feature="Game Launcher",
        setting=f"Session: {exe_name}",
        prev_val="Running",
        new_val="Terminated",
        result="SUCCESS",
        details=f"Playtime: {duration}s"
    )
    _active_game_session = None

def launch_game(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Launch a registered game profile with pre-flight optimizations."""
    global _active_game_session
    exe_path = profile.get("executable", "")
    if not exe_path or not os.path.exists(exe_path):
        return {"result": "FAILED", "error": f"Executable not found at path: {exe_path}"}

    # 1. Record original power plan
    orig_plan = get_active_power_plan().get("guid", "")

    # 2. Apply Power Plan
    target_power = profile.get("power_profile", "High Performance")
    set_power_plan(target_power)

    # 3. Apply GPU preference
    set_game_gpu_preference(exe_path, preference_level=2)

    # 4. Optional RAM trim before launch
    if profile.get("clean_ram_on_launch", True):
        optimize_ram()

    # 5. Launch Game Process
    args = profile.get("launch_args", "").strip()
    cmd = f'"{exe_path}" {args}'.strip()
    
    try:
        proc = subprocess.Popen(cmd, shell=True)
        exe_name = os.path.basename(exe_path)
        
        _active_game_session = {
            "name": profile.get("name", exe_name),
            "pid": proc.pid,
            "start_time": time.time(),
            "profile": profile
        }

        # Start session monitoring thread
        t = threading.Thread(
            target=_monitor_game_process,
            args=(proc, exe_name, orig_plan),
            daemon=True
        )
        t.start()

        record_change("Game Launcher", f"Launch Game: {profile.get('name')}", "Stopped", "Running", "SUCCESS")
        return {
            "result": "SUCCESS",
            "game_name": profile.get("name"),
            "pid": proc.pid,
            "message": "Game launched with High-Performance profile."
        }
    except Exception as e:
        record_change("Game Launcher", f"Launch Game: {profile.get('name')}", "Stopped", "Failed", "FAILED", str(e))
        return {"result": "FAILED", "error": str(e)}

def get_active_session() -> Optional[Dict[str, Any]]:
    return _active_game_session
