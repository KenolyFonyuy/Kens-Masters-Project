# Deployment Guide

## Docker Compose (PostgreSQL + Gunicorn + Nginx)

```bash
cp .env.example .env          # set DJANGO_SECRET_KEY (required), DB_PASSWORD, ALLOWED_HOSTS
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Services: `db` (postgres:16), `web` (Gunicorn, runs migrate + setup_roles +
collectstatic on start), `nginx` (reverse proxy, serves /static and /media).
Health check: `GET /healthz/`.

## Manual production (no Docker)

```bash
export DJANGO_SETTINGS_MODULE=config.settings.prod
export DJANGO_SECRET_KEY=...            # strong, unique
export DJANGO_ALLOWED_HOSTS=farm.example.com
export DB_ENGINE=postgres DB_HOST=... DB_PASSWORD=...
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py setup_roles
python backend/manage.py collectstatic --noinput
gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:8000 --workers 3
```

Put Nginx in front (see `docker/nginx.conf`) and terminate TLS with certbot.
Production settings enable SSL redirect, HSTS, secure/HTTP-only cookies and
`SECURE_PROXY_SSL_HEADER` (set `X-Forwarded-Proto https` at the proxy).

## Database backup / restore

```bash
# backup
docker compose exec db pg_dump -U poultry poultry > backup_$(date +%F).sql
# restore
cat backup.sql | docker compose exec -T db psql -U poultry poultry
```

## Edge deployment (Raspberry Pi)

See [`edge/README.md`](../edge/README.md). Install the systemd unit
`edge/services/poultry-edge.service`, put secrets in `/etc/poultry-edge.env`
(chmod 600), `systemctl enable --now poultry-edge`.
