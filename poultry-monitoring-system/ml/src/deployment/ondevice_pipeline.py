"""On-device inference pipeline demo (Section 3.9.15).

Implements the flow drawn in Figure 3.18 (``ml_inference_flow``):

    capture frame -> preprocess -> frame-skip -> run quantised model ->
    confidence threshold -> aggregate over N frames -> flag visible risk /
    queue uncertain cases for human review -> POST result via REST.

The aggregation logic (:class:`FrameAggregator`) is **pure and unit-tested** so
the temporal-smoothing behaviour can be verified with no model weights, no
camera and no network. The heavy pieces (OpenCV frame capture, the YOLO
detector, the HTTP POST) are lazily imported and optional, so this module
imports cleanly in CI. Nothing here fabricates a result: with no weights it
uses the deterministic ``MockDetector`` and says so.

CLI examples::

    # Offline demo over a folder of frames using the mock detector:
    python -m src.deployment.ondevice_pipeline --source data/raw/sample --device-id PI-001

    # Real detector over a video, flag a class seen in >=3 of the last 5 frames:
    python -m src.deployment.ondevice_pipeline --weights best.pt --source clip.mp4 \
        --device-id PI-001 --pen-code P1 --batch-code B1 \
        --conf 0.35 --frame-skip 5 --window 5 --min-hits 3 --post-url http://server/api/v1/vision-results/
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, deque
from pathlib import Path

from ..common.class_mapping import map_class, trained_classes
from .inference import MockDetector, build_payload

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class FrameAggregator:
    """Temporal smoothing over a sliding window of per-frame top detections.

    A visible-risk class is only *flagged* when it is the thresholded top class
    in at least ``min_hits`` of the most recent ``window`` processed frames.
    This suppresses single-frame spurious detections (the "aggregate over N
    frames" step). ``healthy`` never raises a flag. A frame whose top class maps
    to the ``uncertain`` risk category is counted toward review, not toward a
    flag.
    """

    def __init__(self, window: int = 5, min_hits: int = 3, conf_threshold: float = 0.35):
        if window < 1 or min_hits < 1 or min_hits > window:
            raise ValueError("require 1 <= min_hits <= window")
        self.window = window
        self.min_hits = min_hits
        self.conf_threshold = conf_threshold
        self._recent: deque[str | None] = deque(maxlen=window)

    def update(self, detections: list[dict]) -> dict:
        """Feed one processed frame's detections; return the current decision.

        Returns a dict with keys: ``top`` (str|None after thresholding),
        ``flag`` (str|None class to raise), ``review`` (bool), ``counts`` (dict).
        """
        top = None
        if detections:
            best = max(detections, key=lambda d: d.get("confidence", 0.0))
            if best.get("confidence", 0.0) >= self.conf_threshold:
                top = best["cls"]
        self._recent.append(top)

        counts = Counter(c for c in self._recent if c is not None)
        flag = None
        review = False
        for cls, n in counts.items():
            if n < self.min_hits:
                continue
            risk = map_class(cls)
            if cls == "healthy" or risk.get("risk_category") in (None, "normal"):
                continue
            if risk.get("risk_category") == "uncertain" or risk.get("alert_type") is None:
                review = True
            else:
                flag = cls  # a concrete visible-risk class crossed the temporal threshold
        return {"top": top, "flag": flag, "review": review, "counts": dict(counts)}


def _iter_frames(source: str, frame_skip: int):
    """Yield (index, frame_ref) honouring frame-skip.

    For a directory: iterate image files. For a video/webcam: lazily use OpenCV.
    ``frame_ref`` is a path (folder mode) or a numpy array (video mode) — both
    are accepted by the detectors' ``predict``.
    """
    p = Path(source)
    if p.is_dir():
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() in IMAGE_EXT)
        for i, f in enumerate(files):
            if i % frame_skip == 0:
                yield i, str(f)
        return
    # video / webcam
    import cv2  # lazy, optional

    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
    i = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if i % frame_skip == 0:
                yield i, frame
            i += 1
    finally:
        cap.release()


def run_stream(source, detector, *, device_id, pen_code="", batch_code="",
               frame_skip=5, window=5, min_hits=3, conf=0.35, post_url=None,
               model_name="yolo11n", model_version=""):
    """Run the on-device loop over ``source`` and return a list of emitted events.

    Each event is a backend-contract payload (from :func:`build_payload`) tagged
    with ``routing`` = ``"flag"`` or ``"review"``. Only frames that cross the
    temporal threshold emit an event, matching Figure 3.18.
    """
    agg = FrameAggregator(window=window, min_hits=min_hits, conf_threshold=conf)
    events = []
    last_emitted = None
    for idx, frame_ref in _iter_frames(str(source), frame_skip):
        dets = detector.predict(frame_ref)            # preprocess+inference (detector-internal)
        decision = agg.update(dets)
        raised = decision["flag"] or ("uncertain" if decision["review"] else None)
        # Edge-emit on a change, so we don't spam identical alerts every frame.
        if raised and raised != last_emitted:
            payload = build_payload(
                dets, device_id=device_id, pen_code=pen_code, batch_code=batch_code,
                model_name=model_name, model_version=model_version,
                image_reference=f"frame:{idx}",
            )
            payload["routing"] = "review" if decision["review"] and not decision["flag"] else "flag"
            payload["aggregation"] = {"window": window, "min_hits": min_hits, "counts": decision["counts"]}
            events.append(payload)
            if post_url:
                _post(post_url, payload)
            last_emitted = raised
        elif not raised:
            last_emitted = None
    return events


def _post(url: str, payload: dict):
    import urllib.request  # lazy, stdlib

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            return resp.status
    except Exception as exc:  # noqa: BLE001 — demo must not crash the loop on a network hiccup
        print(f"POST failed ({exc}); result buffered locally in a real edge client.")
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", help="Model weights; omit to use the deterministic mock detector")
    ap.add_argument("--source", required=True, help="Image folder, video file, or webcam index")
    ap.add_argument("--device-id", required=True)
    ap.add_argument("--pen-code", default="")
    ap.add_argument("--batch-code", default="")
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--frame-skip", type=int, default=5)
    ap.add_argument("--window", type=int, default=5)
    ap.add_argument("--min-hits", type=int, default=3)
    ap.add_argument("--post-url", default=None)
    ap.add_argument("--out", help="Write emitted events JSON to this path")
    args = ap.parse_args()

    if args.weights:
        from .inference import YoloDetector
        detector = YoloDetector(args.weights, conf=args.conf)
        model_version = Path(args.weights).stem
    else:
        detector = MockDetector()
        model_version = "MOCK-no-weights"
        print("No --weights given: using deterministic MockDetector (demo only, not a real result).")

    events = run_stream(
        args.source, detector, device_id=args.device_id, pen_code=args.pen_code,
        batch_code=args.batch_code, frame_skip=args.frame_skip, window=args.window,
        min_hits=args.min_hits, conf=args.conf, post_url=args.post_url, model_version=model_version,
    )
    text = json.dumps(events, indent=2)
    print(text)
    print(f"\nEmitted {len(events)} event(s) from source '{args.source}'.")
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
