"""
INFINITY Benchmark: Real CPU compute, memory bandwidth, and disk response benchmarking.
Tracks and compares Before vs After optimization results.
"""
import time
import math
import tempfile
import os
import psutil
from typing import Dict, Any, List
from Restore.change_history import record_change

BENCHMARK_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_history.json")

def _run_cpu_compute_test(iterations: int = 1500000) -> float:
    """Real mathematical prime / floating-point computation benchmark."""
    start = time.perf_counter()
    val = 0.0
    for i in range(1, iterations):
        val += math.sqrt(i) * math.sin(i)
    elapsed = time.perf_counter() - start
    return round(elapsed, 4)

def _run_ram_throughput_test(block_size_mb: int = 128) -> float:
    """Real memory read/write throughput benchmark."""
    size_bytes = block_size_mb * 1024 * 1024
    start = time.perf_counter()
    data = bytearray(size_bytes)
    for i in range(0, size_bytes, 4096):
        data[i] = 0xFF
    elapsed = time.perf_counter() - start
    speed_mb_s = round(block_size_mb / max(0.001, elapsed), 1)
    return speed_mb_s

def _run_disk_latency_test() -> float:
    """Real file I/O latency benchmark."""
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"0" * (10 * 1024 * 1024))
        tmp_path = tmp.name
    
    elapsed = time.perf_counter() - start
    if os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    return round(elapsed * 1000, 2)  # in ms

def run_system_benchmark(stage: str = "CURRENT") -> Dict[str, Any]:
    """Execute complete real hardware benchmark."""
    cpu_time = _run_cpu_compute_test()
    ram_speed = _run_ram_throughput_test()
    disk_lat = _run_disk_latency_test()
    
    vm = psutil.virtual_memory()
    
    # Calculate unified benchmark score (higher is better)
    # CPU score: lower compute time = higher score
    cpu_score = round(max(10.0, 10000.0 / max(0.01, cpu_time)))
    ram_score = round(ram_speed * 1.5)
    disk_score = round(max(10.0, 5000.0 / max(1.0, disk_lat)))
    
    total_score = round((cpu_score * 0.4) + (ram_score * 0.4) + (disk_score * 0.2))

    result = {
        "stage": stage,
        "timestamp": time.time(),
        "total_score": total_score,
        "cpu_compute_time_sec": cpu_time,
        "cpu_score": cpu_score,
        "ram_speed_mb_s": ram_speed,
        "ram_score": ram_score,
        "disk_latency_ms": disk_lat,
        "disk_score": disk_score,
        "ram_available_mb": round(vm.available / (1024 * 1024), 1)
    }

    record_change("Benchmark", f"Benchmark ({stage})", "N/A", f"Score {total_score}", "SUCCESS")
    return result
