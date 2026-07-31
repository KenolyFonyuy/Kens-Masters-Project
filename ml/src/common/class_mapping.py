"""Load the shared class->risk mapping (ml/configs/class_mapping.yaml).

This is the SAME contract used by the Django backend so model classes map to
the same risk categories/severities everywhere.
"""
from __future__ import annotations

import os
from functools import lru_cache

import yaml

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "configs", "class_mapping.yaml")


@lru_cache(maxsize=4)
def load_mapping(path: str | None = None) -> dict:
    path = path or DEFAULT_PATH
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if "class_mapping" not in data:
        raise ValueError(f"'class_mapping' missing in {path}")
    return data


def trained_classes(path: str | None = None) -> list[str]:
    """The ordered list of classes intended for training (class_mapping keys)."""
    return list(load_mapping(path)["class_mapping"].keys())


def map_class(class_name: str, path: str | None = None) -> dict:
    mapping = load_mapping(path)["class_mapping"]
    if class_name in mapping:
        return dict(mapping[class_name])
    return {"risk_category": "uncertain", "severity": load_mapping(path).get("default_severity", "warning"), "alert_type": None}
