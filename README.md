# INFINITY Tweaker — Master Commercial Multi-User Platform

INFINITY Tweaker is a centralized, high-performance Windows desktop gaming optimization platform. It is engineered with an **Online Multi-User Architecture** where a centralized backend server is the single source of truth for licenses, device limits, suspensions, revocations, and diagnostics.

---

## 🌐 Centralized Multi-User Architecture

```
INFINITY TWEAKER CLIENTS (10 to 10,000+ Online User Rigs)
         │
         │  (HTTPS / TLS 1.3 - 30s Heartbeat, Activation, Verification)
         ▼
CENTRAL FASTAPI BACKEND SERVER (Port 8000)
         │
         ├── Rate Limiter & Security Guard
         ├── License Expiration & Verification Engine
         ├── Multi-Device Allocator & Limit Enforcer
         ├── Real-time Heartbeat & Online Session Monitor
         └── Audit Log & License Event Streamer
         │
         ▼
SQLAlchemy / SQLite WAL / PostgreSQL Central Data Store
         ▲
         │  (Authenticated Admin Control API / Session)
         │
OWNER ADMIN COMMAND CENTER (http://127.0.0.1:8000/admin)
```

---

## ⚡ Core Multi-User Capabilities

### 1. Centralized Authority & Source of Truth
- The desktop client is strictly a client and **never** decides license validity independently.
- The central backend validates activation codes, expiration dates, device allocations, and suspension/revocation status.

### 2. Real-Time Periodic Heartbeat & Instant Lockout
- Connected client rigs send a lightweight periodic heartbeat every **30 seconds** (`POST /api/v1/license/heartbeat`).
- **Instant Remote Revocation / Suspension**: When the owner revokes or suspends a license in the Admin Panel, the very next client heartbeat immediately detects the revoked state, instantly locks premium features, and presents the Expired/Revoked screen.

### 3. Configurable Multi-Device Limits & Hardware Replacement
- Activation keys support configurable device limits (e.g. 1 device, 2 devices, 5 devices).
- The backend enforces limits automatically (`DEVICE_LIMIT_REACHED`).
- The Admin Panel allows the owner to de-authorize or replace hardware nodes (HWIDs) remotely when a user upgrades or replaces their gaming PC.

### 4. Limited 24-Hour Offline Grace Period
- If temporary internet disconnection occurs, the client verifies the cryptographic HMAC-SHA256 signature and server timestamp of its last valid heartbeat.
- Offline usage is strictly capped at **24 hours maximum**. Once the grace period expires, optimization features are locked until reconnected to the central server.

### 5. Owner Admin Command Center (`http://127.0.0.1:8000/admin`)
- **Real-Time Metrics**: Online clients (heartbeat within 2 minutes), active licenses, expired, revoked, suspended, and trial counts.
- **Remote Controls**: Create keys, revoke, suspend, reactivate, extend (+30 days), adjust device limits, replace hardware nodes, and broadcast push notifications.
- **Live Event Stream**: Real-time log of multi-user activations, heartbeats, replacements, and status changes.

---

## 🧪 Automated Testing

Run the full automated test suite covering unit tests and multi-user integration tests:
```powershell
python -m unittest discover -s Tests -p "test_*.py" -v
```

---

## 🚀 How to Run

1. **Start Master Suite** (starts Backend on port 8000 and Client UI on port 5000):
   ```powershell
   python run_infinity.py
   ```
2. **Access Admin Panel**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
3. **Pre-Seeded Activation Keys**:
   - `INF-2026-DEMO-PRO1` (1 Month Pro)
   - `INF-2026-TRIA-L3DY` (3-Day Trial)
   - `INF-2026-LIFE-TIME` (Lifetime VIP)
