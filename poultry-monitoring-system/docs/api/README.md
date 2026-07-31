# REST API Guide (v1)

Base URL: `/api/v1/`. A Postman collection is provided in
[`poultry_api.postman_collection.json`](poultry_api.postman_collection.json).

## Authentication

| Principal | Header | Notes |
|---|---|---|
| **Device** | `Authorization: Device <token>` | Token issued at registration, shown once. Only the SHA-256 hash is stored. |
| **User** | session cookie or `Authorization: Token <drf-token>` | For browser/user APIs. |

## Standard response envelope

Success:
```json
{ "success": true, "data": { ... } }
```
Error:
```json
{ "success": false, "error": { "message": "…", "details": { ... } } }
```

## Endpoints

### Register a device  (user with `register_devices` capability)
`POST /api/v1/devices/register/`
```json
{ "device_id": "PI-001", "name": "House 1 Pi", "farm": "DEMO-YDE-01", "pen_code": "P1" }
```
→ `201` `{ "data": { "device_id": "PI-001", "created": true, "token": "…shown once…" } }`

### Heartbeat (device)
`POST /api/v1/devices/heartbeat/`
```json
{ "cpu_percent": 18.2, "memory_percent": 41.0, "uptime_seconds": 86400, "queued_records": 0 }
```

### Sensor reading (device, idempotent on `reading_uuid`)
`POST /api/v1/sensor-readings/`
```json
{
  "reading_uuid": "f1e2d3c4-0000-0000-0000-000000000001",
  "pen_code": "P1", "batch_code": "DEMO-B1",
  "temperature_c": 31.4, "humidity_pct": 64.0,
  "raw_gas_value": 320.0, "gas_risk_value": 0.55,
  "fan_state": true, "heater_state": false, "sensor_status": "ok"
}
```
→ `201` `{ "data": { "duplicate": false, "quality": "good", "gas_risk_category": "high", "alerts_raised": 1 } }`
Resubmitting the same `reading_uuid` → `200` with `"duplicate": true`.

### Vision result (device, idempotent on `result_uuid`)
`POST /api/v1/vision-results/`
```json
{
  "result_uuid": "a1b2c3d4-0000-0000-0000-000000000002",
  "pen_code": "P1", "batch_code": "DEMO-B1",
  "model_name": "yolo11n", "model_version": "v1",
  "predicted_class": "lethargic", "confidence": 0.78,
  "detections": [ { "cls": "lethargic", "confidence": 0.78, "bbox": [0.31,0.42,0.18,0.22] } ],
  "image_reference": "pi://2026-06-27/frame_0012.jpg"
}
```
→ `201` includes `risk_category`, `alert_raised`, and a veterinary disclaimer.

### Actuator event (device, idempotent on `event_uuid`)
`POST /api/v1/actuator-events/`
```json
{ "event_uuid": "…uuid…", "pen_code": "P1", "actuator": "fan", "new_state": true, "trigger": "threshold" }
```

### Device-raised alert (device)
`POST /api/v1/device-alerts/`
```json
{ "alert_type": "camera_failure", "severity": "warning", "title": "Camera offline", "pen_code": "P1" }
```

### Offline batch sync (device, idempotent on each `idempotency_key`)
`POST /api/v1/sync/batch/`
```json
{ "records": [
  { "idempotency_key": "PI-001:2026-06-27T08:00:00:sr", "record_type": "sensor_reading",
    "payload": { "reading_uuid": "…", "temperature_c": 24.0, "humidity_pct": 50.0 } }
] }
```
→ each result is `accepted`, `duplicate`, or `rejected`.

### Configuration / thresholds (device or user)
`GET /api/v1/devices/{device_id}/configuration/`
`GET /api/v1/devices/{device_id}/thresholds/`

## Throttling
Scoped rates (configurable via env): `device_ingest` 120/min, `device_config`
60/min, `user` 1000/h, `anon` 30/h.

## curl example
```bash
curl -X POST http://localhost:8000/api/v1/sensor-readings/ \
  -H "Authorization: Device $TOKEN" -H "Content-Type: application/json" \
  -d '{"reading_uuid":"'"$(uuidgen)"'","temperature_c":31.4,"humidity_pct":64}'
```
"""
