# Screenshot Capture Register

The web application **runs** (verified: migrations applied, system check clean,
`GET /healthz/` → 200, dashboard returns 200 in tests, and a live edge→server
round trip succeeded). Screenshots have **not** been embedded here because that
requires an interactive browser session; they must be captured manually so they
are real, not fabricated.

## How to capture (≈5 minutes)

```bash
cd backend
python manage.py migrate && python manage.py setup_roles && python manage.py seed_demo
python manage.py runserver
```
Sign in at http://127.0.0.1:8000/ as `demo_admin` (password `DemoPass123!`),
then capture each page below and save with the given filename in this folder.

| Filename | Page | URL | Status |
|---|---|---|---|
| `01_login.png` | Login | `/accounts/login/` | ready |
| `02_dashboard.png` | Dashboard | `/` | ready |
| `03_farms.png` | Farm management | `/farms/` | ready |
| `04_batches.png` | Batch management | `/flocks/` | ready |
| `05_mortality_form.png` | Mortality form | `/flocks/mortality/add/` | ready |
| `06_feed_form.png` | Feed form | `/feeding/add/` | ready |
| `07_health.png` | Health records | `/health/` | ready |
| `08_inventory.png` | Inventory | `/inventory/` | ready |
| `09_expenses.png` | Expenses | `/finance/expenses/` | ready |
| `10_sales.png` | Sales | `/finance/sales/` | ready |
| `11_environment.png` | Environmental dashboard (Chart.js) | `/monitoring/environment/` | ready |
| `12_vision_review.png` | Vision-prediction review | `/vision/` → open a result | ready |
| `13_alert_resolution.png` | Alert resolution | `/alerts/` → open an alert | ready |
| `14_reports.png` | Reports index | `/reports/` | ready |
| `15_mobile.png` | Mobile responsive view (≤480px width) | `/` | ready |

All listed pages are implemented, permission-checked, and populated by
`seed_demo`. No screenshots are fabricated.
"""
