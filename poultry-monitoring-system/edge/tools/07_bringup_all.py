#!/usr/bin/env python3
"""Step 7 — end-to-end bring-up of the assembled unit, with no mains load.

    python3 tools/07_bringup_all.py

Exercises the full edge path: read both sensors, run the real control law with
forced readings, watch the relays follow, and confirm a record reaches the
durable queue. This is the test to re-run after any rewiring, and the one to
demonstrate in the viva.

SAFETY: LEDs only on the relay outputs. Connect the fan and heat lamp only
after every step here passes.
"""
import _bootstrap  # noqa: F401
import tempfile
import time

from src.config import EdgeConfig
from src.control_service import ControlService
from src.hardware.relays import RelayBank
from src.local_queue import LocalQueue
from src.main import make_reading_payload
from src.sensor_service import RealSensorAdapter

PASS, FAILED = "  PASS  ", " FAILED "
results = []


def check(label, fn):
    try:
        detail = fn()
        results.append(True)
        print(f"[{PASS}] {label}" + (f" — {detail}" if detail else ""))
    except Exception as exc:  # noqa: BLE001
        results.append(False)
        print(f"[{FAILED}] {label} — {exc}")


cfg = EdgeConfig()
cfg.mock = False
cfg.gas_warmup_seconds = 0  # bring-up is about wiring, not settling time
print(f"Device {cfg.device_id}  gas backend={cfg.gas_backend}\n")

sensor = RealSensorAdapter(cfg)
relays = RelayBank(cfg.relay_fan_pin, cfg.relay_heater_pin, cfg.relay_active_low, interlock=True)
control = ControlService(
    temp_min_c=cfg.temp_min_c, temp_max_c=cfg.temp_max_c,
    hysteresis_c=cfg.hysteresis_c, humidity_max_pct=cfg.humidity_max_pct,
    gas_risk_fan_on=cfg.gas_risk_fan_on, relays=relays,
    min_on_seconds=0, min_off_seconds=0,  # dwell timers would stall the test
)

reading = {}


def read_sensors():
    global reading
    reading = sensor.read()
    if reading.get("temperature_c") is None:
        raise RuntimeError("no temperature — check the DHT22 wiring (step 1)")
    return (f"{reading['temperature_c']} degC, {reading['humidity_pct']} %RH, "
            f"gas risk {reading['gas_risk_value']} [{reading['sensor_status']}]")


def fan_responds():
    control.evaluate({"temperature_c": cfg.temp_max_c + 5})
    if not relays.states()["fan_state"]:
        raise RuntimeError("fan relay did not energise on an over-temperature reading")
    time.sleep(1)
    control.evaluate({"temperature_c": (cfg.temp_min_c + cfg.temp_max_c) / 2})
    if relays.states()["fan_state"]:
        raise RuntimeError("fan relay did not release when the temperature returned to range")
    return "energised on hot, released on normal"


def heater_responds():
    control.evaluate({"temperature_c": cfg.temp_min_c - 5})
    if not relays.states()["heater_state"]:
        raise RuntimeError("heater relay did not energise on an under-temperature reading")
    time.sleep(1)
    control.evaluate({"temperature_c": (cfg.temp_min_c + cfg.temp_max_c) / 2})
    if relays.states()["heater_state"]:
        raise RuntimeError("heater relay did not release when the temperature returned to range")
    return "energised on cold, released on normal"


def interlock_holds():
    control.evaluate({"temperature_c": cfg.temp_min_c - 5})       # heater on
    control.evaluate({"temperature_c": cfg.temp_max_c + 5})       # now demand cooling
    states = relays.states()
    if states["fan_state"] and states["heater_state"]:
        raise RuntimeError("fan and heater were energised simultaneously")
    return "fan and heater never energised together"


def queues_a_record():
    with tempfile.TemporaryDirectory() as d:
        queue = LocalQueue(f"{d}/bringup.db")
        payload = make_reading_payload(cfg, reading, control.states())
        queue.enqueue(payload["reading_uuid"], "/sensor-readings/", payload)
        count = queue.pending_count()
        queue.close()
    if count != 1:
        raise RuntimeError(f"expected 1 queued record, found {count}")
    return "reading serialised and queued"


def fail_safe_off():
    control.all_off()
    if any(relays.states().values()):
        raise RuntimeError("a channel stayed energised after all_off()")
    return "both channels de-energised"


try:
    check("sensors read", read_sensors)
    check("fan relay follows the control law", fan_responds)
    check("heater relay follows the control law", heater_responds)
    check("fan/heater interlock", interlock_holds)
    check("reading reaches the durable queue", queues_a_record)
    check("fail-safe shutdown", fail_safe_off)
finally:
    relays.all_off()
    relays.close()
    sensor.close()

passed, total = sum(results), len(results)
print(f"\n{passed}/{total} checks passed.")
if passed == total:
    print("Unit is ready. Next: set PMS_MOCK=false and run `python3 -m src.main --cycles 3`.")
else:
    raise SystemExit(1)
