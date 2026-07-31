"""HTTP client for the backend API with device-token auth and retry.

Uses urllib (no hard dependency on requests). Network errors are surfaced so
the caller can keep the record queued for later retry.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request


class ApiClient:
    def __init__(self, base, token, timeout=10):
        self.base = base.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _post(self, path, payload):
        url = f"{self.base}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Device {self.token}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def _get(self, path):
        url = f"{self.base}{path}"
        req = urllib.request.Request(url, method="GET")
        if self.token:
            req.add_header("Authorization", f"Device {self.token}")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    # endpoint helpers
    def send_sensor(self, payload):
        return self._post("/sensor-readings/", payload)

    def send_vision(self, payload):
        return self._post("/vision-results/", payload)

    def send_actuator(self, payload):
        return self._post("/actuator-events/", payload)

    def send_alert(self, payload):
        return self._post("/device-alerts/", payload)

    def heartbeat(self, payload):
        return self._post("/devices/heartbeat/", payload)

    def sync_batch(self, records):
        return self._post("/sync/batch/", {"records": records})

    def get_configuration(self, device_id):
        return self._get(f"/devices/{device_id}/configuration/")

    def get_thresholds(self, device_id):
        return self._get(f"/devices/{device_id}/thresholds/")
