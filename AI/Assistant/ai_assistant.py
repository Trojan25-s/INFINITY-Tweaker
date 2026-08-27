"""
INFINITY AI Assistant: Context-aware gaming and system performance advisor.
Analyzes real detected hardware telemetry to deliver factual explanations and troubleshooting guidance.
"""
from typing import Dict, Any, List
from System.Hardware.cpu_info import get_cpu_telemetry
from System.Hardware.gpu_info import get_gpu_telemetry
from System.Hardware.memory_info import get_ram_telemetry, get_top_memory_processes
from System.Hardware.storage_info import get_storage_telemetry
from System.Windows.win_info import get_windows_overview
from Optimization.PowerPlan.power_plan import get_active_power_plan
from AI.Analysis.bottleneck_analyzer import calculate_performance_score, detect_system_bottlenecks

class AIAssistant:
    @staticmethod
    def answer_query(question: str) -> Dict[str, Any]:
        """Generate factual, telemetry-grounded AI consultation."""
        q = question.lower()
        cpu = get_cpu_telemetry()
        gpu = get_gpu_telemetry()
        ram = get_ram_telemetry()
        storage = get_storage_telemetry()
        win = get_windows_overview()
        power = get_active_power_plan()
        score = calculate_performance_score()
        bottlenecks = detect_system_bottlenecks()

        # Context facts
        detected_facts = [
            f"CPU: {cpu['brand']} ({cpu['physical_cores']} Cores / {cpu['logical_threads']} Threads, currently {cpu['usage_pct']}% load)",
            f"GPU: {gpu['name']} ({gpu.get('vram_total_mb', 0)} MB VRAM, Driver: {gpu.get('driver_version')})",
            f"RAM: {ram['used_gb']} GB used / {ram['total_gb']} GB total ({ram['usage_pct']}%)",
            f"Active Power Plan: {power['name']}",
            f"Windows Game Mode: {'Enabled' if win.get('game_mode_enabled') else 'Disabled'}"
        ]

        category = "General"
        response_text = ""
        action_items = []

        if "fps" in q or "low fps" in q or "frame" in q:
            category = "FPS Analysis"
            response_text = (
                f"Based on your system analysis, your overall INFINITY Performance Score is **{score['overall_score']}/100**.\n\n"
                f"**Detected Facts:**\n"
                f"- Your CPU load is at **{cpu['usage_pct']}%** and RAM is at **{ram['usage_pct']}%**.\n"
                f"- Active GPU detected: **{gpu['name']}**.\n\n"
                f"**Diagnostics & Solution:**\n"
                f"1. If GPU usage during gaming is below 95%, you are experiencing a CPU or RAM bandwidth bottleneck. Switch your Power Plan to **High Performance** to eliminate core parking.\n"
                f"2. Ensure your game is set to use the High-Performance GPU in **GPU Optimizer**.\n"
                f"3. Disable background Game DVR buffer recording to free up encoder overhead."
            )
            action_items = ["Activate High Performance Power Plan", "Clean Shader Caches", "Set High GPU Preference"]

        elif "gpu" in q or "gpu usage" in q:
            category = "GPU Diagnostics"
            response_text = (
                f"Your primary display adapter is **{gpu['name']}** (Driver: `{gpu.get('driver_version')}`).\n\n"
                f"**Technical Insight:** In gaming, high GPU usage (97-99%) is actually desirable because it means your graphics card is rendering at maximum capacity. "
                f"If GPU usage drops to 50-70% while gaming, your CPU or single-core IPC is unable to feed draw calls fast enough to the GPU."
            )
            action_items = ["Verify Game Resolution Settings", "Check CPU per-core load in Performance Monitor"]

        elif "ram" in q or "memory" in q:
            top_procs = get_top_memory_processes(limit=4)
            proc_list_str = ", ".join([f"`{p['name']}` ({p['memory_mb']} MB)" for p in top_procs])
            category = "RAM Diagnostics"
            response_text = (
                f"Your system has **{ram['total_gb']} GB** of physical RAM, with **{ram['used_gb']} GB ({ram['usage_pct']}%)** currently in use.\n\n"
                f"**Top Memory Consuming Processes:**\n{proc_list_str}\n\n"
                f"**Recommendation:** Click **[ OPTIMIZE RAM ]** on your Dashboard to safely trim working set caches without terminating essential tasks."
            )
            action_items = ["Execute RAM Optimizer", "Review Startup Applications"]

        elif "power plan" in q or "power" in q:
            category = "Power Configuration"
            response_text = (
                f"Your active Windows power scheme is currently **{power['name']}**.\n\n"
                f"**Recommendation:** For desktop gaming rigs, we recommend the **High Performance** or **Ultimate Performance** plan. "
                f"This prevents CPU core downclocking and reduces frame-time jitter during intense action scenes."
            )
            action_items = ["Switch to High Performance Plan"]

        elif "stutter" in q or "stuttering" in q or "lag" in q:
            category = "Stutter Troubleshooting"
            response_text = (
                f"Micro-stutters and frame-time spikes are typically caused by:\n"
                f"1. **Background disk I/O:** Temporary file indexing or shader compilation.\n"
                f"2. **Memory page faults:** Operating near {ram['usage_pct']}% RAM capacity.\n"
                f"3. **Power state transitions:** CPU cores changing frequency states dynamically.\n\n"
                f"**Recommended Action:** Run Cache Cleaner to purge corrupted shader caches, enable High Performance power plan, and launch games through the INFINITY Game Launcher."
            )
            action_items = ["Run Cache Cleaner", "Trim RAM Working Set", "Launch via Game Launcher"]

        else:
            category = "System Optimization"
            response_text = (
                f"Welcome to the INFINITY AI Advisor. Your PC Performance Score is **{score['overall_score']} / 100**.\n\n"
                f"- **CPU Sub-score:** {score['cpu_score']}/100\n"
                f"- **GPU Sub-score:** {score['gpu_score']}/100\n"
                f"- **RAM Sub-score:** {score['ram_score']}/100\n"
                f"- **Storage Sub-score:** {score['storage_score']}/100\n\n"
                f"To maximize gaming performance, we recommend running a clean sweep in **Cache Cleaner** and tuning your power profile."
            )
            action_items = ["Scan System Caches", "Review AI Recommendations Tab"]

        return {
            "query": question,
            "category": category,
            "response": response_text,
            "detected_facts": detected_facts,
            "suggested_actions": action_items,
            "system_score": score["overall_score"]
        }
