# Database Dictionary (summary)

Every domain record inherits `TimeStampedUserModel`: `uid` (UUID, unique),
`created_at`, `updated_at`, `created_by`, `updated_by`.

## accounts
- **CustomUser**: username, email, `role` (ADMIN/OWNER/MANAGER/WORKER/VET), phone, `assigned_farms` (M2M).
- **UserProfile**: 1-1 user, job_title, bio, avatar, timezone.

## farms
- **Farm**: name, code (unique), location, city/region/country, lat/long, owner, is_demo, is_active.
- **Pen**: farm, name, code, capacity, floor_area_m2. Unique (farm, code).
- **Breed**, **Supplier**, **Customer**: reference entities.

## flocks
- **Batch**: farm, pen, breed, code, start/end dates, status, initial_quantity. Derived: `current_quantity`, `cumulative_mortality_rate`, `age_days`.
- **ChickEntry**, **TransferRecord**, **MortalityRecord**, **WeightRecord**, **DailyObservation**.

## feeding
- **FeedType** (optional `inventory_item` link), **FeedUsage** (auto-decrements inventory; `stock_applied`).

## health
- **HealthObservation** (severity, vet review, `vision_result` link), **Medication**, **TreatmentRecord**, **VaccinationSchedule**, **VaccinationRecord**.

## inventory
- **InventoryCategory**, **InventoryItem** (opening_stock, reorder_level; derived `current_stock`, `is_low_stock`), **StockMovement** (signed ledger; types receipt/issue/adjust±/expiry/damage).

## finance
- **Expense**, **Sale** (status draft/confirmed/cancelled; confirmed reduces flock), **Payment**.

## iot
- **IoTDevice** (device_id unique, status, last_seen_at, `is_online`), **DeviceToken** (key_hash only), **DeviceConfiguration**, **EnvironmentalThreshold**, **SensorReading** (raw_gas_value + gas_risk_value/category, quality, fan/heater state, `reading_uuid` unique), **ActuatorEvent** (`event_uuid`), **DeviceHeartbeat**, **SyncRecord** (`idempotency_key` unique).

## vision
- **VisionResult**: immutable machine output (predicted_class, confidence, detections JSON, `result_uuid`) + layered review (review_status, corrected_class, reviewer). `effective_class` = corrected or predicted.

## alerts
- **Alert** (type, severity, status, source, dedup_key, trigger_count, ack/resolve audit fields), **AlertAction** (state-change log), **NotificationPreference**.

## audit
- **AuditLog** (action, user, target, ip, metadata), **Attachment** (generic FK).

Key indexes: timestamps, farm, pen, batch, device, alert status/severity, sensor
type/category, predicted class. Unique constraints: farm.code, (farm,pen).code,
(farm,batch).code, reading_uuid, event_uuid, idempotency_key, result_uuid,
device_id, token key_hash.
