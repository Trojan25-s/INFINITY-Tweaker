"""
Broadcast notification manager for INFINITY Tweaker clients.
"""
from typing import List
from sqlalchemy.orm import Session
from Database.models import Notification

def get_active_notifications(db: Session) -> List[Notification]:
    return db.query(Notification).filter(Notification.is_active == True).order_by(Notification.created_at.desc()).all()

def create_notification(db: Session, title: str, message: str, level: str = "info") -> Notification:
    notif = Notification(title=title, message=message, level=level, is_active=True)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
