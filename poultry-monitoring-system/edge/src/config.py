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

    # --- Hardware pin map (BCM numbering; matches HARDWARE.md and Table 3.9) --
    dht_pin: int = field(default_factory=lambda: int(os.environ.get("PMS_DHT_PIN", "4")))
    relay_fan_pin: int = field(default_factory=lambda: int(os.environ.get("PMS_RELAY_FAN_PIN", "17")))
    relay_heater_pin: int = field(default_factory=lambda: int(os.environ.get("PMS_RELAY_HEATER_PIN", "27")))
    relay_active_low: bool = field(default_factory=lambda: _b("PMS_RELAY_ACTIVE_LOW", True))
    relay_interlock: bool = field(default_factory=lambda: _b("PMS_RELAY_INTERLOCK", True))
    status_led_pin: int = field(default_factory=lambda: int(os.environ.get("PMS_STATUS_LED_PIN", "24")))
    # No camera attached yet? Leave this off, or every cycle raises a capture
    # failure and the device-alert queue fills with noise that hides real faults.
    vision_enabled: bool = field(default_factory=lambda: _b("PMS_VISION_ENABLED", True))

    # --- Gas sensor -----------------------------------------------------------
    # Backend: "ads1115" | "mcp3008" | "dout". Only "dout" needs no ADC, and it
    # yields a trip point rather than a magnitude — see hardware/gas.py.
    gas_backend: str = field(default_factory=lambda: os.environ.get("PMS_GAS_BACKEND", "dout"))
    gas_channel: int = field(default_factory=lambda: int(os.environ.get("PMS_GAS_CHANNEL", "0")))
    gas_dout_pin: int = field(default_factory=lambda: int(os.environ.get("PMS_GAS_DOUT_PIN", "22")))
    gas_divider_ratio: float = field(default_factory=lambda: float(os.environ.get("PMS_GAS_DIVIDER_RATIO", "2.0")))
    # Per-sensor calibration from tools/mq135_baseline.py. Never copy between units.
    gas_baseline_v: float = field(default_factory=lambda: float(os.environ.get("PMS_GAS_BASELINE_V", "0.4")))
    gas_span_v: float = field(default_factory=lambda: float(os.environ.get("PMS_GAS_SPAN_V", "1.6")))
    gas_warmup_seconds: int = field(default_factory=lambda: int(os.environ.get("PMS_GAS_WARMUP_SECONDS", "180")))

    # --- Control law ----------------------------------------------------------
    # Hysteresis and minimum dwell times stop the relay chattering when a
    # reading sits on a threshold; without them a fan on the boundary switches
    # every sampling interval and the contacts wear out in weeks.
    hysteresis_c: float = field(default_factory=lambda: float(os.environ.get("PMS_HYSTERESIS_C", "1.0")))
    min_on_seconds: int = field(default_factory=lambda: int(os.environ.get("PMS_MIN_ON_SECONDS", "120")))
    min_off_seconds: int = field(default_factory=lambda: int(os.environ.get("PMS_MIN_OFF_SECONDS", "120")))
    humidity_max_pct: float = field(default_factory=lambda: float(os.environ.get("PMS_HUMIDITY_MAX_PCT", "75.0")))
    gas_risk_fan_on: float = field(default_factory=lambda: float(os.environ.get("PMS_GAS_RISK_FAN_ON", "0.8")))
