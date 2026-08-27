"""
Centralized License Authority Service.
Handles Multi-Device Enforcement, Periodic Real-Time Heartbeats, Instant Revocation/Suspension, and HMAC Verification.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from Database.models import License, Device, LicenseEvent, AuditLog, LicenseType, LicenseStatus
from Backend.Licensing.code_generator import generate_activation_code
from Backend.config import BACKEND_SECRET_KEY, MINIMUM_SUPPORTED_VERSION, OFFLINE_GRACE_PERIOD_SECONDS

def generate_signed_token(data: dict) -> str:
    """Generate tamper-proof HMAC-SHA256 signature for server-validated license payload."""
    payload_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
    sig = hmac.new(BACKEND_SECRET_KEY.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
    return sig

def create_license(
    db: Session,
    license_type: str,
    max_devices: int = 1,
    custom_code: Optional[str] = None,
    features_mask: str = "all_features",
    notes: Optional[str] = None
) -> License:
    code = custom_code.strip().upper() if custom_code else generate_activation_code()
    
    new_license = License(
        code=code,
        license_type=license_type,
        status=LicenseStatus.ACTIVE.value,
        max_devices=max_devices,
        features_mask=features_mask,
        notes=notes
    )
    db.add(new_license)
    db.flush()

    event = LicenseEvent(
        license_id=new_license.id,
        event_type="CREATED",
        details=f"Issued {license_type} key (Max devices: {max_devices})"
    )
    db.add(event)

    log = AuditLog(
        action="CREATE_LICENSE",
        license_code=code,
        details=f"Created {license_type} license (Max devices: {max_devices})"
    )
    db.add(log)
    db.commit()
    db.refresh(new_license)
    return new_license

def calculate_expiration(license_type: str, from_date: datetime) -> Optional[datetime]:
    if license_type == LicenseType.TRIAL_3D.value:
        return from_date + timedelta(days=3)
    elif license_type == LicenseType.WEEK_1.value:
        return from_date + timedelta(days=7)
    elif license_type == LicenseType.MONTH_1.value:
        return from_date + timedelta(days=30)
    elif license_type == LicenseType.YEAR_1.value:
        return from_date + timedelta(days=365)
    elif license_type == LicenseType.LIFETIME.value:
        return None
    return from_date + timedelta(days=30)

def activate_license(
    db: Session,
    code: str,
    hwid: str,
    device_name: str,
    os_info: str,
    app_version: str = "1.0.0",
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    code = code.strip().upper()
    license_obj = db.query(License).filter(License.code == code).first()

    if not license_obj:
        return {"status": "INVALID", "message": "Activation code does not exist. Please check your key."}

    if license_obj.status == LicenseStatus.REVOKED.value:
        return {
            "status": "REVOKED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN REVOKED",
            "license_type": license_obj.license_type
        }

    if license_obj.status == LicenseStatus.SUSPENDED.value:
        return {
            "status": "SUSPENDED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN TEMPORARILY SUSPENDED",
            "license_type": license_obj.license_type
        }

    now_utc = datetime.now(timezone.utc)

    # Check expiration
    if license_obj.expires_at:
        exp = license_obj.expires_at if license_obj.expires_at.tzinfo else license_obj.expires_at.replace(tzinfo=timezone.utc)
        if now_utc > exp:
            license_obj.status = LicenseStatus.EXPIRED.value
            db.commit()
            return {
                "status": "EXPIRED",
                "message": "YOUR INFINITY TWEAKER LICENSE HAS EXPIRED",
                "license_type": license_obj.license_type,
                "expiration_date": exp.isoformat()
            }

    # Check existing device
    existing_device = db.query(Device).filter(
        Device.license_id == license_obj.id,
        Device.hwid == hwid
    ).first()

    if existing_device:
        if not existing_device.is_active:
            return {
                "status": "DEVICE_NOT_AUTHORIZED",
                "message": "This specific device HWID has been de-authorized by administration."
            }
        existing_device.last_seen = now_utc
        existing_device.device_name = device_name
        existing_device.os_info = os_info
        existing_device.app_version = app_version
        
        event = LicenseEvent(
            license_id=license_obj.id,
            event_type="RE_ACTIVATED",
            hwid=hwid,
            details=f"Device {device_name} re-verified activation"
        )
        db.add(event)
        db.commit()

        token_payload = {
            "code": code,
            "hwid": hwid,
            "status": "VALID",
            "timestamp": now_utc.timestamp(),
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime"
        }
        sig = generate_signed_token(token_payload)

        return {
            "status": "VALID",
            "message": "License verified successfully.",
            "license_type": license_obj.license_type,
            "license_status": license_obj.status,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime",
            "features_mask": license_obj.features_mask,
            "device_id": existing_device.id,
            "max_devices": license_obj.max_devices,
            "server_signature": sig,
            "grace_period_seconds": OFFLINE_GRACE_PERIOD_SECONDS
        }

    # New device activation - enforce device limit
    active_count = db.query(Device).filter(
        Device.license_id == license_obj.id,
        Device.is_active == True
    ).count()

    if active_count >= license_obj.max_devices:
        return {
            "status": "DEVICE_LIMIT_REACHED",
            "message": f"Device limit reached ({active_count}/{license_obj.max_devices} devices active). Please manage your devices in the Admin Panel or upgrade.",
            "max_devices": license_obj.max_devices,
            "active_devices": active_count
        }

    # First device activation sets starting expiration if duration-based
    if not license_obj.activated_at:
        license_obj.activated_at = now_utc
        license_obj.expires_at = calculate_expiration(license_obj.license_type, now_utc)

    new_device = Device(
        license_id=license_obj.id,
        hwid=hwid,
        device_name=device_name,
        os_info=os_info,
        app_version=app_version,
        first_activated=now_utc,
        last_seen=now_utc,
        is_active=True
    )
    db.add(new_device)
    db.flush()

    event = LicenseEvent(
        license_id=license_obj.id,
        event_type="DEVICE_ACTIVATED",
        hwid=hwid,
        details=f"Device {device_name} (HWID: {hwid[:16]}...) activated ({active_count + 1}/{license_obj.max_devices})"
    )
    db.add(event)

    log = AuditLog(
        action="ACTIVATE_LICENSE",
        license_code=code,
        details=f"Activated device {device_name} (HWID: {hwid[:16]}...)",
        ip_address=ip_address
    )
    db.add(log)
    db.commit()

    token_payload = {
        "code": code,
        "hwid": hwid,
        "status": "VALID",
        "timestamp": now_utc.timestamp(),
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime"
    }
    sig = generate_signed_token(token_payload)

    return {
        "status": "VALID",
        "message": "Activation successful! Welcome to INFINITY Tweaker.",
        "license_type": license_obj.license_type,
        "license_status": license_obj.status,
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime",
        "features_mask": license_obj.features_mask,
        "device_id": new_device.id,
        "max_devices": license_obj.max_devices,
        "server_signature": sig,
        "grace_period_seconds": OFFLINE_GRACE_PERIOD_SECONDS
    }

def process_heartbeat(
    db: Session,
    code: str,
    hwid: str,
    app_version: str = "1.0.0",
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process periodic client heartbeat (every 30s).
    The backend is the sole source of truth for revocation, suspension, and expiration.
    """
    code = code.strip().upper()
    license_obj = db.query(License).filter(License.code == code).first()

    if not license_obj:
        return {"status": "INVALID", "message": "License code not found on central server."}

    if license_obj.status == LicenseStatus.REVOKED.value:
        return {
            "status": "REVOKED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN REVOKED",
            "license_type": license_obj.license_type
        }

    if license_obj.status == LicenseStatus.SUSPENDED.value:
        return {
            "status": "SUSPENDED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN TEMPORARILY SUSPENDED",
            "license_type": license_obj.license_type
        }

    now_utc = datetime.now(timezone.utc)

    # Check expiration
    if license_obj.expires_at:
        exp = license_obj.expires_at if license_obj.expires_at.tzinfo else license_obj.expires_at.replace(tzinfo=timezone.utc)
        if now_utc > exp:
            license_obj.status = LicenseStatus.EXPIRED.value
            db.commit()
            return {
                "status": "EXPIRED",
                "message": "YOUR INFINITY TWEAKER LICENSE HAS EXPIRED",
                "license_type": license_obj.license_type,
                "expiration_date": exp.isoformat()
            }

    # Verify device authorization
    device = db.query(Device).filter(
        Device.license_id == license_obj.id,
        Device.hwid == hwid
    ).first()

    if not device or not device.is_active:
        return {
            "status": "DEVICE_NOT_AUTHORIZED",
            "message": "This device is not authorized or has been deactivated by administration."
        }

    # Update heartbeat timestamp
    device.last_seen = now_utc
    device.app_version = app_version
    db.commit()

    token_payload = {
        "code": code,
        "hwid": hwid,
        "status": "VALID",
        "timestamp": now_utc.timestamp(),
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime"
    }
    sig = generate_signed_token(token_payload)

    return {
        "status": "ACTIVE",
        "license_type": license_obj.license_type,
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime",
        "features_mask": license_obj.features_mask,
        "server_time": now_utc.isoformat(),
        "server_signature": sig,
        "grace_period_seconds": OFFLINE_GRACE_PERIOD_SECONDS
    }

