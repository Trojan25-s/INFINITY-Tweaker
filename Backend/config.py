"""
Configuration for INFINITY Tweaker Centralized Multi-User Backend & Security Authority.
"""
import os
import secrets

BACKEND_HOST = os.getenv("INFINITY_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("PORT", os.getenv("INFINITY_PORT", "8000")))
BACKEND_SECRET_KEY = os.getenv("INFINITY_SECRET_KEY", "INFINITY-CORE-HMAC-SIGNING-SECRET-2026")
ADMIN_API_KEY = os.getenv("INFINITY_ADMIN_KEY", "INFINITY-ADMIN-SECURE-KEY-2026")
CURRENT_CLIENT_VERSION = "1.0.0"
MINIMUM_SUPPORTED_VERSION = "1.0.0"

# Heartbeat & Grace Period Rules
HEARTBEAT_INTERVAL_SECONDS = 30
OFFLINE_GRACE_PERIOD_SECONDS = 86400  # 24 Hours Maximum Limited Offline Grace
RATE_LIMIT_PER_MINUTE = 60
