"""Edge client entry point.

Runs in MOCK mode by default (no hardware). One cycle: read sensors -> evaluate
actuators -> enqueue the reading with the resulting actuator states -> enqueue
any actuator events -> capture+infer -> enqueue vision, then flush the local
queue to the server (retrying failed sends), and send a heartbeat. Survives
restarts via the durable SQLite queue.

    python -m src.main --cycles 3        # run 3 cycles then exit (good for demo)
    python -m src.main                    # run forever

On real hardware set PMS_MOCK=false. The relays are driven de-energised on any
exit path — normal, Ctrl-C or crash — so an interrupted run never leaves the
heat lamp latched on.
"""
from __future__ import annotations

import argparse
import datetime as dt
import time

from .alert_service import AlertService
from .api_client import ApiClient
from .camera import get_camera
from .config import EdgeConfig
from .control_service import ControlService
from .hardware.relays import get_relay_bank
from .heartbeat import build_heartbeat
from .inference_service import InferenceService
from .local_queue import LocalQueue
from .logging_config import configure
from .sensor_service import get_adapter


def make_reading_payload(cfg, reading, actuator_states=None):
    import uuid
    payload = dict(reading)
    payload.update({
        "reading_uuid": str(uuid.uuid4()),
        "pen_code": cfg.pen_code,
        "batch_code": cfg.batch_code,
        "device_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    })
    # Storing the actuator states alongside the reading is what lets the server
    # answer "was the fan already running when it got this hot?" after the fact.
    payload.update(actuator_states or {})
    return payload


def run_cycle(cfg, log, queue, sensor, camera, control, infer, alerts):
    # 1. sensors
    try:
        reading = sensor.read()
    except Exception as exc:  # noqa: BLE001
        log.error("sensor read failed: %s", exc)
        queue.enqueue(f"alert-sensor-{time.time()}", "/device-alerts/", alerts.sensor_failure(str(exc)))
        reading = {}

    # 2. actuator control — evaluated before the reading is queued so the
    #    reading carries the actuator states this very sample produced.
    try:
        events = control.evaluate(reading)
    except Exception as exc:  # noqa: BLE001
        log.error("control failed, forcing actuators off: %s", exc)
        control.all_off()
        events = []
        queue.enqueue(f"alert-control-{time.time()}", "/device-alerts/", alerts.sensor_failure(f"control fault: {exc}"))

    if reading:
        payload = make_reading_payload(cfg, reading, control.states())
        queue.enqueue(payload["reading_uuid"], "/sensor-readings/", payload)

    for event in events:
        event["pen_code"] = cfg.pen_code
        log.info("actuator %s -> %s (%s)", event["actuator"], event["new_state"], event["reason"])
        queue.enqueue(event["event_uuid"], "/actuator-events/", event)

    # 3. vision
    if not cfg.vision_enabled:
        return
    try:
        frame = camera.capture()
        vision = infer.infer(frame, device_id=cfg.device_id, pen_code=cfg.pen_code, batch_code=cfg.batch_code)
        queue.enqueue(vision["result_uuid"], "/vision-results/", vision)
    except Exception as exc:  # noqa: BLE001
        log.error("vision failed: %s", exc)
        queue.enqueue(f"alert-cam-{time.time()}", "/device-alerts/", alerts.camera_failure(str(exc)))


def flush_queue(cfg, log, queue, client):
    sent = 0
    for item in queue.pending(limit=200):
        queue.mark_attempt(item["idempotency_key"])
        try:
            status, _ = client._post(item["endpoint"], item["payload"])
            if status in (200, 201):
                queue.mark_sent(item["idempotency_key"])
                sent += 1
        except Exception as exc:  # noqa: BLE001
            log.warning("send failed (will retry): %s", exc)
            break  # stop on network error; try again next cycle
    return sent


def build_services(cfg, log):
    """Construct every subsystem. Returns (sensor, camera, control, relays)."""
    relays = get_relay_bank(
        mock=cfg.mock,
        fan_pin=cfg.relay_fan_pin,
        heater_pin=cfg.relay_heater_pin,
        active_low=cfg.relay_active_low,
        interlock=cfg.relay_interlock,
    )
    control = ControlService(
        temp_min_c=cfg.temp_min_c,
        temp_max_c=cfg.temp_max_c,
        hysteresis_c=cfg.hysteresis_c,
        min_on_seconds=cfg.min_on_seconds,
        min_off_seconds=cfg.min_off_seconds,
        humidity_max_pct=cfg.humidity_max_pct,
        gas_risk_fan_on=cfg.gas_risk_fan_on,
        relays=relays,
    )
    sensor = get_adapter(mock=cfg.mock, cfg=cfg)
    camera = get_camera(mock=cfg.mock) if cfg.vision_enabled else None
    if not cfg.mock:
        log.info("Hardware mode: DHT22 on BCM%s, relays on BCM%s/BCM%s, gas backend=%s",
                 cfg.dht_pin, cfg.relay_fan_pin, cfg.relay_heater_pin, cfg.gas_backend)
        if hasattr(sensor, "warm_up"):
            sensor.warm_up()
    return sensor, camera, control, relays


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    ap.add_argument("--interval", type=int, default=None, help="override seconds between cycles")
    args = ap.parse_args()

    cfg = EdgeConfig()
    log = configure()
    log.info("Edge client starting (mock=%s, device=%s)", cfg.mock, cfg.device_id)

    queue = LocalQueue(cfg.queue_path)
    infer = InferenceService(cfg.weights, cfg.confidence)
    alerts = AlertService()
    client = ApiClient(cfg.api_base, cfg.token)
    sensor, camera, control, relays = build_services(cfg, log)

    interval = args.interval or cfg.sampling_interval
    cycle = 0
    try:
        while True:
            cycle += 1
            run_cycle(cfg, log, queue, sensor, camera, control, infer, alerts)
            try:
                sent = flush_queue(cfg, log, queue, client)
                client.heartbeat(build_heartbeat(queued_records=queue.pending_count()))
                log.info("cycle %s: sent=%s queued=%s", cycle, sent, queue.pending_count())
            except Exception as exc:  # noqa: BLE001
                log.warning("offline: %s (records remain queued)", exc)
            if args.cycles and cycle >= args.cycles:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        log.info("interrupted; shutting down")
    finally:
        # Fail-safe: actuators off before anything else is torn down.
        control.all_off()
        relays.close()
        if hasattr(sensor, "close"):
            sensor.close()
        queue.close()
        log.info("Edge client stopped; actuators de-energised")


if __name__ == "__main__":
    main()
