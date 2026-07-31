"""Frame capture adapter (USB webcam, Pi camera, or mock)."""
from __future__ import annotations


class BaseCamera:
    def capture(self):
        raise NotImplementedError


class MockCamera(BaseCamera):
    def capture(self):
        # Returns a synthetic frame reference; no real image in mock mode.
        return {"frame_ref": "mock://frame.jpg", "array": None}


class UsbCamera(BaseCamera):  # pragma: no cover - needs hardware
    def __init__(self, index=0):
        self.index = index

    def capture(self):
        import cv2  # lazy

        cap = cv2.VideoCapture(self.index)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError("Camera capture failed")
        return {"frame_ref": "usb://frame.jpg", "array": frame}


def get_camera(mock=True):
    return MockCamera() if mock else UsbCamera()
