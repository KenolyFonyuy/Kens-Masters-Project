"""IoT processing: reading validation, gas-risk categorisation, alerting."""
import logging

from apps.alerts.models import Alert, AlertType, Severity
from apps.alerts.services import raise_alert
from django.utils import timezone

from .models import EnvironmentalThreshold, SensorReading

logger = logging.getLogger("apps.iot")

# Plausibility bounds for input validation (not calibration).
TEMP_RANGE = (-20.0, 70.0)
HUMIDITY_RANGE = (0.0, 100.0)


def validate_reading_values(temperature_c, humidity_pct):
    """Return (quality, reason) — flags impossible values for debugging."""
    reasons = []
    if temperature_c is not None and not (TEMP_RANGE[0] <= temperature_c <= TEMP_RANGE[1]):
        reasons.append(f"temperature {temperature_c} out of range {TEMP_RANGE}")
    if humidity_pct is not None and not (HUMIDITY_RANGE[0] <= humidity_pct <= HUMIDITY_RANGE[1]):
        reasons.append(f"humidity {humidity_pct} out of range {HUMIDITY_RANGE}")
    if reasons:
        return SensorReading.Quality.REJECTED, "; ".join(reasons)
    return SensorReading.Quality.GOOD, ""


def categorise_gas_risk(gas_risk_value, threshold: EnvironmentalThreshold | None):
    """Map a relative gas-risk value (0-1) to a category using thresholds."""
    if gas_risk_value is None:
        return ""
    warn = threshold.gas_risk_warning if threshold else 0.5
    crit = threshold.gas_risk_critical if threshold else 0.8
    if gas_risk_value >= crit:
        return SensorReading.GasRisk.CRITICAL
    if gas_risk_value >= warn:
        return SensorReading.GasRisk.HIGH
    if gas_risk_value >= warn * 0.6:
        return SensorReading.GasRisk.MODERATE
    return SensorReading.GasRisk.LOW


def get_threshold(farm, pen):
    """Resolve the most specific threshold: pen-level, else farm-wide."""
    if pen is not None:
        t = EnvironmentalThreshold.objects.filter(farm=farm, pen=pen).first()
        if t:
            return t
    return EnvironmentalThreshold.objects.filter(farm=farm, pen__isnull=True).first()


def process_sensor_reading(reading: SensorReading):
    """Post-save processing: categorise gas risk and evaluate alert thresholds.

    Returns the list of alerts raised/bumped.
    """
    threshold = get_threshold(reading.farm, reading.pen)

    if reading.gas_risk_category == "" and reading.gas_risk_value is not None:
        reading.gas_risk_category = categorise_gas_risk(reading.gas_risk_value, threshold)
        reading.save(update_fields=["gas_risk_category"])

    if reading.quality == SensorReading.Quality.REJECTED:
        return []

    raised = []
    common = dict(
        farm=reading.farm, pen=reading.pen, batch=reading.batch,
        device=reading.device, sensor_reading=reading, source=Alert.Source.SENSOR,
    )

    t = threshold
    temp = reading.temperature_c
    hum = reading.humidity_pct
    gas = reading.gas_risk_value

    if t and temp is not None:
        if temp > t.temp_max_c:
            raised.append(raise_alert(
                alert_type=AlertType.HIGH_TEMP, severity=Severity.CRITICAL,
                title=f"High temperature {temp:.1f}°C", message=f"Above max {t.temp_max_c}°C",
                **common)[0])
        elif temp < t.temp_min_c:
            raised.append(raise_alert(
                alert_type=AlertType.LOW_TEMP, severity=Severity.WARNING,
                title=f"Low temperature {temp:.1f}°C", message=f"Below min {t.temp_min_c}°C",
                **common)[0])

    if t and hum is not None:
        if hum > t.humidity_max_pct:
            raised.append(raise_alert(
                alert_type=AlertType.HIGH_HUMIDITY, severity=Severity.WARNING,
                title=f"High humidity {hum:.0f}%", message=f"Above max {t.humidity_max_pct}%",
                **common)[0])
        elif hum < t.humidity_min_pct:
            raised.append(raise_alert(
                alert_type=AlertType.LOW_HUMIDITY, severity=Severity.WARNING,
                title=f"Low humidity {hum:.0f}%", message=f"Below min {t.humidity_min_pct}%",
                **common)[0])

    if gas is not None and reading.gas_risk_category in {
        SensorReading.GasRisk.HIGH, SensorReading.GasRisk.CRITICAL
    }:
        sev = Severity.CRITICAL if reading.gas_risk_category == SensorReading.GasRisk.CRITICAL else Severity.WARNING
        raised.append(raise_alert(
            alert_type=AlertType.HIGH_GAS, severity=sev,
            title=f"High gas risk ({reading.get_gas_risk_category_display()})",
            message="Elevated ammonia-risk indicator. Improve ventilation.",
            **common)[0])

    if reading.sensor_status and reading.sensor_status.lower() not in {"ok", "good", ""}:
        raised.append(raise_alert(
            alert_type=AlertType.SENSOR_FAILURE, severity=Severity.WARNING,
            title=f"Sensor status: {reading.sensor_status}",
            message="Device reported an abnormal sensor status.", **common)[0])

    return raised


def touch_device_seen(device):
    device.last_seen_at = timezone.now()
    device.save(update_fields=["last_seen_at"])
