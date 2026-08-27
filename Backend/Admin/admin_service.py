"""
Admin management logic and telemetry aggregates for the INFINITY Admin Panel.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from Database.models import License, Device, LicenseEvent, AuditLog, AppVersion, Notification, FeatureFlag, LicenseStatus

def get_admin_dashboard_stats(db: Session) -> Dict[str, Any]:
    total_licenses = db.query(License).count()
    active_licenses = db.query(License).filter(License.status == LicenseStatus.ACTIVE.value).count()
    expired_licenses = db.query(License).filter(License.status == LicenseStatus.EXPIRED.value).count()
    revoked_licenses = db.query(License).filter(License.status == LicenseStatus.REVOKED.value).count()
    suspended_licenses = db.query(License).filter(License.status == LicenseStatus.SUSPENDED.value).count()
    trial_licenses = db.query(License).filter(License.license_type == "3-Day Trial").count()
    
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.is_active == True).count()
    
    # Online clients actively connected (heartbeat received within last 2 minutes)
    two_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=2)
    online_clients = db.query(Device).filter(Device.last_seen >= two_mins_ago, Device.is_active == True).count()
    
    latest_version = db.query(AppVersion).order_by(AppVersion.id.desc()).first()
    
    return {
        "total_licenses": total_licenses,
        "active_licenses": active_licenses,
        "expired_licenses": expired_licenses,
        "revoked_licenses": revoked_licenses,
        "suspended_licenses": suspended_licenses,
        "trial_licenses": trial_licenses,
        "total_devices": total_devices,
        "active_devices": active_devices,
        "online_clients": online_clients,
        "current_app_version": latest_version.version if latest_version else "1.0.0"
    }

def revoke_license(db: Session, license_id: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    lic.status = LicenseStatus.REVOKED.value
    event = LicenseEvent(license_id=lic.id, event_type="REVOKED", details="License revoked by admin")
    db.add(event)
    log = AuditLog(action="REVOKE_LICENSE", license_code=lic.code, details="License revoked by admin")
    db.add(log)
    db.commit()
    return True

def reactivate_license(db: Session, license_id: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    lic.status = LicenseStatus.ACTIVE.value
    event = LicenseEvent(license_id=lic.id, event_type="REACTIVATED", details="License reactivated by admin")
    db.add(event)
    log = AuditLog(action="REACTIVATE_LICENSE", license_code=lic.code, details="License reactivated by admin")
    db.add(log)
    db.commit()
    return True

def suspend_license(db: Session, license_id: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    lic.status = LicenseStatus.SUSPENDED.value
    event = LicenseEvent(license_id=lic.id, event_type="SUSPENDED", details="License suspended by admin")
    db.add(event)
    log = AuditLog(action="SUSPEND_LICENSE", license_code=lic.code, details="License suspended by admin")
    db.add(log)
    db.commit()
    return True

def extend_license_days(db: Session, license_id: int, additional_days: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    if lic.expires_at:
        lic.expires_at = lic.expires_at + timedelta(days=additional_days)
    else:
        lic.expires_at = datetime.now(timezone.utc) + timedelta(days=additional_days)
    lic.status = LicenseStatus.ACTIVE.value
    event = LicenseEvent(license_id=lic.id, event_type="EXTENDED", details=f"Extended by {additional_days} days")
    db.add(event)
    log = AuditLog(action="EXTEND_LICENSE", license_code=lic.code, details=f"Extended by {additional_days} days")
    db.add(log)
    db.commit()
    return True

def set_license_device_limit(db: Session, license_id: int, new_limit: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    lic.max_devices = max(1, new_limit)
    event = LicenseEvent(license_id=lic.id, event_type="DEVICE_LIMIT_CHANGED", details=f"Limit updated to {lic.max_devices}")
    db.add(event)
    db.commit()
    return True

def get_recent_license_events(db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    events = db.query(LicenseEvent).order_by(LicenseEvent.id.desc()).limit(limit).all()
    return [{
        "id": e.id,
        "license_id": e.license_id,
        "license_code": e.license.code if e.license else "N/A",
        "event_type": e.event_type,
        "hwid": e.hwid,
        "details": e.details,
        "created_at": e.created_at.isoformat()
    } for e in events]
