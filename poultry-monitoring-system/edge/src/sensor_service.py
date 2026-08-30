"""Environmental sensing through a hardware adapter (real or mock).

Gas output is a RAW value plus a relative risk indicator (0-1) — NOT a
calibrated ppm. See hardware/gas.py for why that distinction is load-bearing.
"""
from __future__ import annotations

import logging
import random
import time

log = logging.getLogger("edge.sensors")


class BaseSensorAdapter:
    def read(self) -> dict:
        raise NotImplementedError

    def close(self):
        pass


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
    """DHT22 + MQ135 on a Raspberry Pi.

    One failing sensor does not fail the cycle. A reading with the DHT22 dead
    but the gas sensor alive still carries useful information, so the missing
    fields are sent as null and ``sensor_status`` names what degraded — the
    server stores the partial row rather than losing the sample entirely. Only
    a total failure of both sensors raises.
    """

    def __init__(self, cfg):
        from .hardware import gas as gas_mod
        from .hardware.dht22 import Dht22

        self.cfg = cfg
        self.dht = Dht22(pin_bcm=cfg.dht_pin)

        if cfg.gas_backend == "dout":
            backend = gas_mod.make_backend("dout", pin_bcm=cfg.gas_dout_pin)
        else:
            backend = gas_mod.make_backend(
                cfg.gas_backend,
                channel=cfg.gas_channel,
                divider_ratio=cfg.gas_divider_ratio,
            )
        self.gas = gas_mod.Mq135(backend, baseline_v=cfg.gas_baseline_v, span_v=cfg.gas_span_v)
        self._warmed_at = None

    def warm_up(self):
        """Block until the metal-oxide element has settled.

        Readings taken during warm-up are high and falling and would be logged
        as a false ammonia event, so the first sample must wait this out.
        """
        seconds = self.cfg.gas_warmup_seconds
        if seconds > 0:
            log.info("Gas sensor warm-up: waiting %ss before first reading", seconds)
            time.sleep(seconds)
        self._warmed_at = time.time()

    def read(self) -> dict:
        reading = {
            "temperature_c": None,
            "humidity_pct": None,
            "raw_gas_value": None,
            "gas_risk_value": None,
            "sensor_status": "ok",
        }
        degraded = []

        try:
            temperature, humidity = self.dht.read()
            reading["temperature_c"] = temperature
            reading["humidity_pct"] = humidity
        except Exception as exc:  # noqa: BLE001
            log.warning("DHT22 read failed: %s", exc)
            degraded.append("dht22_failed")

        try:
            reading.update(self.gas.read())
        except Exception as exc:  # noqa: BLE001
            log.warning("MQ135 read failed: %s", exc)
            degraded.append("gas_failed")

        if len(degraded) == 2:
            raise RuntimeError("all sensors failed: " + ", ".join(degraded))
        if degraded:
            reading["sensor_status"] = ",".join(degraded)
        elif self.cfg.gas_backend == "dout":
            # Flagged on every sample so a reviewer of the stored data can see
            # the gas column is a trip point, not a measurement.
            reading["sensor_status"] = "ok,gas_threshold_only"
        return reading

    def close(self):
        self.dht.close()
        self.gas.close()


def get_adapter(mock=True, cfg=None):
    if mock:
        return MockSensorAdapter()
    if cfg is None:
        from .config import EdgeConfig

        cfg = EdgeConfig()
    return RealSensorAdapter(cfg)
