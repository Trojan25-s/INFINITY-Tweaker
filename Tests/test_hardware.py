"""
Automated unit tests for Hardware Inspection and Telemetry.
"""
import unittest
from System.Hardware.cpu_info import get_cpu_telemetry
from System.Hardware.gpu_info import get_gpu_telemetry
from System.Hardware.memory_info import get_ram_telemetry
from System.Hardware.storage_info import get_storage_telemetry
from AI.Analysis.bottleneck_analyzer import calculate_performance_score

class TestHardware(unittest.TestCase):
    def test_cpu_telemetry(self):
        cpu = get_cpu_telemetry()
        self.assertGreater(cpu["physical_cores"], 0)
        self.assertGreater(cpu["logical_threads"], 0)
        self.assertGreaterEqual(cpu["usage_pct"], 0.0)

    def test_gpu_telemetry(self):
        gpu = get_gpu_telemetry()
        self.assertIn("name", gpu)
        self.assertIn("vendor", gpu)

    def test_ram_telemetry(self):
        ram = get_ram_telemetry()
        self.assertGreater(ram["total_gb"], 0.0)
        self.assertGreater(ram["used_gb"], 0.0)
        self.assertGreaterEqual(ram["usage_pct"], 0.0)
        self.assertLessEqual(ram["usage_pct"], 100.0)

    def test_storage_telemetry(self):
        st = get_storage_telemetry()
        self.assertGreaterEqual(len(st["drives"]), 1)

    def test_performance_score_calculation(self):
        score = calculate_performance_score()
        self.assertGreaterEqual(score["overall_score"], 0)
        self.assertLessEqual(score["overall_score"], 100)
        self.assertGreaterEqual(score["cpu_score"], 0)
        self.assertGreaterEqual(score["gpu_score"], 0)
        self.assertGreaterEqual(score["ram_score"], 0)

if __name__ == "__main__":
    unittest.main()
