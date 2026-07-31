"""Evaluate a trained YOLO model on val/test and save metrics JSON.

Reports precision/recall/mAP50/mAP50-95 (per-class where available) and writes
to outputs/evaluation/. Metrics are produced ONLY by running on real data —
nothing is fabricated. Lazy ultralytics import.

Usage: python -m src.evaluation.evaluate_detection --weights runs/.../best.pt \
    --data data/processed/dataset.yaml --split test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "evaluation"


def evaluate(weights: str, data: str, split: str) -> dict:
    from ultralytics import YOLO  # lazy

    model = YOLO(weights)
    metrics = model.val(data=data, split=split)
    box = metrics.box
    result = {
        "split": split,
        "weights": weights,
        "map50": float(box.map50),
        "map50_95": float(box.map),
        "precision_mean": float(box.mp),
        "recall_mean": float(box.mr),
        "per_class_map50": {str(i): float(v) for i, v in enumerate(getattr(box, "maps", []))},
    }
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--split", default="test", choices=["val", "test"])
    args = ap.parse_args()
    if not Path(args.weights).exists():
        raise SystemExit(f"Weights not found: {args.weights} (train a model first)")
    result = evaluate(args.weights, args.data, args.split)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"metrics_{args.split}.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
