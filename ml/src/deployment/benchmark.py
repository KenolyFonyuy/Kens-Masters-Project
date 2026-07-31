"""Benchmark inference latency / FPS for a given model+format on this machine.

Run on the Raspberry Pi to obtain REAL edge numbers — do not extrapolate from a
laptop. Lazy ultralytics import. Outputs measured timings only.

Usage: python -m src.deployment.benchmark --weights best.onnx --runs 50 --imgsz 640
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path


def benchmark(weights, runs, imgsz):
    import numpy as np  # lazy
    from ultralytics import YOLO  # lazy

    model = YOLO(weights)
    dummy = (np.random.rand(imgsz, imgsz, 3) * 255).astype("uint8")
    # warmup
    for _ in range(3):
        model.predict(dummy, verbose=False)
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        model.predict(dummy, verbose=False)
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "weights": str(weights),
        "runs": runs,
        "imgsz": imgsz,
        "latency_ms_mean": statistics.mean(times),
        "latency_ms_p95": sorted(times)[int(0.95 * runs) - 1],
        "fps_mean": 1000.0 / statistics.mean(times),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--runs", type=int, default=50)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()
    if not Path(args.weights).exists():
        raise SystemExit(f"Weights not found: {args.weights}")
    print(json.dumps(benchmark(args.weights, args.runs, args.imgsz), indent=2))


if __name__ == "__main__":
    main()
