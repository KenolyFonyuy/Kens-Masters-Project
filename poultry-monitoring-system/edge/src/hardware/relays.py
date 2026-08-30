"""Opto-isolated relay driver for the ventilation fan and the heat lamp.

The blue relay boards used here are ACTIVE-LOW: pulling the IN pin low lights
the opto-coupler's LED and energises the coil. gpiozero's ``active_high=False``
expresses exactly that, so ``on()`` still means "actuator running" everywhere
in the code above this module.

Fail-safe: both channels are constructed de-energised and are driven back to
de-energised on close, on error, and on interpreter exit. The heat lamp is the
reason — a relay left latched on an unattended infrared lamp is a fire risk,
so "no control" must always mean "no heat", never "last known state".

Powering the board (see HARDWARE.md): remove the VCC-JD_VCC jumper, feed JD_VCC
from 5 V for the coils and VCC from 3.3 V for the logic side. With VCC at 5 V a
3.3 V GPIO never rises far enough above the opto's cathode to switch it fully
off, and the channel chatters or sticks on.
"""
from __future__ import annotations

import atexit


class RelayError(RuntimeError):
    """Raised when a relay channel cannot be opened or driven."""


class RelayChannel:
    """One relay output, held OFF unless explicitly switched on."""

    def __init__(self, pin_bcm, name, active_low=True):
        self.pin_bcm = pin_bcm
        self.name = name
        self.active_low = active_low
        self._device = None

    def _open(self):
        if self._device is not None:
            return self._device
        try:
            from gpiozero import DigitalOutputDevice  # lazy: Pi-only

            self._device = DigitalOutputDevice(
                self.pin_bcm,
                active_high=not self.active_low,
                initial_value=False,  # de-energised the instant the pin is claimed
            )
        except Exception as exc:  # noqa: BLE001
            raise RelayError(f"Cannot open relay '{self.name}' on BCM{self.pin_bcm}: {exc}") from exc
        return self._device

    @property
    def state(self):
        return bool(self._device.value) if self._device is not None else False

    def set(self, on):
        device = self._open()
        try:
            device.on() if on else device.off()
        except Exception as exc:  # noqa: BLE001
            raise RelayError(f"Cannot switch relay '{self.name}': {exc}") from exc
        return bool(on)

    def close(self):
        if self._device is not None:
            try:
                self._device.off()
            finally:
                self._device.close()
                self._device = None


class RelayBank:
    """The fan and heater channels, with a mutual-exclusion interlock.

    Heating and ventilating at once is always wrong — the fan exhausts the heat
    the lamp is paying for — so switching one on drops the other. This is a
    control interlock, not an electrical one; it does not remove the need for
    the fuse and breaker on the mains side.
    """

    def __init__(self, fan_pin=17, heater_pin=27, active_low=True, interlock=True):
        self.fan = RelayChannel(fan_pin, "fan", active_low)
        self.heater = RelayChannel(heater_pin, "heater", active_low)
        self.interlock = interlock
        atexit.register(self.all_off)

    def _channel(self, actuator):
        try:
            return {"fan": self.fan, "heater": self.heater}[actuator]
        except KeyError:
            raise RelayError(f"Unknown actuator '{actuator}'; expected 'fan' or 'heater'.") from None

    def set(self, actuator, on):
        channel = self._channel(actuator)
        if on and self.interlock:
            other = self.heater if actuator == "fan" else self.fan
            other.set(False)
        return channel.set(on)

    def states(self):
        return {"fan_state": self.fan.state, "heater_state": self.heater.state}

    def all_off(self):
        """Drive both channels de-energised; safe to call more than once."""
        for channel in (self.fan, self.heater):
            try:
                channel.set(False)
            except RelayError:
                pass

    def close(self):
        for channel in (self.fan, self.heater):
            channel.close()


class NullRelayBank:
    """Stand-in used in MOCK mode so control logic runs with no GPIO present."""

    def __init__(self):
        self._states = {"fan": False, "heater": False}

    def set(self, actuator, on):
        self._states[actuator] = bool(on)
        return bool(on)

    def states(self):
        return {"fan_state": self._states["fan"], "heater_state": self._states["heater"]}

    def all_off(self):
        self._states = {"fan": False, "heater": False}

    def close(self):
        self.all_off()


def get_relay_bank(mock=True, fan_pin=17, heater_pin=27, active_low=True, interlock=True):
    if mock:
        return NullRelayBank()
    return RelayBank(fan_pin, heater_pin, active_low, interlock)
