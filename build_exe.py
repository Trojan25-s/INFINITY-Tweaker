"""
PyInstaller Build Script with Full Package Collection
"""
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("[INFINITY] Building Executables with Full Package Collection...")
    
    # 1. Build Onedir
    cmd_onedir = [
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
        "--collect-all", "fastapi",
        "--collect-all", "starlette",
        "--collect-all", "uvicorn",
        "--collect-all", "jinja2",
        "--collect-all", "pydantic",
        "--collect-all", "requests",
        "--collect-all", "psutil",
        os.path.join(BASE_DIR, "Client", "app.py")
    ]
    subprocess.check_call(cmd_onedir)

    # 2. Build Single File EXE
    cmd_onefile = [
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
        "--collect-all", "fastapi",
        "--collect-all", "starlette",
        "--collect-all", "uvicorn",
        "--collect-all", "jinja2",
        "--collect-all", "pydantic",
        "--collect-all", "requests",
        "--collect-all", "psutil",
        os.path.join(BASE_DIR, "Client", "app.py")
    ]
    subprocess.check_call(cmd_onefile)
    print("\n[SUCCESS] Both onedir and singlefile builds completed with full dependencies!")

if __name__ == "__main__":
    build()
