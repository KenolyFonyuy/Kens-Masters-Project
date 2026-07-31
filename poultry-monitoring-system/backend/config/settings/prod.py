"""Production settings: PostgreSQL, DEBUG=False, hardened security.

Every secret is read from the environment. The process will refuse to start
with the insecure development SECRET_KEY.
"""
from .base import *  # noqa: F401,F403
from .env import env_bool, env_int, env_list, env_str

DEBUG = False

SECRET_KEY = env_str("DJANGO_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY == "dev-insecure-change-me-in-production":
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set to a strong unique value in production."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_str("DB_NAME", "poultry"),
        "USER": env_str("DB_USER", "poultry"),
        "PASSWORD": env_str("DB_PASSWORD", ""),
        "HOST": env_str("DB_HOST", "db"),
        "PORT": env_str("DB_PORT", "5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
    }
}

# Security hardening
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool("DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE", False)
SESSION_COOKIE_AGE = env_int("DJANGO_SESSION_COOKIE_AGE", 60 * 60 * 8)  # 8h
SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# File log handler in addition to console.
LOGGING["handlers"]["file"] = {  # noqa: F405
    "class": "logging.handlers.RotatingFileHandler",
    "filename": env_str("DJANGO_LOG_FILE", "/var/log/poultry/app.log"),
    "maxBytes": 10 * 1024 * 1024,
    "backupCount": 5,
    "formatter": "verbose",
}
LOGGING["root"]["handlers"] = ["console", "file"]  # noqa: F405
