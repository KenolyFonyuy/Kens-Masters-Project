# Implementation Status

**Project:** IoT-Based Broiler Health Monitoring and Farm Tracking System (Yaoundé)
**Last updated:** 2026-06-27
**Environment:** Python 3.14.6 · Django 5.2.15 · DRF 3.17.1 (PostgreSQL-compatible; SQLite used for the dev smoke test)

## Verification snapshot (actually run)

| Check | Result |
|---|---|
| `manage.py check` | System check identified **no issues** |
| Migrations | **12** migration files, all applied successfully |
| Backend tests (`pytest`) | **57 passed** |
| ML tests (`pytest`) | **9 passed** |
| Edge tests (`pytest`) | **8 passed** |
| **Total tests** | **74 passed, 0 failed** |
| Ruff lint | 86 issues auto-fixed; remainder are minor style (semicolons in scripts) |
| `seed_demo` | Runs; demo farm/batch (live flock 932 after mortality+sales), 2 vision alerts |
| Live API round-trip | Edge client → running server: sensor & vision records persisted (verified counts increased) |

## Build size

backend: 140 Python modules · 12 migrations · 74 templates · 9 device API endpoints
ml: 20 source modules · 5 notebooks · edge: 12 modules · tests: 10 files

## Component status

### Backend (Django) — COMPLETE & RUNNING
- ✅ Settings split (base/dev/prod), 12-factor env config, PostgreSQL + SQLite
- ✅ Custom user model, auth (login/logout/password change+reset), profile
- ✅ Roles as Django Groups + capabilities (`setup_roles`), enforced in views/querysets/API/templates
- ✅ Green-and-white Bootstrap 5 theme, sidebar + topbar, responsive, empty states, error pages (403/404/500)
- ✅ Apps & models: accounts, farms, flocks, feeding, health, inventory, finance, iot, vision, alerts, reports, audit, dashboard
- ✅ Business rules: flock balance (derived + row-locked services), inventory ledger, sale/mortality/transfer validation, feed→inventory auto-decrement
- ✅ Dashboard (aggregated cards), Chart.js environmental charts, reports (11 types) with date filters + CSV export + print
- ✅ Audit logging + current-user middleware; health-check endpoint

### REST API (`/api/v1/`) — COMPLETE
- ✅ Device-token auth (hashed, shown once), throttling, standard envelope, uniform error handler
- ✅ Endpoints: register, heartbeat, sensor-readings, vision-results, actuator-events, device-alerts, sync/batch, configuration, thresholds
- ✅ Idempotency (device UUIDs + SyncRecord ledger); duplicate replays return existing rows
- ✅ Sensor validation (rejects impossible values), gas-risk categorisation, threshold→alert generation
- ✅ Vision ingestion → class mapping → visual-health alerts (with veterinary disclaimer)

### Alerts — COMPLETE
- ✅ All required alert types/severities/statuses, dedup + cooldown, state transitions with actor/time + immutable AlertAction log

### Vision review — COMPLETE
- ✅ Prediction-review page; original machine output never overwritten; accept/correct/uncertain/false/escalate; escalation can spawn a health observation

### Machine learning — CODE COMPLETE, NOT TRAINED
- ✅ Dataset tools (import w/ provenance+checksums, verify images/labels, duplicates, leakage-safe split, dataset.yaml, statistics)
- ✅ Training (YOLO11n, config/env-driven, conservative augmentation), evaluation, export (ONNX/NCNN/TFLite), inference (emits API payload), benchmark
- ✅ Optional EfficientNet baseline; class-mapping shared with backend/edge
- ✅ 5 notebooks (EDA/train/efficientnet/eval/export) — runnable, **empty outputs, PENDING cells**
- ⛔ **Not executed:** no training, metrics, curves, confusion matrices, or Pi benchmarks — dataset + GPU unavailable. Nothing fabricated. See `docs/dissertation-evidence/PENDING_ML_EVIDENCE.md`.

### Edge client (Raspberry Pi) — COMPLETE (mock-verified)
- ✅ Runs in mock mode with no hardware; hardware adapters for real drivers
- ✅ Sensors, camera, on-device inference, threshold control, durable SQLite queue, retry, idempotency, heartbeat, restart recovery
- ✅ systemd unit + env example; verified end-to-end against the running backend

### Deployment & docs — COMPLETE
- ✅ docker-compose (postgres + gunicorn + nginx), Dockerfile, nginx.conf, prod settings, `.env.example`
- ✅ README, backend/ml/edge guides, API guide + Postman collection, database dictionary, user-role guide, deployment, troubleshooting, ADRs

## Remaining hardware/data-dependent work
1. Acquire & licence-verify the Broiler RGB dataset; run dataset tools + EDA.
2. Train YOLO11n; run evaluation; record real metrics + plots.
3. Export + benchmark on a real Raspberry Pi; choose the fastest format.
4. Wire real sensor/camera drivers into the edge hardware adapters.
5. Capture real UI screenshots (procedure in `docs/screenshots/PENDING_SCREENSHOTS.md`).

## Known limitations
- Runs on Python 3.14 here; target/tested per spec is 3.12 (Django 5.2 supports both).
- Many CRUD list pages use a shared generic template; key pages (dashboard, farms, batches, alerts, devices, vision, inventory, finance, reports) have tailored templates.
- Notifications are in-app/console email only (no SMS/push integration yet).
"""
