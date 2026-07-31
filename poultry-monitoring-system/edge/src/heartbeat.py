"""Build a heartbeat payload with best-effort host metrics."""
from __future__ import annotations

import datetime as dt


def build_heartbeat(queued_records=0, firmware_version="edge-1.0"):
    metrics = {"cpu_percent": None, "memory_percent": None, "disk_percent": None}
    try:  # psutil is optional
        import psutil  # pragma: no cover
        metrics["cpu_percent"] = psutil.cpu_percent()
        metrics["memory_percent"] = psutil.virtual_memory().percent
        metrics["disk_percent"] = psutil.disk_usage("/").percent
    except Exception:
        pass
    metrics["queued_records"] = queued_records
    metrics["firmware_version"] = firmware_version
    metrics["device_timestamp"] = dt.datetime.now().isoformat(timespec="seconds")
    return metrics
