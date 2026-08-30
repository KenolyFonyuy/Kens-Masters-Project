"""MQ135 metal-oxide gas sensor: three interchangeable read backends.

The Raspberry Pi has no analogue input, so the MQ135's analogue output (AOUT)
must go through an external ADC. Which ADC you own decides the backend:

    ads1115   MQ135 AOUT -> voltage divider -> ADS1115 A0 -> I2C   (preferred)
    mcp3008   MQ135 AOUT -> voltage divider -> MCP3008 CH0 -> SPI
    dout      MQ135 DOUT -> voltage divider -> BCM22               (no ADC)

The ``dout`` backend exists so bring-up can proceed before an ADC arrives. It
reads the board's on-board LM393 comparator, whose trip point is set by the
blue potentiometer, so it yields a threshold crossing rather than a magnitude:
gas_risk_value can only ever be 0.0 or 1.0. That is enough to prove the wiring
and the alert path, but it cannot produce the calibration curve the study
needs. Swap in an ADC before taking measurements for the results chapter.

In every backend the output is a RELATIVE risk indicator in [0, 1], never a
ppm figure. The MQ135 is cross-sensitive to alcohols, CO2, smoke and solvents,
and its baseline drifts with temperature, humidity and age; the value is only
meaningful against a baseline captured in clean air on the same device
(see tools/mq135_baseline.py).
"""
from __future__ import annotations

# The MQ135 heater runs from 5 V, so AOUT and DOUT both swing to ~5 V. A
# 10k/10k divider halves that to a Pi/ADC-safe 2.5 V; readings are scaled back
# up by this factor so the reported voltage is the sensor's actual output.
DEFAULT_DIVIDER_RATIO = 2.0

# Warm-up before a metal-oxide element settles. The datasheet asks for 24 h of
# burn-in on a new sensor; 3 min is the per-power-cycle minimum after that.
DEFAULT_WARMUP_SECONDS = 180


class GasSensorError(RuntimeError):
    """Raised when the gas sensor or its ADC cannot be read."""


class BaseGasBackend:
    #: True when the backend reports a magnitude, False for a bare trip point.
    analogue = True

    def read_voltage(self) -> float:
        raise NotImplementedError

    def close(self):
        pass


class Ads1115Backend(BaseGasBackend):
    """ADS1115 16-bit ADC over I2C (address 0x48 with ADDR tied to GND)."""

    def __init__(self, channel=0, address=0x48, divider_ratio=DEFAULT_DIVIDER_RATIO):
        self.channel = channel
        self.address = address
        self.divider_ratio = divider_ratio
        self._chan = None

    def _open(self):
        if self._chan is not None:
            return self._chan
        import adafruit_ads1x15.ads1115 as ads  # lazy: Pi-only
        import board
        import busio
        from adafruit_ads1x15.analog_in import AnalogIn

        i2c = busio.I2C(board.SCL, board.SDA)
        adc = ads.ADS1115(i2c, address=self.address)
        # Gain 1 gives a +/-4.096 V full scale, comfortably above the 2.5 V the
        # divider can present while keeping most of the converter's resolution.
        adc.gain = 1
        pins = [ads.P0, ads.P1, ads.P2, ads.P3]
        self._chan = AnalogIn(adc, pins[self.channel])
        return self._chan

    def read_voltage(self):
        try:
            return self._open().voltage * self.divider_ratio
        except Exception as exc:  # noqa: BLE001
            raise GasSensorError(f"ADS1115 read failed: {exc}") from exc


class Mcp3008Backend(BaseGasBackend):
    """MCP3008 10-bit ADC over SPI0, referenced to the Pi's 3.3 V rail."""

    def __init__(self, channel=0, vref=3.3, divider_ratio=DEFAULT_DIVIDER_RATIO):
        self.channel = channel
        self.vref = vref
        self.divider_ratio = divider_ratio
        self._adc = None

    def _open(self):
        if self._adc is None:
            from gpiozero import MCP3008  # lazy: Pi-only

            self._adc = MCP3008(channel=self.channel)
        return self._adc

    def read_voltage(self):
        try:
            # gpiozero reports 0.0-1.0 as a fraction of VREF.
            return self._open().value * self.vref * self.divider_ratio
        except Exception as exc:  # noqa: BLE001
            raise GasSensorError(f"MCP3008 read failed: {exc}") from exc

    def close(self):
        if self._adc is not None:
            self._adc.close()
            self._adc = None


class DoutBackend(BaseGasBackend):
    """MQ135 DOUT comparator on a GPIO pin: a trip point, not a magnitude.

    The LM393 output is active-low — it goes LOW once gas exceeds the level set
    by the on-board potentiometer — so a LOW pin means "over threshold".
    """

    analogue = False

    def __init__(self, pin_bcm=22, active_low=True):
        self.pin_bcm = pin_bcm
        self.active_low = active_low
        self._pin = None

    def _open(self):
        if self._pin is None:
            from gpiozero import DigitalInputDevice  # lazy: Pi-only

            self._pin = DigitalInputDevice(self.pin_bcm, pull_up=None, active_state=True)
        return self._pin

    def read_tripped(self):
        try:
            high = bool(self._open().value)
        except Exception as exc:  # noqa: BLE001
            raise GasSensorError(f"MQ135 DOUT read failed: {exc}") from exc
        return (not high) if self.active_low else high

    def read_voltage(self):
        # Reported so the payload keeps one shape across backends; these are the
        # comparator's rails, not a measurement of the sensing element.
        return 0.0 if self.read_tripped() else 5.0

    def close(self):
        if self._pin is not None:
            self._pin.close()
            self._pin = None


def make_backend(kind, **kwargs):
    backends = {"ads1115": Ads1115Backend, "mcp3008": Mcp3008Backend, "dout": DoutBackend}
    try:
        return backends[kind](**kwargs)
    except KeyError:
        raise GasSensorError(
            f"Unknown gas backend '{kind}'. Choose one of: {', '.join(sorted(backends))}."
        ) from None


class Mq135:
    """MQ135 read as a relative risk indicator against a clean-air baseline.

    ``baseline_v`` is the AOUT voltage recorded in clean air on this device and
    ``span_v`` the rise above it that should read as full risk (1.0). Both come
    from tools/mq135_baseline.py and belong in the device's env file — they are
    per-sensor and must not be shared between units.
    """

    def __init__(self, backend, baseline_v=0.4, span_v=1.6):
        self.backend = backend
        self.baseline_v = baseline_v
        # A zero or negative span would divide by zero on the first read.
        self.span_v = span_v if span_v > 0 else 1.0

    def read(self):
        """Return {"raw_gas_value": volts, "gas_risk_value": 0.0-1.0}."""
        voltage = self.backend.read_voltage()
        if self.backend.analogue:
            risk = (voltage - self.baseline_v) / self.span_v
            risk = min(max(risk, 0.0), 1.0)
        else:
            # Comparator backend: tripped or not, nothing in between.
            risk = 1.0 if self.backend.read_tripped() else 0.0
        return {"raw_gas_value": round(voltage, 4), "gas_risk_value": round(risk, 3)}

    def close(self):
        self.backend.close()
