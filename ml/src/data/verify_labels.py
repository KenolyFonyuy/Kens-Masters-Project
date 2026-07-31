"""Validate YOLO-format label files against an image directory and class list.

Checks: label exists for each image, class ids in range, bbox coords in [0,1],
flags empty/missing labels. Usage:
    python -m src.data.verify_labels --images data/processed/images/train \
        --labels data/processed/labels/train --num-classes 6
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def validate(images: Path, labels: Path, num_classes: int) -> dict:
    issues, empty, missing, ok = [], [], [], 0
    for img in images.rglob("*"):
        if img.suffix.lower() not in IMAGE_EXT:
            continue
        label = labels / (img.stem + ".txt")
        if not label.exists():
            missing.append(img.name)
            continue
        lines = [ln for ln in label.read_text().splitlines() if ln.strip()]
        if not lines:
            empty.append(label.name)
            continue
        valid = True
        for ln in lines:
            parts = ln.split()
            if len(parts) < 5:
                issues.append({"file": label.name, "error": "too few fields"}); valid = False; break
            try:
                cid = int(parts[0]); coords = [float(x) for x in parts[1:5]]
            except ValueError:
                issues.append({"file": label.name, "error": "non-numeric"}); valid = False; break
            if not (0 <= cid < num_classes):
                issues.append({"file": label.name, "error": f"class id {cid} out of range"}); valid = False; break
            if any(not (0.0 <= c <= 1.0) for c in coords):
                issues.append({"file": label.name, "error": "coord out of [0,1]"}); valid = False; break
        if valid:
            ok += 1
    return {"ok": ok, "missing_labels": missing, "empty_labels": empty, "issues": issues}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--num-classes", type=int, required=True)
    args = ap.parse_args()
    print(json.dumps(validate(Path(args.images), Path(args.labels), args.num_classes), indent=2))


if __name__ == "__main__":
    main()
