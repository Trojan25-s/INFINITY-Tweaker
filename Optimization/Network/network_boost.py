"""
Network Boost: Real ping latency, packet loss calculation, DNS benchmark, and network adapter inspection.
"""
import subprocess
import re
import socket
import time
from typing import Dict, Any, List

GAMING_ENDPOINTS = [
    {"name": "Cloudflare DNS", "host": "1.1.1.1"},
    {"name": "Google DNS", "host": "8.8.8.8"},
    {"name": "Quad9 DNS", "host": "9.9.9.9"},
    {"name": "Valve / Steam East", "host": "162.254.192.1"},
    {"name": "Riot Games Europe", "host": "104.160.141.3"}
]

def ping_host(host: str, count: int = 4) -> Dict[str, Any]:
    """Execute real ICMP ping test and parse min, avg, max, and packet loss."""
    try:
        cmd = f"ping -n {count} -w 1000 {host}"
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        
        # Loss match: "Lost = 0 (0% loss)"
        loss_match = re.search(r"\((\d+)%\s+loss\)", out)
        loss_pct = int(loss_match.group(1)) if loss_match else 0
        
        # Time match: "Minimum = 12ms, Maximum = 24ms, Average = 16ms"
        time_match = re.search(r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms", out)
        if time_match:
            return {
                "host": host,
                "reachable": True,
                "loss_pct": loss_pct,
                "min_ms": int(time_match.group(1)),
                "max_ms": int(time_match.group(2)),
                "avg_ms": int(time_match.group(3)),
                "jitter_ms": int(time_match.group(2)) - int(time_match.group(1))
            }
        else:
            return {"host": host, "reachable": False, "loss_pct": 100, "avg_ms": 999, "jitter_ms": 0}
    except Exception:
        return {"host": host, "reachable": False, "loss_pct": 100, "avg_ms": 999, "jitter_ms": 0}

def benchmark_dns_resolution() -> List[Dict[str, Any]]:
    """Measure real DNS lookup times across popular gaming domains."""
    test_domains = ["store.steampowered.com", "epicgames.com", "discord.com", "twitch.tv"]
    results = []
    
    for domain in test_domains:
        start = time.perf_counter()
        try:
            ip = socket.gethostbyname(domain)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            results.append({"domain": domain, "resolved_ip": ip, "latency_ms": latency_ms, "status": "OK"})
        except Exception:
            results.append({"domain": domain, "resolved_ip": "Failed", "latency_ms": 999.0, "status": "FAILED"})

    return results

def run_network_diagnostic() -> Dict[str, Any]:
    """Complete network health and gaming latency evaluation."""
    ping_results = []
    for ep in GAMING_ENDPOINTS:
        res = ping_host(ep["host"], count=3)
        res["name"] = ep["name"]
        ping_results.append(res)

    dns_bench = benchmark_dns_resolution()
    
    # Calculate connection quality grade
    avg_latencies = [p["avg_ms"] for p in ping_results if p["reachable"]]
    overall_avg_ms = round(sum(avg_latencies) / len(avg_latencies), 1) if avg_latencies else 999
    
    if overall_avg_ms < 25:
        grade = "EXCELLENT (A+)"
    elif overall_avg_ms < 50:
        grade = "VERY GOOD (A)"
    elif overall_avg_ms < 80:
        grade = "FAIR (B)"
    else:
        grade = "HIGH LATENCY (C)"

    return {
        "endpoints": ping_results,
        "dns_benchmark": dns_bench,
        "overall_avg_ms": overall_avg_ms,
        "quality_grade": grade,
        "recommendation": "Use a wired Gigabit Ethernet connection rather than Wi-Fi to eliminate radio interference jitter in competitive FPS gaming."
    }
