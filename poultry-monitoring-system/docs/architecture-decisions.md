# Architecture Decision Records

Concise ADRs for the significant technical choices.

## ADR-001 — Modular monorepo (backend / ml / edge)
Keep the three subsystems in one repository but strictly separated so each has
its own dependencies and lifecycle. The web app must run without PyTorch; the
edge client must run on a Pi without the Django stack.

## ADR-002 — Settings split (base/dev/prod), 12-factor config
`config.settings.{base,dev,prod}`. All secrets come from the environment
(`.env` locally). `prod` refuses to start with the insecure dev secret and
enables HSTS, secure cookies, SSL redirect. SQLite is allowed only for a dev
smoke test; PostgreSQL is the supported database.

## ADR-003 — Custom user + roles as Django Groups
`accounts.CustomUser` with a `role` field mirrored into Django Groups, so all
authorization flows through the standard permission framework. A
capability layer (`ROLE_CAPABILITIES`) handles fine-grained checks beyond model
permissions. Permissions are enforced in views, querysets, API permission
classes and templates — never UI-hiding alone.

## ADR-004 — Flock balance is derived, not stored
Live bird count = entries + transfers_in − transfers_out − mortality −
confirmed sales, computed from transaction rows. Mutations go through
`select_for_update` services that validate availability under a row lock, so
concurrent writes cannot oversell/over-cull. History is preserved; nothing is
silently deleted.

## ADR-005 — Inventory as an append-only ledger
Stock = opening + Σ(signed movements). Negative stock is blocked unless an
authorised adjustment overrides it. Feed usage auto-issues stock (idempotent).

## ADR-006 — Device-token auth + idempotent ingestion
Devices authenticate with `Authorization: Device <token>`; only the SHA-256
hash is stored, raw shown once. Every synchronised record carries a
device-generated UUID / idempotency key; replays return the existing row
(`get_or_create`, `SyncRecord` ledger) so a Pi resubmission never duplicates.

## ADR-007 — Gas sensing terminology
MQ-series sensors are not calibrated to ppm here. We store a raw ADC value plus
a processed *relative* gas-risk indicator (0–1) and a category. UI/text never
claim precise ammonia concentration.

## ADR-008 — Alerts with dedup + cooldown
Identical unchanged conditions within a cooldown window bump a trigger count
instead of spamming new alerts. State transitions record who/when and append an
immutable `AlertAction`.

## ADR-009 — Vision predictions are immutable; review is layered
The original model output (class, confidence, detections) is never overwritten.
Human review stores `corrected_class`, status, reviewer and timestamp
separately. A configurable YAML maps classes → risk categories/severities,
shared by backend, ML and edge.

## ADR-010 — YOLO11n default detector
Lightweight nano model for reproducibility and edge deployment. Export to
NCNN/ONNX/TFLite, choose the fastest **after** benchmarking on the actual Pi.
EfficientNet is an optional classification benchmark only.
