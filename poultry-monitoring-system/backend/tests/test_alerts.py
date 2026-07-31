"""Alert generation, dedup/cooldown and state transitions."""
import pytest
from apps.alerts.models import Alert, AlertType, Severity
from apps.alerts.services import raise_alert, transition

pytestmark = pytest.mark.django_db


def test_raise_alert_creates(farm):
    alert, created = raise_alert(
        alert_type=AlertType.HIGH_TEMP, severity=Severity.CRITICAL,
        title="Hot", farm=farm,
    )
    assert created is True
    assert alert.status == Alert.Status.NEW


def test_duplicate_within_cooldown_bumps_count(farm):
    a1, c1 = raise_alert(alert_type=AlertType.HIGH_TEMP, severity=Severity.WARNING,
                         title="Hot", farm=farm, dedup_key="k1")
    a2, c2 = raise_alert(alert_type=AlertType.HIGH_TEMP, severity=Severity.WARNING,
                         title="Hot", farm=farm, dedup_key="k1")
    assert c1 is True and c2 is False
    assert a1.pk == a2.pk
    a1.refresh_from_db()
    assert a1.trigger_count == 2


def test_resolved_alert_allows_new_one(farm):
    a1, _ = raise_alert(alert_type=AlertType.HIGH_GAS, severity=Severity.WARNING,
                        title="Gas", farm=farm, dedup_key="g1")
    transition(a1, to_status=Alert.Status.RESOLVED)
    a2, created = raise_alert(alert_type=AlertType.HIGH_GAS, severity=Severity.WARNING,
                             title="Gas", farm=farm, dedup_key="g1")
    assert created is True
    assert a2.pk != a1.pk


def test_acknowledge_records_user_and_time(farm, manager):
    alert, _ = raise_alert(alert_type=AlertType.LOW_TEMP, severity=Severity.WARNING,
                           title="Cold", farm=farm)
    transition(alert, to_status=Alert.Status.ACKNOWLEDGED, actor=manager)
    alert.refresh_from_db()
    assert alert.acknowledged_by == manager
    assert alert.acknowledged_at is not None
    assert alert.actions.count() == 1


def test_resolution_records_user_and_time(farm, manager):
    alert, _ = raise_alert(alert_type=AlertType.LOW_TEMP, severity=Severity.WARNING,
                           title="Cold", farm=farm)
    transition(alert, to_status=Alert.Status.RESOLVED, actor=manager, note="Fixed heater")
    alert.refresh_from_db()
    assert alert.resolved_by == manager
    assert alert.resolved_at is not None
    assert alert.resolution_notes == "Fixed heater"
