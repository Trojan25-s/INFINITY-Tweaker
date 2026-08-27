"""
Device management service for tracking and modifying authorized client HWIDs.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from Database.models import Device, AuditLog

def list_devices_for_license(db: Session, license_id: int) -> List[Device]:
    return db.query(Device).filter(Device.license_id == license_id).all()

def deactivate_device(db: Session, device_id: int) -> bool:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return False
    device.is_active = False
    log = AuditLog(
        action="DEACTIVATE_DEVICE",
        details=f"Deactivated device id {device_id} ({device.device_name})"
    )
    db.add(log)
    db.commit()
    return True

def remove_device(db: Session, device_id: int) -> bool:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return False
    db.delete(device)
    log = AuditLog(
        action="DELETE_DEVICE",
        details=f"Deleted device id {device_id}"
    )
    db.add(log)
    db.commit()
    return True
