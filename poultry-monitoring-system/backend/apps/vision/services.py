"""Apply class mapping to a VisionResult and raise visual-health alerts."""
import logging

from apps.alerts.models import Alert, AlertType, Severity

from .class_mapping import map_class

logger = logging.getLogger("apps.vision")

_SEVERITY_MAP = {
    "information": Severity.INFO,
    "info": Severity.INFO,
    "warning": Severity.WARNING,
    "critical": Severity.CRITICAL,
}

# Map the YAML alert_type strings to AlertType enum values.
_ALERT_TYPE_MAP = {
    "lethargy": AlertType.LETHARGY,
    "open_beak_stress": AlertType.OPEN_BEAK,
    "diseased_eye": AlertType.DISEASED_EYE,
    "mobility_abnormality": AlertType.MOBILITY,
    "physical_abnormality": AlertType.PHYSICAL_ABNORMALITY,
    "huddling": AlertType.HUDDLING,
    "visible_distress": AlertType.VISIBLE_DISTRESS,
}


def annotate_result(result):
    """Populate ``risk_category``/``severity`` from the class mapping."""
    entry = map_class(result.predicted_class)
    result.risk_category = entry.get("risk_category", "")
    sev = entry.get("severity", "warning")
    result.severity = _SEVERITY_MAP.get(sev, Severity.WARNING)
    return result


def process_vision_result(result, *, min_confidence=0.35):
    """After saving a VisionResult, raise an alert if the class warrants it.

    Returns the alert if one was raised/bumped, else None.
    """
    from apps.alerts.services import raise_alert

    annotate_result(result)
    result.save(update_fields=["risk_category", "severity"])

    entry = map_class(result.predicted_class)
    alert_type_key = entry.get("alert_type")
    if not alert_type_key or result.predicted_class == "healthy":
        return None
    if result.confidence < min_confidence:
        return None

    alert_type = _ALERT_TYPE_MAP.get(alert_type_key, AlertType.VISIBLE_DISTRESS)
    severity = _SEVERITY_MAP.get(entry.get("severity", "warning"), Severity.WARNING)

    alert, _ = raise_alert(
        alert_type=alert_type,
        severity=severity,
        source=Alert.Source.VISION,
        title=f"Visual indicator: {result.predicted_class} ({result.confidence:.0%})",
        message=(
            "Machine-vision early-warning indicator. This is NOT a veterinary "
            "diagnosis — review the image and confirm before acting."
        ),
        farm=result.farm,
        pen=result.pen,
        batch=result.batch,
        device=result.device,
        vision_result=result,
        dedup_key=f"vision:{result.predicted_class}:{getattr(result.pen, 'pk', None) or result.farm.pk}",
    )
    return alert
