"""
INFINITY Bottleneck Analyzer and Performance Scoring Engine.
Calculates the real INFINITY Performance Score (0-100) based on detected hardware, load, and configuration.
"""
import psutil
from typing import Dict, Any, List
from System.Hardware.cpu_info import get_cpu_telemetry
from System.Hardware.gpu_info import get_gpu_telemetry
from System.Hardware.memory_info import get_ram_telemetry
from System.Hardware.storage_info import get_storage_telemetry
from System.Windows.win_info import get_windows_overview

def calculate_performance_score() -> Dict[str, Any]:
    """
    Calculate authentic INFINITY Performance Score from actual hardware metrics.
    Formula:
    Score = 0.25*CPU + 0.25*GPU + 0.20*RAM + 0.15*Storage + 0.15*Windows
    """
    cpu = get_cpu_telemetry()
    gpu = get_gpu_telemetry()
    ram = get_ram_telemetry()
    storage = get_storage_telemetry()
    win = get_windows_overview()

    # CPU Score calculation (Cores, Freq, Load headroom)
    cores = cpu.get("physical_cores", 4)
    freq = cpu.get("current_frequency_mhz", 2400)
    cpu_load = cpu.get("usage_pct", 20.0)
    
    cpu_base = min(40.0, cores * 8.0) + min(30.0, (freq / 4500.0) * 30.0)
    cpu_headroom = max(0.0, (100.0 - cpu_load) * 0.3)
    cpu_score = round(min(100.0, cpu_base + cpu_headroom))

    # GPU Score calculation (VRAM, Vendor)
    vram_mb = gpu.get("vram_total_mb", 4096.0)
    gpu_score = 60
    if vram_mb >= 16000:
        gpu_score = 98
    elif vram_mb >= 12000:
        gpu_score = 92
    elif vram_mb >= 8000:
        gpu_score = 85
    elif vram_mb >= 6000:
        gpu_score = 78
    elif vram_mb >= 4000:
        gpu_score = 70

    # RAM Score calculation (Total GB & Available headroom)
    total_ram_gb = ram.get("total_gb", 16.0)
    ram_load = ram.get("usage_pct", 50.0)
    ram_base = 50
    if total_ram_gb >= 64:
        ram_base = 70
    elif total_ram_gb >= 32:
        ram_base = 65
    elif total_ram_gb >= 16:
        ram_base = 55
    else:
        ram_base = 40
    ram_headroom = max(0.0, (100.0 - ram_load) * 0.35)
    ram_score = round(min(100.0, ram_base + ram_headroom))

    # Storage Score calculation (Free space percentage)
    storage_load = storage.get("overall_usage_pct", 50.0)
    storage_score = round(max(30.0, 100.0 - (storage_load * 0.5)))

    # Windows OS score (Game Mode active, HAGS)
    win_score = 75
    if win.get("game_mode_enabled"):
        win_score += 15
    if win.get("hags", {}).get("enabled"):
        win_score += 10
    win_score = min(100, win_score)

    overall_score = round(
        (0.25 * cpu_score) +
        (0.25 * gpu_score) +
        (0.20 * ram_score) +
        (0.15 * storage_score) +
        (0.15 * win_score)
    )

    return {
        "overall_score": overall_score,
        "cpu_score": cpu_score,
        "gpu_score": gpu_score,
        "ram_score": ram_score,
        "storage_score": storage_score,
        "windows_score": win_score,
        "metrics_summary": {
            "cpu_model": cpu["brand"],
            "gpu_model": gpu["name"],
            "ram_total": f"{total_ram_gb} GB",
            "storage_used_pct": f"{storage_load}%"
        }
    }

def detect_system_bottlenecks() -> List[Dict[str, Any]]:
    """Analyze real metrics to identify active gaming bottlenecks."""
    bottlenecks = []
    cpu = get_cpu_telemetry()
    ram = get_ram_telemetry()
    storage = get_storage_telemetry()

    if cpu["usage_pct"] > 85.0:
        bottlenecks.append({
            "component": "CPU",
            "severity": "HIGH",
            "title": "Heavy CPU Background Contention",
            "description": f"CPU is operating at {cpu['usage_pct']}% load. Background processes may cause micro-stutters during gaming."
        })

    if ram["usage_pct"] > 85.0:
        bottlenecks.append({
            "component": "RAM",
            "severity": "HIGH",
            "title": "Low Available Physical Memory",
            "description": f"RAM usage is at {ram['usage_pct']}%. Windows is forced to use pagefile memory which increases frame-time spikes."
        })

    if storage["overall_usage_pct"] > 90.0:
        bottlenecks.append({
            "component": "STORAGE",
            "severity": "MEDIUM",
            "title": "Drive Space Nearly Exhausted",
            "description": f"Primary drive has only {round(100 - storage['overall_usage_pct'], 1)}% free space remaining, impairing write caching."
        })

    return bottlenecks
