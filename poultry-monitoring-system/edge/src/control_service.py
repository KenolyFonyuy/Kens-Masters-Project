"""Threshold-based actuator control (fan/heater) with event emission.

Three mechanisms keep a relay from chattering, which matters because a
mechanical contact on a poultry-house fan that toggles every sampling interval
wears out in weeks and floods the server with meaningless events:

  hysteresis    the turn-off threshold sits ``hysteresis_c`` below the turn-on
                threshold, so a reading hovering on the limit cannot oscillate
  minimum dwell once switched, a channel holds its state for ``min_on_seconds``
                / ``min_off_seconds`` before it may switch back
  edge-trigger  an event is emitted only on a change of state, never while a
                condition merely persists

The fan answers three signals — heat, humidity and gas risk — because all three
are relieved by air exchange. The heater answers temperature alone. When
temperature is unavailable the heater is forced off: "no reading" must never
mean "keep heating", which is the failure mode that sets a house on fire.
"""
from __future__ import annotations

import datetime as dt
import time
import uuid


class ControlService:
    def __init__(
        self,
        temp_min_c=20.0,
        temp_max_c=32.0,
        hysteresis_c=1.0,
        min_on_seconds=0,
        min_off_seconds=0,
        humidity_max_pct=None,
        gas_risk_fan_on=None,
        relays=None,
        clock=time.monotonic,
    ):
        self.temp_min_c = temp_min_c
        self.temp_max_c = temp_max_c
        self.hysteresis_c = hysteresis_c
        self.min_on_seconds = min_on_seconds
        self.min_off_seconds = min_off_seconds
        self.humidity_max_pct = humidity_max_pct
        self.gas_risk_fan_on = gas_risk_fan_on
        self.relays = relays
        self._clock = clock
        self.fan_state = False
        self.heater_state = False
        # None means "never switched", so the first transition is always allowed.
        self._changed_at = {"fan": None, "heater": None}

    # -- desired-state calculation -------------------------------------------
    def _want_fan(self, temp, humidity, gas_risk):
        """True while any ventilation trigger is above its turn-on threshold.

        Each signal keeps its own hysteresis band, and the fan runs while ANY
        of them asks for it — so it only stops once every trigger has fallen
        back through its turn-off threshold.
        """
        on = self.fan_state
        reasons = []
        if temp is not None:
            if temp > self.temp_max_c:
                reasons.append(f"temp {temp} > max {self.temp_max_c}")
            elif on and temp > self.temp_max_c - self.hysteresis_c:
                reasons.append(f"temp {temp} within hysteresis of max {self.temp_max_c}")
        if humidity is not None and self.humidity_max_pct is not None:
            if humidity > self.humidity_max_pct:
                reasons.append(f"humidity {humidity} > max {self.humidity_max_pct}")
            elif on and humidity > self.humidity_max_pct - self.hysteresis_c:
                reasons.append(f"humidity {humidity} within hysteresis of max {self.humidity_max_pct}")
        if gas_risk is not None and self.gas_risk_fan_on is not None:
            if gas_risk >= self.gas_risk_fan_on:
                reasons.append(f"gas risk {gas_risk} >= {self.gas_risk_fan_on}")
            elif on and gas_risk >= self.gas_risk_fan_on * 0.8:
                reasons.append(f"gas risk {gas_risk} within hysteresis of {self.gas_risk_fan_on}")
        return bool(reasons), "; ".join(reasons)

    def _want_heater(self, temp):
        if temp is None:
            return False, "no temperature reading — heater forced off (fail-safe)"
        if temp < self.temp_min_c:
            return True, f"temp {temp} < min {self.temp_min_c}"
        if self.heater_state and temp < self.temp_min_c + self.hysteresis_c:
            return True, f"temp {temp} within hysteresis of min {self.temp_min_c}"
        return False, f"temp {temp} >= min {self.temp_min_c}"

    def _dwell_elapsed(self, actuator, currently_on):
        """False while the channel is still inside its minimum on/off window."""
        changed_at = self._changed_at[actuator]
        if changed_at is None:
            return True
        required = self.min_on_seconds if currently_on else self.min_off_seconds
        return (self._clock() - changed_at) >= required

    # -- public API -----------------------------------------------------------
    def evaluate(self, reading: dict):
        """Return a list of actuator events triggered by this reading."""
        events = []
        temp = reading.get("temperature_c")
        humidity = reading.get("humidity_pct")
        gas_risk = reading.get("gas_risk_value")
        if temp is None and humidity is None and gas_risk is None:
            return events  # nothing measurable; leave actuators as they are

        want_fan, fan_reason = self._want_fan(temp, humidity, gas_risk)
        want_heater, heater_reason = self._want_heater(temp)

        # Never heat and ventilate at once: the fan exhausts the heat the lamp
        # is producing. Cooling wins, because heat stress kills faster than cold.
        if want_fan and want_heater:
            want_heater = False
            heater_reason = "suppressed by fan interlock: " + fan_reason

        # The fan is resolved first so the heater can be tested against the fan's
        # ACTUAL state. Testing it against the desired state is not enough: a fan
        # held on by its minimum-on timer would otherwise let the heater start,
        # energising both channels — the very thing the interlock prevents.
        if want_fan != self.fan_state and self._dwell_elapsed("fan", self.fan_state):
            self._apply("fan", want_fan)
            events.append(self._event("fan", want_fan, fan_reason))

        if want_heater and self.fan_state:
            want_heater = False
            heater_reason = "suppressed: fan still running"

        if want_heater != self.heater_state and self._dwell_elapsed("heater", self.heater_state):
            self._apply("heater", want_heater)
            events.append(self._event("heater", want_heater, heater_reason))
        return events

    def _apply(self, actuator, state):
        if self.relays is not None:
            self.relays.set(actuator, state)
        if actuator == "fan":
            self.fan_state = state
        else:
            self.heater_state = state
        self._changed_at[actuator] = self._clock()

    def states(self):
        """Current actuator states, in the shape SensorReadingSerializer wants."""
        return {"fan_state": self.fan_state, "heater_state": self.heater_state}

    def all_off(self):
        """Fail-safe shutdown: de-energise both channels."""
        if self.relays is not None:
            self.relays.all_off()
        self.fan_state = False
        self.heater_state = False

    def _event(self, actuator, state, reason):
        return {
            "event_uuid": str(uuid.uuid4()),
            "actuator": actuator,
            "new_state": state,
            "trigger": "threshold",
            "reason": reason,
            "device_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        }