def suspend_license(db: Session, license_id: int) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    lic.status = LicenseStatus.SUSPENDED.value
    event = LicenseEvent(license_id=lic.id, event_type="SUSPENDED", details="License suspended by administrator")
    db.add(event)
    log = AuditLog(action="SUSPEND_LICENSE", license_code=lic.code, details="Suspended by administrator")
    db.add(log)
    db.commit()
    return True

def replace_device_hwid(db: Session, license_id: int, old_device_id: int, new_hwid: str, new_device_name: str) -> bool:
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        return False
    old_dev = db.query(Device).filter(Device.id == old_device_id, Device.license_id == license_id).first()
    if not old_dev:
        return False
    
    old_dev.is_active = False
    
    now_utc = datetime.now(timezone.utc)
    new_dev = Device(
        license_id=lic.id,
        hwid=new_hwid,
        device_name=new_device_name,
        os_info="Replaced Device",
        first_activated=now_utc,
        last_seen=now_utc,
        is_active=True
    )
    db.add(new_dev)
    
    event = LicenseEvent(
        license_id=lic.id,
        event_type="DEVICE_REPLACED",
        hwid=new_hwid,
        details=f"Replaced device {old_dev.device_name} with {new_device_name}"
    )
    db.add(event)
    db.commit()
    return True

