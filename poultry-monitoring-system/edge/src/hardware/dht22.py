"""DHT22 (AM2302) temperature/humidity driver.

The DHT22 is a bit-banged one-wire part with no clock line, so a read fails
whenever Linux preempts the driver mid-frame. A single failed read is normal
and is NOT a sensor fault; only a run of consecutive failures is. The sensor
also refuses to be polled faster than about once every 2 s.

Wiring (see HARDWARE.md): VCC -> 3.3 V, DATA -> BCM4, GND -> GND.
Power it from 3.3 V, never 5 V: the data line idles at the supply rail and a
5 V line on a GPIO pin damages the Pi.
"""
from __future__ import annotations

import time

# Physically impossible readings are rejected rather than transmitted; the
# DHT22 emits these when a frame is corrupted but the checksum coincidentally
# passes. Ranges are the datasheet limits, widened slightly.
TEMP_MIN_C, TEMP_MAX_C = -40.0, 80.0
HUMIDITY_MIN_PCT, HUMIDITY_MAX_PCT = 0.0, 100.0


class Dht22Error(RuntimeError):
    """Raised when the sensor could not be read after every retry."""


class Dht22:
    def __init__(self, pin_bcm=4, retries=5, retry_delay=2.1):
        self.pin_bcm = pin_bcm
        self.retries = retries
        self.retry_delay = retry_delay
        self._device = None

    def _open(self):
        if self._device is not None:
            return self._device
        import adafruit_dht  # lazy: Pi-only
        import board

        try:
            pin = getattr(board, f"D{self.pin_bcm}")
        except AttributeError as exc:  # pragma: no cover - wiring error
            raise Dht22Error(f"BCM{self.pin_bcm} is not a valid data pin") from exc
        # use_pulseio=False selects the bit-bang backend, which is the one that
        # works on current Raspberry Pi OS (the pulseio backend needs a DMA
        # channel that Pi 4/5 kernels no longer expose to userspace).
        self._device = adafruit_dht.DHT22(pin, use_pulseio=False)
        return self._device

    def read(self):
        """Return (temperature_c, humidity_pct) or raise Dht22Error."""
        device = self._open()
        last = None
        for attempt in range(self.retries):
            try:
                temperature = device.temperature
                humidity = device.humidity
                if temperature is None or humidity is None:
                    raise RuntimeError("sensor returned no value")
                if not TEMP_MIN_C <= temperature <= TEMP_MAX_C:
                    raise RuntimeError(f"temperature {temperature} out of range")
                if not HUMIDITY_MIN_PCT <= humidity <= HUMIDITY_MAX_PCT:
                    raise RuntimeError(f"humidity {humidity} out of range")
                return round(float(temperature), 1), round(float(humidity), 1)
            except Exception as exc:  # noqa: BLE001 - retry any read failure
                last = exc
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay)
        raise Dht22Error(f"DHT22 on BCM{self.pin_bcm} failed after {self.retries} tries: {last}")

    def close(self):
        if self._device is not None:
            try:
                self._device.exit()
            except Exception:  # noqa: BLE001
                pass
            self._device = None
