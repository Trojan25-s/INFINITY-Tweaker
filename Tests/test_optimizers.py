"""
Automated unit tests for system optimizers and safe cleaning routines.
"""
import unittest
from Optimization.CacheCleaner.cache_cleaner import CacheCleaner
from Optimization.RamOptimizer.ram_optimizer import optimize_ram
from Optimization.PowerPlan.power_plan import get_active_power_plan, list_available_power_plans
from Optimization.WindowsOptimizer.windows_optimizer import get_windows_tweaks_status

class TestOptimizers(unittest.TestCase):
    def test_cache_cleaner_scan(self):
        scan = CacheCleaner.scan_all()
        self.assertIn("total", scan)
        self.assertIn("user_temp", scan)
        self.assertIn("windows_temp", scan)
        self.assertIn("recycle_bin", scan)
        self.assertGreaterEqual(scan["total"]["bytes"], 0)

    def test_ram_optimizer_execution(self):
        res = optimize_ram()
        self.assertIn(res["result"], ["SUCCESS", "PARTIAL SUCCESS"])
        self.assertGreater(res["before_used_mb"], 0)
        self.assertGreater(res["after_used_mb"], 0)
        self.assertGreaterEqual(res["freed_mb"], 0)

    def test_power_plan_query(self):
        active = get_active_power_plan()
        self.assertTrue(len(active["guid"]) > 10)
        plans = list_available_power_plans()
        self.assertGreaterEqual(len(plans), 1)

    def test_windows_tweaks_structure(self):
        tweaks = get_windows_tweaks_status()
        self.assertGreaterEqual(len(tweaks), 4)
        for t in tweaks:
            self.assertIn("id", t)
            self.assertIn("name", t)
            self.assertIn("category", t)
            self.assertIn("risk", t)

if __name__ == "__main__":
    unittest.main()
