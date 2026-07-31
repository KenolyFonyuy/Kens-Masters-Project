"""Tiny environment-variable helpers (no hard dependency on django-environ)."""
import os


def env_str(key: str, default: str = "") -> str:
    value = os.environ.get(key)
    return value if value not in (None, "") else default


def env_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(key: str, default: int = 0) -> int:
    value = os.environ.get(key)
    try:
        return int(value) if value not in (None, "") else default
    except (TypeError, ValueError):
        return default


def env_list(key: str, default: str = "") -> list[str]:
    raw = env_str(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]
