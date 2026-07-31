# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Missing staticfiles manifest entry` | Run `collectstatic` (prod) — dev uses the non-manifest storage automatically. |
| `RuntimeError: DJANGO_SECRET_KEY must be set` | Set a strong `DJANGO_SECRET_KEY` for `config.settings.prod`. |
| API returns 401/403 for a device | Check the `Authorization: Device <token>` header; the token may be revoked or for a different device. Tokens are shown once at creation — re-issue if lost. |
| Duplicate-looking records from a Pi | Expected to be deduped: same `reading_uuid`/`idempotency_key` returns the existing row (`"duplicate": true`). |
| Sensor reading `quality: rejected` | Value failed plausibility validation (temp/humidity out of range). See `rejection_reason`. |
| Alerts not firing on high temperature | Define an `EnvironmentalThreshold` for the farm/pen first. |
| `ModuleNotFoundError: ultralytics` when training | Install ML deps in a separate env: `pip install -r ml/requirements.txt`. Backend/edge run without it. |
| Edge client logs "offline … records remain queued" | The backend is unreachable; records persist in the SQLite queue and are retried next cycle (by design). |
| Migrations out of sync | `python manage.py makemigrations && python manage.py migrate`. |
