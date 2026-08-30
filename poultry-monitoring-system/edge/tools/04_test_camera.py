#!/usr/bin/env python3
"""Step 4 — capture one frame and save it. Skip this until you own a camera.

    python3 tools/04_test_camera.py --index 0

A USB webcam normally appears as /dev/video0. A Pi Camera on the CSI ribbon
needs the picamera2 stack instead of OpenCV; this script covers USB only, which
is what the study's bill of materials specifies.
"""
import _bootstrap  # noqa: F401
import argparse
import pathlib

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--index", type=int, default=0, help="V4L2 device index")
ap.add_argument("--out", default="frame.jpg")
args = ap.parse_args()

try:
    import cv2
except ImportError:
    raise SystemExit("OpenCV missing. Install with: sudo apt install -y python3-opencv")

cap = cv2.VideoCapture(args.index)
if not cap.isOpened():
    raise SystemExit(
        f"Cannot open camera index {args.index}. Check `ls /dev/video*` and try another index."
    )
# The first frame off a USB webcam is often black while auto-exposure settles.
for _ in range(5):
    ok, frame = cap.read()
cap.release()

if not ok:
    raise SystemExit("Camera opened but returned no frame.")
cv2.imwrite(args.out, frame)
h, w = frame.shape[:2]
print(f"Captured {w}x{h} -> {pathlib.Path(args.out).resolve()}")
print("Open it and check the framing covers the birds at their level, evenly lit.")
