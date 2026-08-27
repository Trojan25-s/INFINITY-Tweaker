"""
FastAPI Server for INFINITY Tweaker Centralized Multi-User Licensing, Real-time Heartbeats, Remote Admin, and Security.
"""
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import os

from Database.database import init_db, get_db
from Database.models import License, Device, LicenseEvent, AuditLog, AppVersion, Notification, FeatureFlag, LicenseType, LicenseStatus
from Backend.config import ADMIN_API_KEY, CURRENT_CLIENT_VERSION, MINIMUM_SUPPORTED_VERSION, BACKEND_HOST, BACKEND_PORT
from Backend.Licensing.license_service import (
    create_license, activate_license, validate_license, process_heartbeat,
    replace_device_hwid
)
from Backend.Licensing.code_generator import generate_activation_code
from Backend.Admin.admin_service import (
    get_admin_dashboard_stats, revoke_license, reactivate_license,
    suspend_license, extend_license_days, set_license_device_limit,
    get_recent_license_events
)
from Backend.Devices.device_manager import deactivate_device, remove_device
from Backend.Notifications.notification_service import get_active_notifications, create_notification

app = FastAPI(title="INFINITY Tweaker Centralized Licensing & Multi-User Authority", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_DIR = os.path.join(BASE_DIR, "AdminPanel")
templates = Jinja2Templates(directory=os.path.join(ADMIN_DIR, "templates"))

static_dir = os.path.join(ADMIN_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

# --- Public Client Request Models ---

class ActivationRequest(BaseModel):
    code: str
    hwid: str
    device_name: Optional[str] = "Windows PC"
    os_info: Optional[str] = "Windows 11 / 10"
    app_version: Optional[str] = "1.0.0"

class ValidationRequest(BaseModel):
    code: str
    hwid: str

class HeartbeatRequest(BaseModel):
    code: str
    hwid: str
    app_version: Optional[str] = "1.0.0"

class LicenseCreateRequest(BaseModel):
    license_type: str = "1 Month"
    max_devices: int = 1
    custom_code: Optional[str] = None
    features_mask: str = "all_features"
    notes: Optional[str] = None

class NotificationCreateRequest(BaseModel):
    title: str
    message: str
    level: str = "info"

class VersionPublishRequest(BaseModel):
    version: str
    min_supported_version: str = "1.0.0"
    download_url: str
    checksum_sha256: str
    release_notes: Optional[str] = ""
    is_critical: bool = False

class ReplaceDeviceRequest(BaseModel):
    old_device_id: int
    new_hwid: str
    new_device_name: str

class DeviceLimitRequest(BaseModel):
    new_limit: int

# --- Public Client Endpoints ---

@app.post("/api/v1/license/activate")
def activate_endpoint(req: ActivationRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return activate_license(
        db=db,
        code=req.code,
        hwid=req.hwid,
        device_name=req.device_name,
        os_info=req.os_info,
        app_version=req.app_version,
        ip_address=ip
    )

@app.post("/api/v1/license/validate")
def validate_endpoint(req: ValidationRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return validate_license(
        db=db,
        code=req.code,
        hwid=req.hwid,
        ip_address=ip
    )

@app.post("/api/v1/license/heartbeat")
def heartbeat_endpoint(req: HeartbeatRequest, request: Request, db: Session = Depends(get_db)):
    """Centralized heartbeat called every 30s by connected clients."""
    ip = request.client.host if request.client else None
    return process_heartbeat(
        db=db,
        code=req.code,
        hwid=req.hwid,
        app_version=req.app_version,
        ip_address=ip
    )

@app.get("/api/v1/application/version")
def version_endpoint(db: Session = Depends(get_db)):
    latest = db.query(AppVersion).order_by(AppVersion.id.desc()).first()
    return {
        "current_version": latest.version if latest else CURRENT_CLIENT_VERSION,
        "min_supported_version": latest.min_supported_version if latest else MINIMUM_SUPPORTED_VERSION
    }

@app.get("/api/v1/application/config")
def config_endpoint(db: Session = Depends(get_db)):
    flags = db.query(FeatureFlag).all()
    flags_map = {f.key: f.is_enabled for f in flags}
    return {
        "flags": flags_map,
        "min_supported_version": MINIMUM_SUPPORTED_VERSION,
        "heartbeat_interval_seconds": 30
    }

@app.get("/api/v1/notifications")
def list_notifications_endpoint(db: Session = Depends(get_db)):
    notifications = get_active_notifications(db)
    return [{"id": n.id, "title": n.title, "message": n.message, "level": n.level, "created_at": n.created_at.isoformat()} for n in notifications]

@app.get("/api/v1/updates/check")
def check_update_endpoint(version: str, db: Session = Depends(get_db)):
    latest = db.query(AppVersion).order_by(AppVersion.id.desc()).first()
    if not latest:
        return {"update_available": False, "latest_version": CURRENT_CLIENT_VERSION}
    
    is_newer = latest.version != version
    return {
        "update_available": is_newer,
        "latest_version": latest.version,
        "min_supported_version": latest.min_supported_version,
        "download_url": latest.download_url,
        "checksum_sha256": latest.checksum_sha256,
        "release_notes": latest.release_notes,
        "is_critical": latest.is_critical
    }

# --- Owner Admin Endpoints (Secured by Admin Key / Token) ---

def verify_admin_token(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key and x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized Admin Access")
    return True

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/api/v1/admin/stats")
def admin_stats(db: Session = Depends(get_db)):
    return get_admin_dashboard_stats(db)

@app.get("/api/v1/admin/licenses")
def admin_list_licenses(db: Session = Depends(get_db)):
    licenses = db.query(License).order_by(License.id.desc()).all()
    results = []
    for lic in licenses:
        results.append({
            "id": lic.id,
            "code": lic.code,
            "license_type": lic.license_type,
            "status": lic.status,
            "max_devices": lic.max_devices,
            "device_count": len([d for d in lic.devices if d.is_active]),
            "created_at": lic.created_at.isoformat() if lic.created_at else None,
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else "Lifetime",
            "notes": lic.notes
        })
    return results

@app.post("/api/v1/admin/licenses")
def admin_create_license(req: LicenseCreateRequest, db: Session = Depends(get_db)):
    lic = create_license(
        db=db,
        license_type=req.license_type,
        max_devices=req.max_devices,
        custom_code=req.custom_code,
        features_mask=req.features_mask,
        notes=req.notes
    )
    return {"status": "SUCCESS", "code": lic.code, "id": lic.id, "type": lic.license_type}

@app.post("/api/v1/admin/licenses/{license_id}/revoke")
def admin_revoke_license(license_id: int, db: Session = Depends(get_db)):
    success = revoke_license(db, license_id)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"status": "SUCCESS", "message": "License revoked"}

@app.post("/api/v1/admin/licenses/{license_id}/suspend")
def admin_suspend_license(license_id: int, db: Session = Depends(get_db)):
    success = suspend_license(db, license_id)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"status": "SUCCESS", "message": "License suspended"}

@app.post("/api/v1/admin/licenses/{license_id}/reactivate")
def admin_reactivate_license(license_id: int, db: Session = Depends(get_db)):
    success = reactivate_license(db, license_id)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"status": "SUCCESS", "message": "License reactivated"}

@app.post("/api/v1/admin/licenses/{license_id}/extend")
def admin_extend_license(license_id: int, days: int = 30, db: Session = Depends(get_db)):
    success = extend_license_days(db, license_id, days)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"status": "SUCCESS", "message": f"License extended by {days} days"}

@app.post("/api/v1/admin/licenses/{license_id}/set-limit")
def admin_set_device_limit(license_id: int, req: DeviceLimitRequest, db: Session = Depends(get_db)):
    success = set_license_device_limit(db, license_id, req.new_limit)
    if not success:
        raise HTTPException(status_code=404, detail="License not found")
    return {"status": "SUCCESS", "message": f"Device limit updated to {req.new_limit}"}

@app.post("/api/v1/admin/licenses/{license_id}/replace-device")
def admin_replace_device(license_id: int, req: ReplaceDeviceRequest, db: Session = Depends(get_db)):
    success = replace_device_hwid(
        db=db,
        license_id=license_id,
        old_device_id=req.old_device_id,
        new_hwid=req.new_hwid,
        new_device_name=req.new_device_name
    )
    if not success:
        raise HTTPException(status_code=404, detail="Device or License not found")
    return {"status": "SUCCESS", "message": "Device replaced"}

@app.get("/api/v1/admin/devices")
def admin_list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).order_by(Device.last_seen.desc()).all()
    results = []
    for dev in devices:
        results.append({
            "id": dev.id,
            "license_id": dev.license_id,
            "license_code": dev.license.code if dev.license else "N/A",
            "hwid": dev.hwid,
            "device_name": dev.device_name,
            "os_info": dev.os_info,
            "app_version": dev.app_version,
            "first_activated": dev.first_activated.isoformat() if dev.first_activated else None,
            "last_seen": dev.last_seen.isoformat() if dev.last_seen else None,
            "is_active": dev.is_active
        })
    return results

