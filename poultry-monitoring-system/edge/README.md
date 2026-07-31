# Edge Client (Raspberry Pi)

Modular client that reads sensors, captures frames, runs on-device inference,
applies threshold control, and reliably ships records to the backend — with a
durable offline queue and idempotent submission.

## Runs in MOCK mode with no hardware

```bash
pip install pyyaml                 # minimal; opencv/ultralytics only for real HW/inference
PMS_MOCK=true python -m src.main --cycles 3 --interval 1
pytest                            # 8 tests, no hardware/network needed
```

In mock mode, simulated sensor/camera adapters are used so the full pipeline
(read → queue → flush → heartbeat) can be demonstrated and tested anywhere.

## Real deployment

1. Register the device via the API (`POST /api/v1/devices/register/`) to obtain a
   token (shown once).
2. Copy `config/edge.env.example` to `/etc/poultry-edge.env` (chmod 600) and set
   `PMS_API_BASE`, `PMS_DEVICE_ID`, `PMS_DEVICE_TOKEN`, `PMS_MOCK=false`,
   `PMS_WEIGHTS` (exported model).
3. Install the systemd unit:
   ```bash
   sudo cp services/poultry-edge.service /etc/systemd/system/
   sudo systemctl daemon-reload && sudo systemctl enable --now poultry-edge
   ```

## Architecture

| Module | Responsibility |
|---|---|
| `config.py` | Env-driven config (no hard-coded secrets) |
| `sensor_service.py` | Hardware adapter (Mock / Real); raw gas + relative risk |
| `camera.py` | Frame capture adapter (Mock / USB / Pi camera) |
| `inference_service.py` | YOLO if weights present, else mock; emits vision payload |
| `control_service.py` | Threshold fan/heater control + actuator events |
| `local_queue.py` | Durable SQLite outbox, idempotency keys, survives restart |
| `api_client.py` | HTTP client, device-token auth |
| `heartbeat.py` | Host metrics heartbeat |
| `alert_service.py` | Local failure alerts (camera/sensor) |
| `main.py` | Orchestrates one cycle + queue flush + heartbeat; retries on failure |

## Reliability guarantees

- Records persist in SQLite and are retried until the server confirms them.
- Each record carries a device-generated UUID / idempotency key, so retries and
  server-side dedup never create duplicates.
- The client recovers after restart (queue is on disk).
- Hardware adapters isolate real drivers, which can be added without touching the
  rest of the client.
"""
