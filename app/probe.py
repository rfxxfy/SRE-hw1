import json
import logging
import os
import time
from urllib.request import urlopen

from prometheus_client import Counter, Gauge, Histogram, start_http_server


BASE_URL = os.getenv("PROBE_URL", "http://taskboard-web:8000").rstrip("/")
INTERVAL = float(os.getenv("PROBE_INTERVAL_SECONDS", "15"))

checks = Counter("taskboard_probe_checks_total", "Probe checks", ["result"])
success = Gauge("taskboard_probe_success", "Result of the latest probe check")
duration = Histogram("taskboard_probe_duration_seconds", "Probe check duration")


def check():
    with urlopen(f"{BASE_URL}/readyz", timeout=5) as response:
        if response.status != 200:
            raise ValueError(f"readiness returned {response.status}")
    with urlopen(f"{BASE_URL}/api/tasks", timeout=5) as response:
        if response.status != 200 or not isinstance(json.load(response), list):
            raise ValueError("tasks API did not return a list")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    checks.labels(result="success")
    checks.labels(result="failure")
    success.set(0)
    start_http_server(9115)
    while True:
        started = time.monotonic()
        try:
            check()
        except Exception as exc:
            checks.labels(result="failure").inc()
            success.set(0)
            logging.warning("probe failed: %s", exc)
        else:
            checks.labels(result="success").inc()
            success.set(1)
        duration.observe(time.monotonic() - started)
        time.sleep(max(0, INTERVAL - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