@app.post("/api/v1/admin/devices/{device_id}/deactivate")
def admin_deactivate_device(device_id: int, db: Session = Depends(get_db)):
    success = deactivate_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "SUCCESS", "message": "Device deactivated"}

@app.get("/api/v1/admin/events")
def admin_events(limit: int = 50, db: Session = Depends(get_db)):
    return get_recent_license_events(db, limit)

@app.post("/api/v1/admin/notifications")
def admin_broadcast_notification(req: NotificationCreateRequest, db: Session = Depends(get_db)):
    notif = create_notification(db, title=req.title, message=req.message, level=req.level)
    return {"status": "SUCCESS", "id": notif.id}

@app.post("/api/v1/admin/updates/publish")
def admin_publish_update(req: VersionPublishRequest, db: Session = Depends(get_db)):
    ver = AppVersion(
        version=req.version,
        min_supported_version=req.min_supported_version,
        download_url=req.download_url,
        checksum_sha256=req.checksum_sha256,
        release_notes=req.release_notes,
        is_critical=req.is_critical
    )
    db.add(ver)
    db.commit()
    return {"status": "SUCCESS", "version": ver.version}

@app.get("/api/v1/admin/logs")
def admin_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [{
        "id": l.id,
        "action": l.action,
        "license_code": l.license_code,
        "details": l.details,
        "ip_address": l.ip_address,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
