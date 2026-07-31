# Poultry Monitoring System

IoT-based broiler health monitoring and farm-tracking system for Yaoundé,
Cameroon. M.Eng engineering project.

The system has three subsystems:

| Subsystem | Folder | What it does |
|-----------|--------|--------------|
| **Web application** | `backend/` | Django 5.2 + DRF. Farm/flock/health/inventory/finance management, IoT & vision REST APIs, alerts, dashboards, reports, role-based access. |
| **Machine learning** | `ml/` | Ultralytics YOLO (default **YOLO11n**) detection pipeline: dataset tools, EDA, training, evaluation, export (ONNX/NCNN/TFLite), inference. Optional EfficientNet benchmark. |
| **Edge client** | `edge/` | Mockable Raspberry Pi client: sensors, camera, on-device inference, threshold control, durable offline queue, retry, heartbeat. |

> **Disclaimer:** Machine-vision predictions are early-warning indicators and
> **do not replace veterinary diagnosis**. MQ-series gas output is reported as a
> *relative ammonia-risk indicator*, never as a calibrated ppm value.

## Quick start (backend, local SQLite smoke test)

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate    |  Unix:  source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env            # edit DJANGO_SECRET_KEY etc.
python manage.py migrate
python manage.py setup_roles       # create role groups + permissions
python manage.py seed_demo         # clearly-labelled demo data
python manage.py createsuperuser   # optional, for /admin
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with a demo account
(`demo_admin` / `demo_owner` / `demo_manager` / `demo_worker` / `demo_vet`,
password `DemoPass123!`).

## PostgreSQL (recommended, matches production)

Set in `backend/.env`:

```
DB_ENGINE=postgres
DB_NAME=poultry
DB_USER=poultry
DB_PASSWORD=poultry
DB_HOST=localhost
DB_PORT=5432
```

Or run the whole stack with Docker:

```bash
cp .env.example .env   # set DJANGO_SECRET_KEY, DB_PASSWORD
docker compose up --build
```

## Tests

```bash
cd backend && pytest        # backend (Django + DRF)
cd ml && pytest             # ML data tools / class mapping / inference contract
cd edge && pytest           # edge client (queue, control, inference, heartbeat)
```

## Documentation

See [`docs/`](docs/): API guide + Postman collection (`docs/api/`), database
dictionary, user-role guide, deployment, troubleshooting. ML and edge guides are
in [`ml/README.md`](ml/README.md) and [`edge/README.md`](edge/README.md).
Project status and remaining hardware/data-dependent work:
[`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md).
