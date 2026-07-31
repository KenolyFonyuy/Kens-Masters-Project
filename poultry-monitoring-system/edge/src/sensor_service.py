"""Environmental sensing through a hardware adapter (real or mock).

Real DHT/MQ drivers can be dropped into ``RealSensorAdapter`` later without
changing the rest of the client. Gas output is a RAW value plus a relative
risk indicator (0-1) — NOT a calibrated ppm.
"""
from __future__ import annotations

import random


class BaseSensorAdapter:
    def read(self) -> dict:
        raise NotImplementedError


class MockSensorAdapter(BaseSensorAdapter):
    def __init__(self, seed=None):
        self._rng = random.Random(seed)

    def read(self) -> dict:
        raw_gas = self._rng.uniform(80, 450)
        return {
            "temperature_c": round(self._rng.uniform(22, 34), 1),
            "humidity_pct": round(self._rng.uniform(45, 80), 1),
            "raw_gas_value": round(raw_gas, 1),
            # crude normalisation to a 0-1 relative risk indicator
            "gas_risk_value": round(min(raw_gas / 600.0, 1.0), 2),
            "sensor_status": "ok",
        }


class RealSensorAdapter(BaseSensorAdapter):  # pragma: no cover - needs hardware
    """Placeholder for real drivers (e.g. Adafruit_DHT, MQ via ADC)."""

    def read(self) -> dict:
        raise NotImplementedError(
            "Install and wire real sensor drivers, then implement read()."
        )


def get_adapter(mock=True):
    return MockSensorAdapter() if mock else RealSensorAdapter()
