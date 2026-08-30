"""Tests for the hysteresis, dwell and fail-safe behaviour of the control law,
and for the hardware adapters' import-safety off a Raspberry Pi."""
from src.control_service import ControlService
from src.hardware.gas import DoutBackend, GasSensorError, Mq135, make_backend
from src.hardware.relays import NullRelayBank, get_relay_bank


class FakeClock:
    """Manually advanced monotonic clock, so dwell times need no sleeping."""

    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeBackend:
    analogue = True

    def __init__(self, voltage):
        self.voltage = voltage

    def read_voltage(self):
        return self.voltage

    def close(self):
        pass


# -- hysteresis -----------------------------------------------------------
def test_fan_does_not_chatter_inside_hysteresis_band():
    c = ControlService(temp_min_c=20, temp_max_c=30, hysteresis_c=2.0)
    assert c.evaluate({"temperature_c": 31})  # 31 > 30 -> on
    # 29.5 is below the turn-on threshold but inside the 2 degree band, so the
    # fan must hold rather than switch off.
    assert c.evaluate({"temperature_c": 29.5}) == []
    assert c.fan_state is True
    # Below the band it finally releases.
    events = c.evaluate({"temperature_c": 27.9})
    assert [e["new_state"] for e in events if e["actuator"] == "fan"] == [False]


# -- minimum dwell --------------------------------------------------------
def test_minimum_on_time_blocks_an_early_switch_off():
    clock = FakeClock()
    c = ControlService(temp_min_c=20, temp_max_c=30, hysteresis_c=0.0,
                       min_on_seconds=120, clock=clock)
    assert c.evaluate({"temperature_c": 35})  # first transition is never blocked
    clock.advance(30)
    assert c.evaluate({"temperature_c": 10}) == []  # still inside the on-window
    assert c.fan_state is True
    clock.advance(200)
    assert c.evaluate({"temperature_c": 10})  # window elapsed, now it may switch


# -- fail-safe ------------------------------------------------------------
def test_heater_forced_off_when_temperature_is_missing():
    c = ControlService(temp_min_c=20, temp_max_c=30)
    c.evaluate({"temperature_c": 5})
    assert c.heater_state is True
    # A dead DHT22 with a live gas sensor must not leave the lamp latched on.
    c.evaluate({"temperature_c": None, "gas_risk_value": 0.1})
    assert c.heater_state is False


def test_fan_and_heater_are_never_on_together():
    c = ControlService(temp_min_c=20, temp_max_c=30, gas_risk_fan_on=0.8)
    c.evaluate({"temperature_c": 5})
    assert c.heater_state is True
    # Cold but gassy: ventilation wins, heating is suppressed.
    c.evaluate({"temperature_c": 5, "gas_risk_value": 0.95})
    assert c.fan_state is True
    assert c.heater_state is False


def test_all_off_drives_both_channels_down():
    relays = NullRelayBank()
    c = ControlService(temp_min_c=20, temp_max_c=30, relays=relays)
    c.evaluate({"temperature_c": 35})
    assert relays.states()["fan_state"] is True
    c.all_off()
    assert relays.states() == {"fan_state": False, "heater_state": False}


# -- gas triggers ventilation --------------------------------------------
def test_gas_risk_alone_starts_the_fan():
    c = ControlService(temp_min_c=20, temp_max_c=30, gas_risk_fan_on=0.8)
    events = c.evaluate({"temperature_c": 25, "gas_risk_value": 0.9})
    assert [e["actuator"] for e in events] == ["fan"]
    assert "gas risk" in events[0]["reason"]


# -- adapters are import-safe and behave off-Pi ---------------------------
def test_relay_bank_is_null_in_mock_mode():
    bank = get_relay_bank(mock=True)
    assert isinstance(bank, NullRelayBank)
    bank.set("fan", True)
    assert bank.states()["fan_state"] is True


def test_unknown_gas_backend_names_the_valid_choices():
    try:
        make_backend("i2c-magic")
    except GasSensorError as exc:
        assert "ads1115" in str(exc) and "dout" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected GasSensorError")


def test_gas_risk_is_clamped_to_the_unit_interval():
    hot = Mq135(FakeBackend(voltage=9.0), baseline_v=0.4, span_v=1.6).read()
    clean = Mq135(FakeBackend(voltage=0.1), baseline_v=0.4, span_v=1.6).read()
    assert hot["gas_risk_value"] == 1.0
    assert clean["gas_risk_value"] == 0.0  # never negative


def test_dout_backend_is_declared_non_analogue():
    # The distinction drives sensor_status tagging and the calibration warning.
    assert DoutBackend(pin_bcm=22).analogue is False


def test_heater_cannot_start_while_the_fan_is_held_on_by_its_dwell_timer():
    """Regression: the interlock must test the fan's ACTUAL state, not the
    desired one, or a fan held on by min_on_seconds lets the heater energise."""
    clock = FakeClock()
    relays = NullRelayBank()
    c = ControlService(temp_min_c=20, temp_max_c=30, hysteresis_c=0.0,
                       min_on_seconds=600, relays=relays, clock=clock)
    c.evaluate({"temperature_c": 35})
    assert relays.states()["fan_state"] is True
    clock.advance(10)
    c.evaluate({"temperature_c": 5})  # cold enough to want heat, fan still latched
    assert relays.states() == {"fan_state": True, "heater_state": False}
