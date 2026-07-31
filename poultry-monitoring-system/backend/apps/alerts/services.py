"""Alert creation/dedup/cooldown and visibility helpers."""
from datetime import timedelta

from apps.audit.models import AuditLog
from apps.audit.services import log_action
from django.conf import settings
from django.utils import timezone

from .models import Alert, AlertAction


def _cooldown_active(alert) -> bool:
    minutes = settings.ALERT_COOLDOWN_MINUTES
    return (timezone.now() - alert.last_triggered_at) < timedelta(minutes=minutes)


def raise_alert(
    *,
    alert_type,
    severity,
    title,
    farm,
    source=Alert.Source.SYSTEM,
    message="",
    pen=None,
    batch=None,
    device=None,
    sensor_reading=None,
    vision_result=None,
    dedup_key=None,
):
    """Create an alert, or bump an existing open one within its cooldown window.

    Duplicate suppression: if an *open* alert with the same ``dedup_key`` exists
    and is still inside the cooldown window, increment its trigger count rather
    than spamming a new alert. Returns ``(alert, created)``.
    """
    dedup_key = dedup_key or f"{alert_type}:{getattr(pen, 'pk', None) or farm.pk}"

    existing = (
        Alert.objects.filter(
            dedup_key=dedup_key,
            status__in=[
                Alert.Status.NEW,
                Alert.Status.ACKNOWLEDGED,
                Alert.Status.INVESTIGATING,
                Alert.Status.ESCALATED,
            ],
        )
        .order_by("-last_triggered_at")
        .first()
    )

    if existing and _cooldown_active(existing):
        existing.trigger_count += 1
        existing.last_triggered_at = timezone.now()
        existing.save(update_fields=["trigger_count", "last_triggered_at"])
        return existing, False

    alert = Alert.objects.create(
        alert_type=alert_type,
        severity=severity,
        source=source,
        title=title,
        message=message,
        farm=farm,
        pen=pen,
        batch=batch,
        device=device,
        sensor_reading=sensor_reading,
        vision_result=vision_result,
        dedup_key=dedup_key,
    )
    log_action(AuditLog.Action.ALERT, target=alert, message=f"Alert raised: {title}")
    return alert, True


def transition(alert, *, to_status, actor=None, note=""):
    """Move an alert to a new status, recording who/when and an AlertAction."""
    from_status = alert.status
    now = timezone.now()
    alert.status = to_status
    if to_status == Alert.Status.ACKNOWLEDGED and not alert.acknowledged_at:
        alert.acknowledged_at = now
        alert.acknowledged_by = actor
    if to_status in {Alert.Status.RESOLVED, Alert.Status.FALSE}:
        alert.resolved_at = now
        alert.resolved_by = actor
        if note:
            alert.resolution_notes = note
    alert.save()
    AlertAction.objects.create(
        alert=alert, actor=actor, from_status=from_status, to_status=to_status, note=note
    )
    log_action(
        AuditLog.Action.ALERT, target=alert,
        message=f"Alert {from_status}->{to_status}", user=actor,
    )
    return alert


def alerts_visible_to(user):
    """Alerts within the farms a user can access."""
    from apps.alerts.models import Alert
    from apps.farms.services import farms_for_user

    if user.is_superuser or user.has_role("ADMIN"):
        return Alert.objects.all()
    return Alert.objects.filter(farm__in=farms_for_user(user))
