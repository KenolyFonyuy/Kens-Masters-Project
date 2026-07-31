"""Edge configuration loaded from environment / .env (never hard-coded secrets).

Required env vars in production:
    PMS_API_BASE   e.g. https://farm.example.com/api/v1
    PMS_DEVICE_ID  e.g. PI-001
    PMS_DEVICE_TOKEN  bearer token issued by the server (store securely)
MOCK mode (default) needs none of these and uses simulated hardware.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _b(name, default=False):
    v = os.environ.get(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class EdgeConfig:
    api_base: str = field(default_factory=lambda: os.environ.get("PMS_API_BASE", "http://localhost:8000/api/v1"))
    device_id: str = field(default_factory=lambda: os.environ.get("PMS_DEVICE_ID", "PI-MOCK-001"))
    token: str = field(default_factory=lambda: os.environ.get("PMS_DEVICE_TOKEN", ""))
    pen_code: str = field(default_factory=lambda: os.environ.get("PMS_PEN_CODE", "P1"))
    batch_code: str = field(default_factory=lambda: os.environ.get("PMS_BATCH_CODE", ""))
    mock: bool = field(default_factory=lambda: _b("PMS_MOCK", True))
    sampling_interval: int = field(default_factory=lambda: int(os.environ.get("PMS_SAMPLING_INTERVAL", "60")))
    heartbeat_interval: int = field(default_factory=lambda: int(os.environ.get("PMS_HEARTBEAT_INTERVAL", "120")))
    capture_interval: int = field(default_factory=lambda: int(os.environ.get("PMS_CAPTURE_INTERVAL", "300")))
    queue_path: str = field(default_factory=lambda: os.environ.get("PMS_QUEUE_PATH", "edge_queue.db"))
    weights: str = field(default_factory=lambda: os.environ.get("PMS_WEIGHTS", ""))
    confidence: float = field(default_factory=lambda: float(os.environ.get("PMS_CONFIDENCE", "0.35")))
    temp_max_c: float = 32.0
    temp_min_c: float = 20.0
