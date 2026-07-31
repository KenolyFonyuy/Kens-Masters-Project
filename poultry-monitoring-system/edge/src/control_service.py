"""Threshold-based actuator control (fan/heater) with event emission."""
from __future__ import annotations

import datetime as dt
import uuid


class ControlService:
    def __init__(self, temp_min_c=20.0, temp_max_c=32.0):
        self.temp_min_c = temp_min_c
        self.temp_max_c = temp_max_c
        self.fan_state = False
        self.heater_state = False

    def evaluate(self, reading: dict):
        """Return a list of actuator events triggered by this reading."""
        events = []
        temp = reading.get("temperature_c")
        if temp is None:
            return events
        new_fan = temp > self.temp_max_c
        new_heater = temp < self.temp_min_c
        if new_fan != self.fan_state:
            self.fan_state = new_fan
            events.append(self._event("fan", new_fan, f"temp {temp} vs max {self.temp_max_c}"))
        if new_heater != self.heater_state:
            self.heater_state = new_heater
            events.append(self._event("heater", new_heater, f"temp {temp} vs min {self.temp_min_c}"))
        return events

    def _event(self, actuator, state, reason):
        return {
            "event_uuid": str(uuid.uuid4()),
            "actuator": actuator,
            "new_state": state,
            "trigger": "threshold",
            "reason": reason,
            "device_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        }
