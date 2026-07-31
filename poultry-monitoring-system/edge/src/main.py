"""Edge client entry point.

Runs in MOCK mode by default (no hardware). One cycle: read sensors -> enqueue
reading, evaluate actuators -> enqueue events, capture+infer -> enqueue vision,
then flush the local queue to the server (retrying failed sends), and send a
heartbeat. Survives restarts via the durable SQLite queue.

    python -m src.main --cycles 3        # run 3 cycles then exit (good for demo)
    python -m src.main                    # run forever
"""
from __future__ import annotations

import argparse
import time

from .alert_service import AlertService
from .api_client import ApiClient
from .camera import get_camera
from .config import EdgeConfig
from .control_service import ControlService
from .heartbeat import build_heartbeat
from .inference_service import InferenceService
from .local_queue import LocalQueue
from .logging_config import configure
from .sensor_service import get_adapter


def make_reading_payload(cfg, reading):
    import uuid
    payload = dict(reading)
    payload.update({
        "reading_uuid": str(uuid.uuid4()),
        "pen_code": cfg.pen_code,
        "batch_code": cfg.batch_code,
    })
    return payload


def run_cycle(cfg, log, queue, sensor, camera, control, infer, alerts):
    # 1. sensors
    try:
        reading = sensor.read()
        payload = make_reading_payload(cfg, reading)
        queue.enqueue(payload["reading_uuid"], "/sensor-readings/", payload)
    except Exception as exc:  # noqa: BLE001
        log.error("sensor read failed: %s", exc)
        a = alerts.sensor_failure(str(exc))
        queue.enqueue(f"alert-sensor-{time.time()}", "/device-alerts/", a)
        reading = {}

    # 2. actuator control
    for event in control.evaluate(reading):
        queue.enqueue(event["event_uuid"], "/actuator-events/", event)

    # 3. vision
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    ap.add_argument("--interval", type=int, default=None, help="override seconds between cycles")
    args = ap.parse_args()

    cfg = EdgeConfig()
    log = configure()
    log.info("Edge client starting (mock=%s, device=%s)", cfg.mock, cfg.device_id)

    queue = LocalQueue(cfg.queue_path)
    sensor = get_adapter(mock=cfg.mock)
    camera = get_camera(mock=cfg.mock)
    control = ControlService(cfg.temp_min_c, cfg.temp_max_c)
    infer = InferenceService(cfg.weights, cfg.confidence)
    alerts = AlertService()
    client = ApiClient(cfg.api_base, cfg.token)

    interval = args.interval or cfg.sampling_interval
    cycle = 0
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
    queue.close()


if __name__ == "__main__":
    main()
