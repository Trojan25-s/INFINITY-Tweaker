"""
Automated unit tests for INFINITY Tweaker licensing backend and activation rules.
"""
import unittest
from datetime import datetime, timedelta, timezone
from Database.database import Base, engine, SessionLocal
from Database.models import License, Device, LicenseStatus
from Backend.Licensing.code_generator import generate_activation_code
from Backend.Licensing.license_service import create_license, activate_license, validate_license

class TestLicensing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_code_generator_format(self):
        code = generate_activation_code()
        self.assertTrue(code.startswith("INF-"))
        parts = code.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)

    def test_license_creation_and_activation(self):
        lic = create_license(self.db, license_type="1 Month", max_devices=1)
        self.assertIsNotNone(lic.id)
        self.assertEqual(lic.status, LicenseStatus.ACTIVE.value)

        # First activation on HWID 1
        res = activate_license(
            db=self.db,
            code=lic.code,
            hwid="TEST-HWID-DEVICE-1",
            device_name="Gaming Rig 1",
            os_info="Windows 11 Pro"
        )
        self.assertEqual(res["status"], "VALID")
        self.assertIn("Activation successful", res["message"])

        # Second activation on same HWID should succeed (idempotent validation)
        res_same = activate_license(
            db=self.db,
            code=lic.code,
            hwid="TEST-HWID-DEVICE-1",
            device_name="Gaming Rig 1",
            os_info="Windows 11 Pro"
        )
        self.assertEqual(res_same["status"], "VALID")

        # Second device on 1-device limit should be rejected
        res_device2 = activate_license(
            db=self.db,
            code=lic.code,
            hwid="TEST-HWID-DEVICE-2",
            device_name="Laptop",
            os_info="Windows 10"
        )
        self.assertEqual(res_device2["status"], "DEVICE_LIMIT_REACHED")

    def test_invalid_code_handling(self):
        res = activate_license(
            db=self.db,
            code="INF-FAKE-CODE-9999",
            hwid="TEST-HWID",
            device_name="PC",
            os_info="Windows"
        )
        self.assertEqual(res["status"], "INVALID")

    def test_revoked_license_handling(self):
        lic = create_license(self.db, license_type="Lifetime", max_devices=1)
        lic.status = LicenseStatus.REVOKED.value
        self.db.commit()

        res = activate_license(
            db=self.db,
            code=lic.code,
            hwid="TEST-HWID",
            device_name="PC",
            os_info="Windows"
        )
        self.assertEqual(res["status"], "REVOKED")

if __name__ == "__main__":
    unittest.main()
