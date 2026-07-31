"""
Base Django settings for the Poultry Monitoring System.

Settings are environment-driven (12-factor). Secrets must never be committed;
use a .env file (see .env.example) for local development.

Environment selection is handled by DJANGO_SETTINGS_MODULE:
    config.settings.dev   -> local development (SQLite default, DEBUG=True)
    config.settings.prod  -> production (PostgreSQL, DEBUG=False, hardened)
"""
from pathlib import Path

from dotenv import load_dotenv

from .env import env_bool, env_list, env_str

# backend/ directory (contains manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from the backend root if present.
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env_str("DJANGO_SECRET_KEY", "dev-insecure-change-me-in-production")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.farms",
    "apps.flocks",
    "apps.feeding",
    "apps.health",
    "apps.inventory",
    "apps.finance",
    "apps.iot",
    "apps.vision",
    "apps.alerts",
    "apps.reports",
    "apps.audit",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database (overridden per-environment)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
# Cameroon (Yaoundé) is in West Africa Time (UTC+1).
TIME_ZONE = env_str("DJANGO_TIME_ZONE", "Africa/Douala")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.iot.authentication.DeviceTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "device_ingest": env_str("DRF_THROTTLE_DEVICE", "120/minute"),
        "device_config": env_str("DRF_THROTTLE_CONFIG", "60/minute"),
        "user": env_str("DRF_THROTTLE_USER", "1000/hour"),
        "anon": env_str("DRF_THROTTLE_ANON", "30/hour"),
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "EXCEPTION_HANDLER": "apps.core.api.exception_handler",
}

# ---------------------------------------------------------------------------
# Messages -> Bootstrap mapping
# ---------------------------------------------------------------------------
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
# Cooldown (minutes) before an identical unchanged alert condition re-fires.
ALERT_COOLDOWN_MINUTES = int(env_str("ALERT_COOLDOWN_MINUTES", "30"))
# Minutes without a heartbeat before a device is considered offline.
DEVICE_OFFLINE_MINUTES = int(env_str("DEVICE_OFFLINE_MINUTES", "10"))
# Path to the ML class-mapping config consumed by the vision subsystem.
ML_CLASS_MAPPING_PATH = env_str(
    "ML_CLASS_MAPPING_PATH",
    str(BASE_DIR.parent / "ml" / "configs" / "class_mapping.yaml"),
)

SITE_NAME = "Poultry Monitoring System"
SITE_SHORT_NAME = "PMS"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = env_str("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} [{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
