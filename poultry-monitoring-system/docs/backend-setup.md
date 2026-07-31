# Backend Setup & Common Commands

## Environment

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate     Unix:  source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env                 # set DJANGO_SECRET_KEY at minimum
```

## Database

SQLite is the default for a quick smoke test. For PostgreSQL (recommended), set
`DB_ENGINE=postgres` plus `DB_*` in `.env`, then create the database:

```bash
# with Docker:
docker compose up -d db
# or local psql:
createdb poultry && createuser poultry --pwprompt
```

## Standard commands

| Action | Command |
|---|---|
| Run migrations | `python manage.py migrate` |
| Make migrations | `python manage.py makemigrations` |
| Set up roles/permissions | `python manage.py setup_roles` |
| Create superuser | `python manage.py createsuperuser` |
| Seed demo data | `python manage.py seed_demo` (add `--reset` to wipe prior demo) |
| Run dev server | `python manage.py runserver` |
| Run tests | `pytest` |
| Lint / format | `ruff check . --fix` · `black .` |
| Collect static (prod) | `python manage.py collectstatic` |
| System check | `python manage.py check` |

## Settings selection

`DJANGO_SETTINGS_MODULE` selects the environment:
`config.settings.dev` (default in `manage.py`) or `config.settings.prod`
(used by `wsgi`/`asgi`). Tests use `dev`.

## ML & edge

ML and edge each have their own `requirements.txt` and READMEs — install them in
separate virtual environments. See [`../ml/README.md`](../ml/README.md) and
[`../edge/README.md`](../edge/README.md).
"""
