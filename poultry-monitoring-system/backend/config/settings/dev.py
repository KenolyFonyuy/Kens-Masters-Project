"""Development settings: SQLite by default, PostgreSQL if DB_ENGINE is set.

The project is PostgreSQL-compatible. To run the dev server against PostgreSQL
(matching production) set DB_ENGINE=postgres and the DB_* variables in .env.
SQLite is used by default only for a fast local smoke test.
"""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, STORAGES
from .env import env_bool, env_int, env_str

DEBUG = env_bool("DJANGO_DEBUG", True)

# Development/tests don't run collectstatic, so use the non-manifest static
# storage (the manifest backend is used in production only).
STORAGES["staticfiles"]["BACKEND"] = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)

if env_str("DB_ENGINE", "sqlite").lower() in {"postgres", "postgresql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_str("DB_NAME", "poultry"),
            "USER": env_str("DB_USER", "poultry"),
            "PASSWORD": env_str("DB_PASSWORD", "poultry"),
            "HOST": env_str("DB_HOST", "localhost"),
            "PORT": env_str("DB_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Make the browsable API and console email convenient in development.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
