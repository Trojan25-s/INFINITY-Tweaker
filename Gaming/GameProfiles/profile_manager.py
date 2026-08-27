"""
Game Profile Manager: Stores and manages game-specific optimization configurations.
"""
import os
import json
from typing import List, Dict, Any, Optional

PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")

DEFAULT_PROFILES = [
    {
        "id": "cs2",
        "name": "Counter-Strike 2",
        "executable": "cs2.exe",
        "gpu_preference": "High Performance",
        "power_profile": "High Performance",
        "priority": "HIGH",
        "launch_args": "-novid -tickrate 128",
        "clean_ram_on_launch": True
    },
    {
        "id": "valorant",
        "name": "Valorant",
        "executable": "VALORANT.exe",
        "gpu_preference": "High Performance",
        "power_profile": "High Performance",
        "priority": "ABOVE_NORMAL",
        "launch_args": "",
        "clean_ram_on_launch": True
    },
    {
        "id": "cyberpunk2077",
        "name": "Cyberpunk 2077",
        "executable": "Cyberpunk2077.exe",
        "gpu_preference": "High Performance",
        "power_profile": "Ultimate Performance",
        "priority": "HIGH",
        "launch_args": "",
        "clean_ram_on_launch": True
    }
]

def load_profiles() -> List[Dict[str, Any]]:
    if not os.path.exists(PROFILES_FILE):
        save_profiles(DEFAULT_PROFILES)
        return DEFAULT_PROFILES.copy()
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_PROFILES.copy()

def save_profiles(profiles: List[Dict[str, Any]]):
    try:
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2)
    except Exception:
        pass

def add_or_update_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    profiles = load_profiles()
    existing_idx = next((i for i, p in enumerate(profiles) if p.get("id") == profile.get("id")), None)
    if existing_idx is not None:
        profiles[existing_idx] = profile
    else:
        if not profile.get("id"):
            profile["id"] = profile.get("name", "game").lower().replace(" ", "_")
        profiles.append(profile)
    save_profiles(profiles)
    return profile

def delete_profile(profile_id: str) -> bool:
    profiles = load_profiles()
    initial_len = len(profiles)
    profiles = [p for p in profiles if p.get("id") != profile_id]
    if len(profiles) != initial_len:
        save_profiles(profiles)
        return True
    return False
