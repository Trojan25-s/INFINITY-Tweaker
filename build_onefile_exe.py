"""
Single File (.EXE) Builder for INFINITY Tweaker
"""
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build_onefile():
    print("[INFINITY] Building Single File EXE...")
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "INFINITY-Tweaker-SingleFile",
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
        "--hidden-import", "jinja2",
        "--hidden-import", "fastapi",
        "--hidden-import", "psutil",
        "--hidden-import", "requests",
        "--hidden-import", "pydantic",
        os.path.join(BASE_DIR, "Client", "app.py")
    ]
    subprocess.check_call(cmd)
    print("\n[SUCCESS] Single File EXE built successfully in dist/INFINITY-Tweaker-SingleFile.exe")

if __name__ == "__main__":
    build_onefile()
