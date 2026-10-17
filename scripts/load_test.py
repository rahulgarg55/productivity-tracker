"""
Repeatable Load Testing and Capacity Validation for Productivity Tracker API
Measures requests/sec, latency percentiles (p50, p90, p95, p99), error rates under concurrency.
"""

import concurrent.futures
import os
import time
import requests

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("PRODUCTIVITY_ADMIN_TOKEN", "sys-admin-token-2026")
AUTH_HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

ENDPOINTS = [
    ("GET", "/health", None, None),
    ("GET", "/", None, None),
    ("GET", "/api/stats", None, None),
    ("GET", "/api/activities?limit=20", None, None),
    ("POST", "/api/screenshots", {"app_name": "vscode", "window_title": "load_test.py"}, AUTH_HEADERS),
]

def make_request(idx):
    method, path, body, headers = ENDPOINTS[idx % len(ENDPOINTS)]
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=5)
        else:
            r = requests.post(url, json=body, headers=headers, timeout=5)
        duration_ms = (time.perf_counter() - start) * 1000.0
        success = (200 <= r.status_code < 400) or r.status_code == 429
        return duration_ms, success, r.status_code
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return duration_ms, False, 500

def run_stage(concurrency, total_requests):
    latencies = []
    successes = 0
    failures = 0
    start_time = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            dur, ok, code = f.result()
            latencies.append(dur)
            if ok:
                successes += 1
            else:
                failures += 1

    total_time_sec = time.perf_counter() - start_time
    latencies.sort()

    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0
    p90 = latencies[int(len(latencies) * 0.90)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    avg = sum(latencies) / len(latencies) if latencies else 0
    rps = total_requests / total_time_sec if total_time_sec > 0 else 0

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "successful": successes,
        "failed": failures,
        "duration_sec": round(total_time_sec, 2),
        "rps": round(rps, 1),
        "avg_ms": round(avg, 2),
        "p50_ms": round(p50, 2),
        "p90_ms": round(p90, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
    }

def main():
    print("=" * 80)
    print(" PRODUCTIVITY TRACKER — LOAD TESTING & CAPACITY VALIDATION")
    print(f" Target Base URL: {BASE_URL}")
    print("=" * 80 + "\n")

    stages = [
        ("Smoke Stage (10 VUs, 50 reqs)", 10, 50),
        ("Moderate Stage (30 VUs, 150 reqs)", 30, 150),
        ("High Concurrency Stage (50 VUs, 250 reqs)", 50, 250),
    ]

    results = []
    for title, conc, reqs in stages:
        print(f"Running {title}...")
        res = run_stage(conc, reqs)
        results.append(res)
        print(f"  -> RPS: {res['rps']} req/s | Success: {res['successful']}/{res['total_requests']} | p95: {res['p95_ms']}ms")

    print("\n" + "=" * 80)
    print(f"{'Concurrency':<12} {'Total':<8} {'Success':<9} {'Failed':<8} {'RPS':<10} {'p50 (ms)':<10} {'p95 (ms)':<10} {'p99 (ms)':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['concurrency']:<12} {r['total_requests']:<8} {r['successful']:<9} {r['failed']:<8} {r['rps']:<10} {r['p50_ms']:<10} {r['p95_ms']:<10} {r['p99_ms']:<10}")
    print("=" * 80)

    any_failed = any(r["failed"] > 0 for r in results)
    if any_failed:
        print("[FAIL] Load test failed: Errors encountered under load.")
        exit(1)
    else:
        print("[PASS] ALL CAPACITY GATES PASSED (0 timeouts, 0 unexpected errors).")

if __name__ == "__main__":
    main()
