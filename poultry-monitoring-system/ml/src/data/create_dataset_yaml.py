"""Generate the Ultralytics dataset.yaml from the processed data + class mapping.

Usage: python -m src.data.create_dataset_yaml --out data/processed/dataset.yaml
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from ..common.class_mapping import trained_classes

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "data" / "processed" / "dataset.yaml"))
    ap.add_argument("--root", default=str(ROOT / "data" / "processed"))
    args = ap.parse_args()
    classes = trained_classes()
    data = {
        "path": args.root,
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(classes),
        "names": classes,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"Wrote {out} with {len(classes)} classes: {classes}")


if __name__ == "__main__":
    main()
