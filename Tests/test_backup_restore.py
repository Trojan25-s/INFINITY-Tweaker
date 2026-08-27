"""
Automated unit tests for snapshot backups and change history logging.
"""
import unittest
from Restore.backup_manager import create_backup_snapshot, list_backup_snapshots, get_snapshot
from Restore.change_history import record_change, get_change_history

class TestBackupRestore(unittest.TestCase):
    def test_snapshot_creation(self):
        test_data = {"power_plan": "High Performance", "test_key": 123}
        snap_id = create_backup_snapshot("Test Restore Point", test_data)
        self.assertTrue(snap_id.startswith("SNAP-"))

        snaps = list_backup_snapshots()
        self.assertTrue(any(s["id"] == snap_id for s in snaps))

        retrieved = get_snapshot(snap_id)
        self.assertEqual(retrieved["name"], "Test Restore Point")
        self.assertEqual(retrieved["state_data"]["test_key"], 123)

    def test_change_history_recording(self):
        record_change("TestFeature", "TestSetting", "OldVal", "NewVal", "SUCCESS", "UnitTest Details")
        history = get_change_history()
        self.assertGreater(len(history), 0)
        first = history[0]
        self.assertEqual(first["feature"], "TestFeature")
        self.assertEqual(first["result"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
