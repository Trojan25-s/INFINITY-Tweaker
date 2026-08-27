"""
AI Recommendations Engine: Formulates prioritized optimization actions with transparent risk, benefits, downsides, and rollback guides.
"""
from typing import Dict, Any, List
from System.Hardware.memory_info import get_ram_telemetry
from System.Windows.win_info import get_windows_overview
from Optimization.WindowsOptimizer.windows_optimizer import get_windows_tweaks_status
from Optimization.PowerPlan.power_plan import get_active_power_plan

def generate_recommendations() -> Dict[str, List[Dict[str, Any]]]:
    """Generate categorized action list based on real system state."""
    ram = get_ram_telemetry()
    win = get_windows_overview()
    tweaks = get_windows_tweaks_status()
    power = get_active_power_plan()

    recommended = []
    advanced = []
    experimental = []

    # 1. Temporary files & Cache
    recommended.append({
        "id": "rec_cache",
        "title": "Clean Temporary Files & Shader Caches",
        "category": "RECOMMENDED",
        "changes": "Removes stale %TEMP% files, shader caches, and temporary web buffers.",
        "expected_benefit": "Recovers drive space and prevents shader compiler cache stalls.",
        "possible_downside": "First launch of some web pages or games may rebuild shaders slightly.",
        "restore_method": "Caches automatically rebuild as applications run."
    })

    # 2. RAM Working Set
    if ram["usage_pct"] > 70:
        recommended.append({
            "id": "rec_ram",
            "title": "Optimize Working Set RAM",
            "category": "RECOMMENDED",
            "changes": "Trims working sets of inactive background applications.",
            "expected_benefit": f"Reclaims memory headroom (currently {ram['usage_pct']}% utilized).",
            "possible_downside": "None. Windows page manager handles memory dynamically.",
            "restore_method": "Applications page memory back in upon activation."
        })

    # 3. Game Mode & DVR
    dvr_tweak = next((t for t in tweaks if t["id"] == "disable_game_dvr"), None)
    if dvr_tweak and not dvr_tweak["is_applied"]:
        recommended.append({
            "id": "rec_dvr",
            "title": "Disable Game DVR Background Capture",
            "category": "RECOMMENDED",
            "changes": "Disables background video encoding buffer in GameConfigStore.",
            "expected_benefit": "Reduces continuous background GPU encoder usage and CPU interrupts.",
            "possible_downside": "Windows Game Bar retrospective clip capture (Win+Alt+G) is disabled.",
            "restore_method": "Toggle back to enabled in Windows Optimizer."
        })

    # 4. Power Plan
    if "high" not in power["name"].lower() and "ultimate" not in power["name"].lower():
        advanced.append({
            "id": "rec_power",
            "title": "Activate High Performance Power Plan",
            "category": "ADVANCED",
            "changes": "Sets minimum CPU frequency state to 100% and unparks CPU cores.",
            "expected_benefit": "Eliminates core frequency ramp-up latency when sudden game action begins.",
            "possible_downside": "Slightly higher idle power draw on desktop PCs.",
            "restore_method": "Switch back to Balanced in Power Plan section."
        })

    # 5. Multimedia Scheduler Latency
    sys_resp = next((t for t in tweaks if t["id"] == "system_responsiveness"), None)
    if sys_resp and not sys_resp["is_applied"]:
        advanced.append({
            "id": "rec_sys_resp",
            "title": "Tune Multimedia SystemResponsiveness",
            "category": "ADVANCED",
            "changes": "Reduces non-gaming multimedia CPU reserve from 20% to 10%.",
            "expected_benefit": "Provides gaming threads with 90% priority scheduling.",
            "possible_downside": "None on modern multi-core CPUs.",
            "restore_method": "Restore default 20% in Windows Optimizer."
        })

    # 6. Experimental Priority Separation
    exp_tweak = next((t for t in tweaks if t["id"] == "priority_separation"), None)
    if exp_tweak and not exp_tweak["is_applied"]:
        experimental.append({
            "id": "rec_quantum",
            "title": "Win32 Foreground Process Priority Separation",
            "category": "EXPERIMENTAL",
            "changes": "Modifies Win32PrioritySeparation to 38 (0x26) for short variable quanta.",
            "expected_benefit": "Maximizes CPU responsiveness for the active foreground window.",
            "possible_downside": "May slightly reduce throughput of heavy background render tasks.",
            "restore_method": "Revert to value 2 in Windows Optimizer."
        })

    return {
        "recommended": recommended,
        "advanced": advanced,
        "experimental": experimental
    }
