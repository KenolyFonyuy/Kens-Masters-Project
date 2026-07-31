"""Compute dataset statistics (class distribution, bbox sizes, image sizes).

Reads YOLO labels + images and prints a JSON report. Saves nothing unless
--out is given. Never invents numbers — only measures what exists.

Usage: python -m src.data.generate_statistics --images data/processed/images/train \
    --labels data/processed/labels/train --num-classes 6 --out outputs/eda/stats_train.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def compute(images: Path, labels: Path, num_classes: int) -> dict:
    class_counts = Counter()
    objs_per_image = []
    bbox_w, bbox_h = [], []
    n_images = 0
    empty = 0
    for img in images.rglob("*"):
        if img.suffix.lower() not in IMAGE_EXT:
            continue
        n_images += 1
        label = labels / (img.stem + ".txt")
        if not label.exists():
            objs_per_image.append(0); empty += 1; continue
        lines = [ln for ln in label.read_text().splitlines() if ln.strip()]
        objs_per_image.append(len(lines))
        if not lines:
            empty += 1
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 5:
                class_counts[int(parts[0])] += 1
                bbox_w.append(float(parts[3])); bbox_h.append(float(parts[4]))

    def stats(xs):
        return {"min": min(xs), "max": max(xs), "mean": sum(xs) / len(xs)} if xs else None

    return {
        "images": n_images,
        "empty_or_missing_labels": empty,
        "total_objects": sum(class_counts.values()),
        "class_distribution": {str(k): v for k, v in sorted(class_counts.items())},
        "objects_per_image": stats(objs_per_image),
        "bbox_width_norm": stats(bbox_w),
        "bbox_height_norm": stats(bbox_h),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--num-classes", type=int, default=6)
    ap.add_argument("--out")
    args = ap.parse_args()
    report = compute(Path(args.images), Path(args.labels), args.num_classes)
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
