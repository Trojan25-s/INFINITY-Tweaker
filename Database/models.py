"""
Database models for INFINITY Tweaker Centralized Multi-User Licensing Authority.
"""
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from Database.database import Base

class LicenseType(str, enum.Enum):
    TRIAL_3D = "3-Day Trial"
    WEEK_1 = "1 Week"
    MONTH_1 = "1 Month"
    YEAR_1 = "1 Year"
    LIFETIME = "Lifetime"

class LicenseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    SUSPENDED = "SUSPENDED"
    DEVICE_NOT_AUTHORIZED = "DEVICE_NOT_AUTHORIZED"
    UPDATE_REQUIRED = "UPDATE_REQUIRED"

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    license_type = Column(String(32), default=LicenseType.MONTH_1.value, nullable=False, index=True)
    status = Column(String(32), default=LicenseStatus.ACTIVE.value, nullable=False, index=True)
    max_devices = Column(Integer, default=1, nullable=False)
    features_mask = Column(String(256), default="all_features", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    notes = Column(Text, nullable=True)

    devices = relationship("Device", back_populates="license", cascade="all, delete-orphan")
    events = relationship("LicenseEvent", back_populates="license", cascade="all, delete-orphan")

    def is_valid_now(self) -> bool:
        if self.status != LicenseStatus.ACTIVE.value:
            return False
        if self.expires_at is not None:
            now_utc = datetime.now(timezone.utc)
            exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
            if now_utc > exp:
                return False
        return True

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    hwid = Column(String(64), index=True, nullable=False)
    device_name = Column(String(128), default="Windows PC", nullable=False)
    os_info = Column(String(128), default="Windows", nullable=False)
    app_version = Column(String(32), default="1.0.0", nullable=False)
    first_activated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    license = relationship("License", back_populates="devices")

    __table_args__ = (
        Index('idx_license_hwid', 'license_id', 'hwid'),
    )

class LicenseEvent(Base):
    __tablename__ = "license_events"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)  # ACTIVATED, HEARTBEAT, REVOKED, SUSPENDED, REACTIVATED, EXTENDED, DEVICE_REPLACED
    hwid = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    license = relationship("License", back_populates="events")

class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    api_token = Column(String(128), unique=True, nullable=False, index=True)
    role = Column(String(32), default="SUPERADMIN", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    min_app_version = Column(String(32), default="1.0.0", nullable=False)

class AppVersion(Base):
    __tablename__ = "app_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(32), unique=True, nullable=False, index=True)
    min_supported_version = Column(String(32), default="1.0.0", nullable=False)
    download_url = Column(String(256), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    release_notes = Column(Text, nullable=True)
    is_critical = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(32), default="info", nullable=False)  # info, warning, urgent
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    license_code = Column(String(64), nullable=True, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
