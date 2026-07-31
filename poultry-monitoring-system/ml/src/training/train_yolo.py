"""Train a lightweight YOLO detector (default YOLO11n) via Ultralytics.

Paths and hyper-parameters come from a config file (configs/train.yaml) and/or
environment variables — never hard-coded user paths. Heavy imports are lazy so
this module can be imported (and unit-tested) without ultralytics/torch.

Usage:
    python -m src.training.train_yolo --config configs/train.yaml
Colab: set DATA_ROOT / PROJECT_DIR to Google Drive paths via env vars.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    # Environment overrides (useful in Colab).
    cfg["data"] = os.environ.get("DATASET_YAML", cfg.get("data"))
    cfg["project"] = os.environ.get("PROJECT_DIR", cfg.get("project", str(ROOT / "outputs" / "runs")))
    return cfg


def train(cfg: dict):
    from ultralytics import YOLO  # lazy heavy import

    model = YOLO(cfg.get("model", "yolo11n.pt"))
    results = model.train(
        data=cfg["data"],
        epochs=cfg.get("epochs", 100),
        imgsz=cfg.get("imgsz", 640),
        batch=cfg.get("batch", 16),
        optimizer=cfg.get("optimizer", "auto"),
        lr0=cfg.get("lr0", 0.01),
        patience=cfg.get("patience", 20),
        seed=cfg.get("seed", 42),
        project=cfg["project"],
        name=cfg.get("name", "broiler_yolo11n"),
        resume=cfg.get("resume", False),
        **cfg.get("augment", {}),
    )
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "configs" / "train.yaml"))
    args = ap.parse_args()
    cfg = load_config(args.config)
    if not cfg.get("data") or not Path(str(cfg["data"])).exists():
        raise SystemExit(
            "Dataset yaml not found. Prepare the dataset and run "
            "src.data.create_dataset_yaml first, or set DATASET_YAML."
        )
    print(f"Training {cfg.get('model')} on {cfg['data']} ...")
    train(cfg)


if __name__ == "__main__":
    main()
