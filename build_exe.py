"""
Build Script for INFINITY Tweaker Desktop Application (.EXE)
Packages client, UI templates, static assets, and optimization modules.
"""
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("[INFINITY] Starting .EXE Build Pipeline...")
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "INFINITY-Tweaker",
        "--add-data", f"{os.path.join(BASE_DIR, 'UI')};UI",
        "--add-data", f"{os.path.join(BASE_DIR, 'Core')};Core",
        "--add-data", f"{os.path.join(BASE_DIR, 'Optimization')};Optimization",
        "--add-data", f"{os.path.join(BASE_DIR, 'Gaming')};Gaming",
        "--add-data", f"{os.path.join(BASE_DIR, 'AI')};AI",
        "--add-data", f"{os.path.join(BASE_DIR, 'System')};System",
        "--add-data", f"{os.path.join(BASE_DIR, 'Restore')};Restore",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespans",
        "--hidden-import", "uvicorn.lifespans.on",
        "--hidden-import", "jinja2",
        "--hidden-import", "fastapi",
        "--hidden-import", "psutil",
        "--hidden-import", "requests",
        "--hidden-import", "pydantic",
        os.path.join(BASE_DIR, "Client", "app.py")
    ]
    
    print(f"[INFINITY] Executing command: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    dist_path = os.path.join(BASE_DIR, "dist", "INFINITY-Tweaker", "INFINITY-Tweaker.exe")
    if os.path.exists(dist_path):
        print(f"\n==================================================")
        print(f"🎉 BUILD SUCCESSFUL!")
        print(f"Executable Location: {dist_path}")
        print(f"==================================================")
    else:
        print("\n[WARN] Build completed but executable path could not be verified.")

if __name__ == "__main__":
    build()
