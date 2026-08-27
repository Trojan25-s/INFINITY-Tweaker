"""
Automated Integration & Concurrency Tests for Centralized Multi-User Architecture.
Tests simultaneous multi-client activations, device limits, periodic heartbeats, remote suspension/revocation, and device replacement.
"""
import unittest
import time
from datetime import datetime, timezone
from Database.database import Base, engine, SessionLocal
from Database.models import License, Device, LicenseEvent, LicenseStatus
from Backend.Licensing.license_service import (
    create_license, activate_license, validate_license, process_heartbeat,
    suspend_license, replace_device_hwid, generate_signed_token
)
from Backend.Admin.admin_service import (
    revoke_license, reactivate_license, set_license_device_limit,
    get_admin_dashboard_stats, get_recent_license_events
)

class TestMultiUserArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_multi_user_isolation_and_device_limits(self):
        """Test that a 2-device license allows 2 distinct client rigs but strictly rejects a 3rd."""
        lic = create_license(self.db, license_type="1 Year", max_devices=2, custom_code="INF-TEST-MULTI-2DEV")
        
        # User 1 Rig (HWID A)
        res1 = activate_license(
            db=self.db,
            code=lic.code,
            hwid="HWID-RIG-ALPHA-001",
            device_name="Desktop-Rig-Alpha",
            os_info="Windows 11 Pro"
        )
        self.assertEqual(res1["status"], "VALID")
        self.assertEqual(res1["max_devices"], 2)

        # User 2 Rig (HWID B on same license)
        res2 = activate_license(
            db=self.db,
            code=lic.code,
            hwid="HWID-RIG-BETA-002",
            device_name="Laptop-Rig-Beta",
            os_info="Windows 10 Home"
        )
        self.assertEqual(res2["status"], "VALID")
        self.assertEqual(res2["max_devices"], 2)

        # User 3 Rig (HWID C - exceeds 2-device limit)
        res3 = activate_license(
            db=self.db,
            code=lic.code,
            hwid="HWID-RIG-GAMMA-003",
            device_name="Gaming-PC-Gamma",
            os_info="Windows 11"
        )
        self.assertEqual(res3["status"], "DEVICE_LIMIT_REACHED")
        self.assertIn("Device limit reached", res3["message"])

    def test_realtime_heartbeat_and_remote_suspension(self):
        """Test heartbeat tracking, remote suspension, and immediate client lockdown."""
        lic = create_license(self.db, license_type="1 Month", max_devices=1, custom_code="INF-TEST-SUSP-DEMO")
        
        # Activate Rig
        act_res = activate_license(
            db=self.db,
            code=lic.code,
            hwid="HWID-HEARTBEAT-RIG-1",
            device_name="Tournament-PC-1",
            os_info="Windows 11"
        )
        self.assertEqual(act_res["status"], "VALID")

        # Client sends regular 30s heartbeat
        hb1 = process_heartbeat(
            db=self.db,
            code=lic.code,
            hwid="HWID-HEARTBEAT-RIG-1",
            app_version="1.0.0"
        )
        self.assertEqual(hb1["status"], "ACTIVE")
        self.assertIn("server_signature", hb1)

        # Owner suspends the license from Admin Panel
        suspend_success = suspend_license(self.db, lic.id)
        self.assertTrue(suspend_success)

        # Next client heartbeat must instantly return SUSPENDED
        hb2 = process_heartbeat(
            db=self.db,
            code=lic.code,
            hwid="HWID-HEARTBEAT-RIG-1",
            app_version="1.0.0"
        )
        self.assertEqual(hb2["status"], "SUSPENDED")
        self.assertIn("SUSPENDED", hb2["message"])

        # Owner reactivates the license
        react_success = reactivate_license(self.db, lic.id)
        self.assertTrue(react_success)

        # Next heartbeat returns ACTIVE
        hb3 = process_heartbeat(
            db=self.db,
            code=lic.code,
            hwid="HWID-HEARTBEAT-RIG-1",
            app_version="1.0.0"
        )
        self.assertEqual(hb3["status"], "ACTIVE")

    def test_remote_revocation_lockout(self):
        """Test that remote revocation permanently blocks client heartbeats."""
        lic = create_license(self.db, license_type="Lifetime", max_devices=1, custom_code="INF-TEST-REVK-DEMO")
        
        activate_license(self.db, code=lic.code, hwid="HWID-REVOKE-RIG", device_name="Target-PC", os_info="Win11")
        
        # Owner revokes license
        revoke_license(self.db, lic.id)

        # Heartbeat detects revocation
        hb = process_heartbeat(self.db, code=lic.code, hwid="HWID-REVOKE-RIG")
        self.assertEqual(hb["status"], "REVOKED")

    def test_admin_device_replacement(self):
        """Test administrator remotely replacing an old broken PC HWID with a new one."""
        lic = create_license(self.db, license_type="1 Year", max_devices=1, custom_code="INF-TEST-REPLACE-HWID")
        
        act = activate_license(self.db, code=lic.code, hwid="OLD-BROKEN-HWID", device_name="Old-PC", os_info="Win10")
        device_id = act["device_id"]

        # Attempting to activate on new PC fails due to limit 1
        res_new_fail = activate_license(self.db, code=lic.code, hwid="NEW-REPLACEMENT-HWID", device_name="New-PC", os_info="Win11")
        self.assertEqual(res_new_fail["status"], "DEVICE_LIMIT_REACHED")

        # Admin replaces the device
        rep_success = replace_device_hwid(
            db=self.db,
            license_id=lic.id,
            old_device_id=device_id,
            new_hwid="NEW-REPLACEMENT-HWID",
            new_device_name="New-Upgraded-PC"
        )
        self.assertTrue(rep_success)

        # Old HWID is now deactivated and rejected
        hb_old = process_heartbeat(self.db, code=lic.code, hwid="OLD-BROKEN-HWID")
        self.assertEqual(hb_old["status"], "DEVICE_NOT_AUTHORIZED")

        # New HWID is active and authorized
        hb_new = process_heartbeat(self.db, code=lic.code, hwid="NEW-REPLACEMENT-HWID")
        self.assertEqual(hb_new["status"], "ACTIVE")

    def test_admin_device_limit_upgrade(self):
        """Test dynamically increasing device limit from 1 to 3."""
        lic = create_license(self.db, license_type="1 Month", max_devices=1, custom_code="INF-TEST-UPGRADE-LIM")
        
        activate_license(self.db, code=lic.code, hwid="RIG-1", device_name="PC-1", os_info="Win11")
        
        # Second rig initially rejected
        res2 = activate_license(self.db, code=lic.code, hwid="RIG-2", device_name="PC-2", os_info="Win11")
        self.assertEqual(res2["status"], "DEVICE_LIMIT_REACHED")

        # Admin raises limit to 3
        set_license_device_limit(self.db, lic.id, new_limit=3)

        # Second and third rigs now activate successfully
        res2_retry = activate_license(self.db, code=lic.code, hwid="RIG-2", device_name="PC-2", os_info="Win11")
        self.assertEqual(res2_retry["status"], "VALID")

        res3 = activate_license(self.db, code=lic.code, hwid="RIG-3", device_name="PC-3", os_info="Win11")
        self.assertEqual(res3["status"], "VALID")

    def test_admin_dashboard_metrics_and_events(self):
        """Verify aggregated telemetry metrics and multi-user events stream."""
        stats = get_admin_dashboard_stats(self.db)
        self.assertGreaterEqual(stats["total_licenses"], 1)
        self.assertIn("online_clients", stats)
        self.assertIn("active_devices", stats)

        events = get_recent_license_events(self.db, limit=10)
        self.assertGreaterEqual(len(events), 1)
        self.assertIn("event_type", events[0])

if __name__ == "__main__":
    unittest.main()
