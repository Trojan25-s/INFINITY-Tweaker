"""
INFINITY Tweaker - Master Dual Launcher & Development Harness.
Starts the Backend Licensing API & Admin Panel on port 8000,
pre-seeds initial demo licenses, and launches the Desktop Client on port 5000.
"""
import threading
import time
import os
import sys
import uvicorn
import webbrowser

# Add current workspace to path
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from Backend.server import app as backend_app
from UI.server import client_app
from Database.database import SessionLocal, init_db
from Database.models import License
from Backend.Licensing.license_service import create_license

def seed_demo_licenses():
    init_db()
    db = SessionLocal()
    try:
        # Check if demo licenses exist
        if db.query(License).count() == 0:
            create_license(db, license_type="1 Month", custom_code="INF-2026-DEMO-PRO1", notes="Default Demo Key")
            create_license(db, license_type="3-Day Trial", custom_code="INF-2026-TRIA-L3DY", notes="3-Day Trial Key")
            create_license(db, license_type="Lifetime", custom_code="INF-2026-LIFE-TIME", notes="Lifetime VIP Key")
            print("==================================================================")
            print("  [INFINITY TWEAKER] SEEDED INITIAL ACTIVATION KEYS:")
            print("  - Pro (1 Month): INF-2026-DEMO-PRO1")
            print("  - 3-Day Trial:   INF-2026-TRIA-L3DY")
            print("  - Lifetime VIP:  INF-2026-LIFE-TIME")
            print("  Admin Command Center: http://127.0.0.1:8000/admin")
            print("==================================================================")
    finally:
        db.close()

def start_backend():
    uvicorn.run(backend_app, host="127.0.0.1", port=8000, log_level="warning")

def start_client():
    uvicorn.run(client_app, host="127.0.0.1", port=5000, log_level="warning")

def open_ui():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")

def main():
    print("[INFINITY TWEAKER] Initializing Architecture...")
    seed_demo_licenses()

    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    print("  [OK] Licensing Backend Server running on http://127.0.0.1:8000")
    print("  [OK] Admin Panel running on http://127.0.0.1:8000/admin")

    time.sleep(1.0)
    client_thread = threading.Thread(target=start_client, daemon=True)
    client_thread.start()
    print("  [OK] INFINITY Tweaker Client UI running on http://127.0.0.1:5000")

    threading.Thread(target=open_ui, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFINITY TWEAKER] Shutting down...")

if __name__ == "__main__":
    main()
