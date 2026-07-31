"""Export a trained YOLO model to ONNX / NCNN / TFLite for edge deployment.

Pick the fastest format only AFTER benchmarking on the target Pi — do not
assume. Lazy ultralytics import.

Usage: python -m src.deployment.export_model --weights best.pt --format ncnn
"""
from __future__ import annotations

import argparse
from pathlib import Path


def export(weights: str, fmt: str, imgsz: int):
    from ultralytics import YOLO  # lazy

    model = YOLO(weights)
    return model.export(format=fmt, imgsz=imgsz)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--format", default="onnx", choices=["onnx", "ncnn", "tflite", "torchscript"])
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()
    if not Path(args.weights).exists():
        raise SystemExit(f"Weights not found: {args.weights}")
    path = export(args.weights, args.format, args.imgsz)
    print(f"Exported -> {path}")


if __name__ == "__main__":
    main()
