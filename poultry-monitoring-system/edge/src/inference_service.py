"""On-device inference. Uses the ML subsystem detector if weights are present,
else a mock detector. Emits the vision-results payload contract.
"""
from __future__ import annotations

import datetime as dt
import uuid


class InferenceService:
    def __init__(self, weights="", confidence=0.35):
        self.weights = weights
        self.confidence = confidence
        self._detector = None

    def _detector_or_mock(self):
        if self._detector is not None:
            return self._detector
        if self.weights:
            try:  # pragma: no cover - needs ultralytics
                from ultralytics import YOLO
                self._detector = ("yolo", YOLO(self.weights))
                return self._detector
            except Exception:
                pass
        self._detector = ("mock", None)
        return self._detector

    def infer(self, frame, *, device_id, pen_code="", batch_code=""):
        kind, model = self._detector_or_mock()
        if kind == "yolo" and frame.get("array") is not None:  # pragma: no cover
            results = model.predict(frame["array"], conf=self.confidence, verbose=False)
            dets = []
            for r in results:
                for b in r.boxes:
                    dets.append({
                        "cls": model.names.get(int(b.cls[0]), str(int(b.cls[0]))),
                        "confidence": float(b.conf[0]),
                        "bbox": [float(v) for v in b.xywhn[0]],
                    })
        else:
            dets = [{"cls": "healthy", "confidence": 0.5, "bbox": [0.4, 0.4, 0.2, 0.2]}]
        dets.sort(key=lambda d: d["confidence"], reverse=True)
        top = dets[0]
        return {
            "result_uuid": str(uuid.uuid4()),
            "pen_code": pen_code,
            "batch_code": batch_code,
            "model_name": "yolo11n",
            "model_version": "edge",
            "predicted_class": top["cls"],
            "confidence": round(top["confidence"], 4),
            "detections": dets,
            "image_reference": frame.get("frame_ref", ""),
            "device_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        }
