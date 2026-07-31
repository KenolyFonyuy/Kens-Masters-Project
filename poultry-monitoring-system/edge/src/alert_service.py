"""Local alerting for failures the server can't detect (e.g. camera failure)."""
from __future__ import annotations


class AlertService:
    def camera_failure(self, message="Camera capture failed"):
        return {"alert_type": "camera_failure", "severity": "warning", "title": "Camera failure", "message": message}

    def sensor_failure(self, message="Sensor read failed"):
        return {"alert_type": "sensor_failure", "severity": "warning", "title": "Sensor failure", "message": message}
