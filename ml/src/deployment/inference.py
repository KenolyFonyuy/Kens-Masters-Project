"""Inference service: run detection on an image/video/webcam and emit JSON that
matches the backend vision-results API contract.

Heavy imports are lazy. ``build_payload`` and ``MockDetector`` are import-safe
and unit-tested without ultralytics, so the JSON contract can be verified
anywhere.

Usage:
    python -m src.deployment.inference --weights best.pt --source image.jpg \
        --device-id PI-001 --pen-code P1 --batch-code B1 --conf 0.35
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path

from ..common.class_mapping import map_class, trained_classes


def build_payload(detections, *, device_id, pen_code="", batch_code="",
                  model_name="yolo11n", model_version="", image_reference=""):
    """Assemble the vision-results payload from a list of detections.

    Each detection: {"cls": str, "confidence": float, "bbox": [x, y, w, h]}.
    The top detection (by confidence) becomes the headline predicted_class.
    """
    detections = sorted(detections, key=lambda d: d.get("confidence", 0), reverse=True)
    top = detections[0] if detections else {"cls": "healthy", "confidence": 0.0}
    mapping = map_class(top["cls"])
    return {
        "result_uuid": str(uuid.uuid4()),
        "device_id": device_id,
        "pen_code": pen_code,
        "batch_code": batch_code,
        "model_name": model_name,
        "model_version": model_version,
        "predicted_class": top["cls"],
        "confidence": round(float(top.get("confidence", 0.0)), 4),
        "risk_category": mapping.get("risk_category"),
        "detections": detections,
        "image_reference": image_reference,
        "device_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    }


class MockDetector:
    """Deterministic detector for offline/CI use (no model weights needed)."""

    def __init__(self, classes=None):
        self.classes = classes or trained_classes()

    def predict(self, source):  # noqa: ARG002
        c = self.classes[0] if self.classes else "healthy"
        return [{"cls": c, "confidence": 0.5, "bbox": [0.4, 0.4, 0.2, 0.2]}]


class YoloDetector:
    def __init__(self, weights, conf=0.35, iou=0.45):
        from ultralytics import YOLO  # lazy

        self.model = YOLO(weights)
        self.conf = conf
        self.iou = iou
        self.names = self.model.names

    def predict(self, source):
        results = self.model.predict(source, conf=self.conf, iou=self.iou, verbose=False)
        dets = []
        for r in results:
            for b in r.boxes:
                cls_id = int(b.cls[0])
                x, y, w, h = [float(v) for v in b.xywhn[0]]
                dets.append({
                    "cls": self.names.get(cls_id, str(cls_id)),
                    "confidence": float(b.conf[0]),
                    "bbox": [x, y, w, h],
                })
        return dets


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", help="Model weights; omit to use the mock detector")
    ap.add_argument("--source", required=True)
    ap.add_argument("--device-id", required=True)
    ap.add_argument("--pen-code", default="")
    ap.add_argument("--batch-code", default="")
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--out", help="Write JSON payload to this path")
    args = ap.parse_args()

    detector = YoloDetector(args.weights, conf=args.conf) if args.weights else MockDetector()
    dets = detector.predict(args.source)
    payload = build_payload(
        dets, device_id=args.device_id, pen_code=args.pen_code,
        batch_code=args.batch_code, image_reference=str(args.source),
    )
    text = json.dumps(payload, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
