"""Real hardware drivers for the Raspberry Pi edge unit.

Every module here is import-safe on a laptop: the Pi-only libraries
(gpiozero, adafruit_dht, board) are imported lazily inside the constructors,
so the test suite and MOCK mode never need them installed.
"""
from __future__ import annotations

__all__ = ["dht22", "gas", "relays"]
