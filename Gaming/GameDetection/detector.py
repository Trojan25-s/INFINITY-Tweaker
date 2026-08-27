"""
Game Detection Module: Automatically discovers installed games across Steam, Epic Games, and custom directory roots.
"""
import os
import winreg
from typing import List, Dict, Any

def scan_steam_games() -> List[Dict[str, Any]]:
    """Scan Steam library folders for installed games."""
    games = []
    steam_path = ""
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_READ)
        steam_path, _ = winreg.QueryValueEx(k, "SteamPath")
        winreg.CloseKey(k)
    except Exception:
        pass

    if not steam_path:
        # Common locations
        for p in ["C:\\Program Files (x86)\\Steam", "D:\\Steam", "E:\\Steam"]:
            if os.path.exists(p):
                steam_path = p
                break

    if steam_path and os.path.exists(steam_path):
        common_dir = os.path.join(steam_path, "steamapps", "common")
        if os.path.exists(common_dir):
            for d in os.listdir(common_dir):
                full_dir = os.path.join(common_dir, d)
                if os.path.isdir(full_dir):
                    # Search for main executable
                    for f in os.listdir(full_dir):
                        if f.endswith('.exe') and not any(skip in f.lower() for skip in ['crash', 'unins', 'setup', 'helper', 'dxsetup']):
                            games.append({
                                "name": d,
                                "launcher": "Steam",
                                "directory": full_dir,
                                "executable": os.path.join(full_dir, f)
                            })
                            break
    return games

def scan_epic_games() -> List[Dict[str, Any]]:
    """Scan Epic Games manifests for installed titles."""
    games = []
    manifests_dir = os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Epic", "EpicGamesLauncher", "Data", "Manifests")
    if os.path.exists(manifests_dir):
        for f in os.listdir(manifests_dir):
            if f.endswith('.item'):
                try:
                    import json
                    with open(os.path.join(manifests_dir, f), 'r', encoding='utf-8') as handle:
                        data = json.load(handle)
                        name = data.get("DisplayName", "Epic Game")
                        install_loc = data.get("InstallLocation", "")
                        launch_exe = data.get("LaunchExecutable", "")
                        if install_loc and launch_exe:
                            exe_path = os.path.join(install_loc, launch_exe)
                            games.append({
                                "name": name,
                                "launcher": "Epic Games",
                                "directory": install_loc,
                                "executable": exe_path
                            })
                except Exception:
                    continue
    return games

def detect_all_installed_games() -> List[Dict[str, Any]]:
    """Enumerate all discovered gaming titles."""
    steam = scan_steam_games()
    epic = scan_epic_games()
    all_games = steam + epic
    return all_games
