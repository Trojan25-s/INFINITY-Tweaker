"""
INFINITY Tweaker Client UI Server & Hardware Bridge.
Implements 30-second periodic heartbeat loop with centralized backend authority and 24-hour offline grace protection.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import asyncio
import json
import time
import requests

from Core.Configuration.config_manager import config
from Core.Security.hwid import get_hardware_fingerprint, get_machine_name, get_os_string
from Core.Security.crypto import save_activation_vault, load_activation_vault, clear_activation_vault
from Core.Logging.logger import get_logger
from System.Hardware.cpu_info import get_cpu_telemetry
from System.Hardware.gpu_info import get_gpu_telemetry
from System.Hardware.memory_info import get_ram_telemetry, get_top_memory_processes
from System.Hardware.storage_info import get_storage_telemetry
from System.Drivers.driver_center import get_installed_drivers
from System.Windows.win_info import get_windows_overview
from Optimization.CacheCleaner.cache_cleaner import CacheCleaner
from Optimization.RamOptimizer.ram_optimizer import optimize_ram
from Optimization.PowerPlan.power_plan import get_active_power_plan, list_available_power_plans, set_power_plan
from Optimization.GpuOptimizer.gpu_optimizer import get_gpu_optimization_status, set_game_gpu_preference
from Optimization.WindowsOptimizer.windows_optimizer import get_windows_tweaks_status, apply_tweak
from Optimization.Services.services_manager import list_services, change_service_startup, control_service
from Optimization.Startup.startup_manager import list_startup_entries, toggle_startup_item
from Optimization.Network.network_boost import run_network_diagnostic
from Optimization.Storage.storage_optimizer import find_large_files, get_trim_status
from Gaming.GameDetection.detector import detect_all_installed_games
from Gaming.GameProfiles.profile_manager import load_profiles, add_or_update_profile, delete_profile
from Gaming.GameLauncher.launcher import launch_game, get_active_session
from Gaming.PerformanceMonitor.monitor import monitor
from Gaming.Benchmark.benchmark import run_system_benchmark
from AI.Analysis.bottleneck_analyzer import calculate_performance_score, detect_system_bottlenecks
from AI.Recommendations.recommender import generate_recommendations
from AI.Assistant.ai_assistant import AIAssistant
from Restore.backup_manager import create_backup_snapshot, list_backup_snapshots, get_snapshot
from Restore.change_history import get_change_history
from Core.Updates.update_manager import check_for_updates

logger = get_logger()

client_app = FastAPI(title="INFINITY Tweaker Client Bridge", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
client_app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Models
class ActivationInput(BaseModel):
    code: str

class TweakInput(BaseModel):
    tweak_id: str
    enable: bool

class ServiceActionInput(BaseModel):
    service_name: str
    action: str

class ServiceStartupInput(BaseModel):
    service_name: str
    startup_type: str

class StartupToggleInput(BaseModel):
    name: str
    enable: bool

class AIQueryInput(BaseModel):
    question: str

class PowerPlanInput(BaseModel):
    plan_name: str

class GameLaunchInput(BaseModel):
    profile_id: str

@client_app.get("/", response_class=HTMLResponse)
def index_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Licensing & Central Heartbeat Endpoints ---

@client_app.get("/api/client/auth/status")
def auth_status():
    vault = load_activation_vault()
    hwid = get_hardware_fingerprint()
    if not vault or "code" not in vault:
        return {"activated": False, "hwid": hwid, "device_name": get_machine_name()}
    
    backend_url = config.get("network", "backend_url", "http://127.0.0.1:8000")
    try:
        res = requests.post(f"{backend_url}/api/v1/license/heartbeat", json={
            "code": vault["code"],
            "hwid": hwid,
            "app_version": "1.0.0"
        }, timeout=3)
        if res.status_code == 200:
            val_data = res.json()
            if val_data.get("status") in ["ACTIVE", "VALID"]:
                # Update local vault timestamp proof
                vault["last_verified_ts"] = time.time()
                vault["license_type"] = val_data.get("license_type", vault.get("license_type"))
                vault["expires_at"] = val_data.get("expires_at", vault.get("expires_at"))
                save_activation_vault(vault)

                return {
                    "activated": True,
                    "license_type": val_data.get("license_type"),
                    "expires_at": val_data.get("expires_at"),
                    "code_masked": f"{vault['code'][:4]}-****-****-{vault['code'][-4:]}",
                    "hwid": hwid,
                    "status": "ACTIVE"
                }
            else:
                # License revoked, suspended, or expired on backend
                return {
                    "activated": False,
                    "reason": val_data.get("status"),
                    "message": val_data.get("message"),
                    "hwid": hwid
                }
    except Exception:
        # Backend unreachable -> Check 24-hour limited offline grace period
        last_verified = vault.get("last_verified_ts", 0)
        time_elapsed = time.time() - last_verified
        MAX_GRACE = 86400  # 24 Hours
        
        if last_verified > 0 and time_elapsed <= MAX_GRACE:
            hours_left = round((MAX_GRACE - time_elapsed) / 3600, 1)
            return {
                "activated": True,
                "license_type": vault.get("license_type", "Offline Grace"),
                "expires_at": vault.get("expires_at", "Cached"),
                "code_masked": f"{vault['code'][:4]}-****-****-{vault['code'][-4:]}",
                "hwid": hwid,
                "offline_mode": True,
                "grace_hours_remaining": hours_left,
                "status": "OFFLINE_GRACE"
            }
        else:
            return {
                "activated": False,
                "reason": "GRACE_EXPIRED",
                "message": "Offline grace period (24 hours) has expired. Please connect to the Internet to verify license.",
                "hwid": hwid
            }

@client_app.post("/api/client/auth/activate")
def client_activate(inp: ActivationInput):
    hwid = get_hardware_fingerprint()
    dev_name = get_machine_name()
    os_info = get_os_string()
    backend_url = config.get("network", "backend_url", "http://127.0.0.1:8000")

    try:
        res = requests.post(f"{backend_url}/api/v1/license/activate", json={
            "code": inp.code.strip().upper(),
            "hwid": hwid,
            "device_name": dev_name,
            "os_info": os_info,
            "app_version": "1.0.0"
        }, timeout=5)
        data = res.json()
        if data.get("status") == "VALID":
            save_activation_vault({
                "code": inp.code.strip().upper(),
                "license_type": data.get("license_type"),
                "expires_at": data.get("expires_at"),
                "hwid": hwid,
                "last_verified_ts": time.time()
            })
            return {"success": True, "message": data.get("message"), "data": data}
        return {"success": False, "status": data.get("status"), "message": data.get("message")}
    except Exception as e:
        return {"success": False, "status": "SERVER_UNAVAILABLE", "message": f"Could not contact central licensing authority: {e}"}

@client_app.post("/api/client/auth/deactivate")
def client_deactivate():
    clear_activation_vault()
    return {"success": True}

# --- Telemetry & System Endpoints ---

@client_app.get("/api/client/telemetry/live")
def get_live_telemetry():
    return monitor.sample_telemetry()

@client_app.get("/api/client/dashboard/overview")
def get_dashboard_overview():
    cpu = get_cpu_telemetry()
    gpu = get_gpu_telemetry()
    ram = get_ram_telemetry()
    storage = get_storage_telemetry()
    score = calculate_performance_score()
    power = get_active_power_plan()
    active_session = get_active_session()

    return {
        "score": score,
        "cpu": cpu,
        "gpu": gpu,
        "ram": ram,
        "storage": storage,
        "power_plan": power,
        "active_game": active_session.get("name") if active_session else "None Detected"
    }

@client_app.get("/api/client/system/info")
def get_full_system_info():
    return {
        "cpu": get_cpu_telemetry(),
        "gpu": get_gpu_telemetry(),
        "ram": get_ram_telemetry(),
        "storage": get_storage_telemetry(),
        "windows": get_windows_overview(),
        "drivers": get_installed_drivers()
    }

# --- Optimization Action Endpoints ---

@client_app.post("/api/client/optimize/ram")
def trigger_ram_optimization():
    return optimize_ram()

@client_app.get("/api/client/cache/scan")
def scan_caches():
    return CacheCleaner.scan_all()

@client_app.post("/api/client/cache/clean")
def clean_all_caches():
    return CacheCleaner.clean_all()

@client_app.post("/api/client/cache/clean/{category}")
def clean_category_cache(category: str):
    return CacheCleaner.clean_category(category)

@client_app.get("/api/client/windows/tweaks")
def get_win_tweaks():
    return get_windows_tweaks_status()

@client_app.post("/api/client/windows/tweaks/apply")
def apply_win_tweak(inp: TweakInput):
    return apply_tweak(inp.tweak_id, inp.enable)

@client_app.get("/api/client/power/plans")
def get_power_plans():
    return {
        "active": get_active_power_plan(),
        "available": list_available_power_plans()
    }

@client_app.post("/api/client/power/set")
def set_power_plan_endpoint(inp: PowerPlanInput):
    return set_power_plan(inp.plan_name)

@client_app.get("/api/client/services")
def get_services_endpoint():
    return list_services()

@client_app.post("/api/client/services/startup")
def change_service_startup_endpoint(inp: ServiceStartupInput):
    return change_service_startup(inp.service_name, inp.startup_type)

@client_app.post("/api/client/services/control")
def control_service_endpoint(inp: ServiceActionInput):
    return control_service(inp.service_name, inp.action)

@client_app.get("/api/client/startup")
def get_startup_items():
    return list_startup_entries()

@client_app.post("/api/client/startup/toggle")
def toggle_startup_endpoint(inp: StartupToggleInput):
    return toggle_startup_item(inp.name, inp.enable)

@client_app.get("/api/client/network/diagnostic")
def get_network_diagnostic():
    return run_network_diagnostic()

@client_app.get("/api/client/storage/large-files")
def get_large_files():
    return {
        "files": find_large_files(),
        "trim": get_trim_status()
    }

@client_app.get("/api/client/gpu/status")
def get_gpu_status():
    return get_gpu_optimization_status()

# --- Gaming & Benchmarking Endpoints ---

@client_app.get("/api/client/games/detected")
def get_detected_games():
    return detect_all_installed_games()

@client_app.get("/api/client/games/profiles")
def get_game_profiles():
    return load_profiles()

@client_app.post("/api/client/games/profiles")
def save_game_profile(profile: Dict[str, Any]):
    return add_or_update_profile(profile)

@client_app.delete("/api/client/games/profiles/{profile_id}")
def remove_game_profile(profile_id: str):
    return {"success": delete_profile(profile_id)}

@client_app.post("/api/client/games/launch")
def launch_game_endpoint(inp: GameLaunchInput):
    profiles = load_profiles()
    target = next((p for p in profiles if p.get("id") == inp.profile_id), None)
    if not target:
        return {"result": "FAILED", "error": "Profile not found"}
    return launch_game(target)

@client_app.post("/api/client/benchmark/run")
def trigger_benchmark(stage: str = "CURRENT"):
    return run_system_benchmark(stage)

# --- AI, Recommendations, Backup & Logs ---

@client_app.get("/api/client/ai/recommendations")
def get_ai_recommendations():
    return generate_recommendations()

@client_app.post("/api/client/ai/query")
def query_ai_assistant(inp: AIQueryInput):
    return AIAssistant.answer_query(inp.question)

@client_app.get("/api/client/history/changes")
def get_change_history_endpoint():
    return get_change_history()

@client_app.get("/api/client/backup/snapshots")
def get_snapshots_endpoint():
    return list_backup_snapshots()

@client_app.post("/api/client/backup/create")
def create_snapshot_endpoint(name: str = "Pre-Optimization Snapshot"):
    data = {
        "power_plan": get_active_power_plan(),
        "tweaks": get_windows_tweaks_status()
    }
    snap_id = create_backup_snapshot(name, data)
    return {"id": snap_id, "name": name}

@client_app.get("/api/client/updates/check")
def check_updates_endpoint():
    return check_for_updates()

# --- WebSocket for Real-time Hardware Stream ---

@client_app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = monitor.sample_telemetry()
            await websocket.send_json(data)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