def validate_license(
    db: Session,
    code: str,
    hwid: str,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """Validate ongoing license session."""
    code = code.strip().upper()
    license_obj = db.query(License).filter(License.code == code).first()

    if not license_obj:
        return {"status": "INVALID", "message": "License code not found."}

    if license_obj.status == LicenseStatus.REVOKED.value:
        return {
            "status": "REVOKED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN REVOKED",
            "license_type": license_obj.license_type
        }

    if license_obj.status == LicenseStatus.SUSPENDED.value:
        return {
            "status": "SUSPENDED",
            "message": "YOUR INFINITY TWEAKER LICENSE HAS BEEN TEMPORARILY SUSPENDED",
            "license_type": license_obj.license_type
        }

    now_utc = datetime.now(timezone.utc)
    if license_obj.expires_at:
        exp = license_obj.expires_at if license_obj.expires_at.tzinfo else license_obj.expires_at.replace(tzinfo=timezone.utc)
        if now_utc > exp:
            license_obj.status = LicenseStatus.EXPIRED.value
            db.commit()
            return {
                "status": "EXPIRED",
                "message": "YOUR INFINITY TWEAKER LICENSE HAS EXPIRED",
                "license_type": license_obj.license_type,
                "expiration_date": exp.isoformat()
            }

    device = db.query(Device).filter(
        Device.license_id == license_obj.id,
        Device.hwid == hwid
    ).first()

    if not device or not device.is_active:
        return {
            "status": "NOT_SUPPORTED",
            "message": "This device is not authorized for this license."
        }

    device.last_seen = now_utc
    db.commit()

    return {
        "status": "VALID",
        "message": "License active and authorized.",
        "license_type": license_obj.license_type,
        "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else "Lifetime"
    }

