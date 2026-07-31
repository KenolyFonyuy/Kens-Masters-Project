"""Load and query the configurable class -> risk-category/severity mapping.

The mapping lives in a YAML file shared with the ML subsystem
(``settings.ML_CLASS_MAPPING_PATH``) so the web app and the edge inference
client agree on how model classes translate to alerts.
"""
import functools
import logging

from django.conf import settings

logger = logging.getLogger("apps.vision")

_FALLBACK = {
    "class_mapping": {
        "healthy": {"risk_category": "normal", "severity": "information", "alert_type": None},
    },
    "default_severity": "warning",
    "review_outcomes": ["uncertain"],
}


@functools.lru_cache(maxsize=1)
def _load():
    path = settings.ML_CLASS_MAPPING_PATH
    try:
        import yaml

        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if "class_mapping" not in data:
            raise ValueError("class_mapping key missing")
        return data
    except Exception as exc:  # pragma: no cover - config/IO defensive path
        logger.warning("Falling back to built-in class mapping (%s): %s", path, exc)
        return _FALLBACK


def reload_mapping():
    _load.cache_clear()


def get_mapping():
    return _load().get("class_mapping", {})


def map_class(class_name: str):
    """Return the mapping dict for a class, or a safe default."""
    mapping = get_mapping()
    if class_name in mapping:
        entry = dict(mapping[class_name])
        entry.setdefault("severity", _load().get("default_severity", "warning"))
        return entry
    return {
        "risk_category": "uncertain",
        "severity": _load().get("default_severity", "warning"),
        "alert_type": None,
    }


def known_classes():
    return list(get_mapping().keys())
