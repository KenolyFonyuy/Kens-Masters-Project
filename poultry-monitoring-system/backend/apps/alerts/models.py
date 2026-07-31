"""Alerting: Alert, AlertAction (audit of state changes), NotificationPreference."""
from apps.core.models import TimeStampedModel, UUIDModel
from django.conf import settings
from django.db import models
from django.utils import timezone


class AlertType(models.TextChoices):
    HIGH_TEMP = "high_temp", "High temperature"
    LOW_TEMP = "low_temp", "Low temperature"
    HIGH_HUMIDITY = "high_humidity", "High humidity"
    LOW_HUMIDITY = "low_humidity", "Low humidity"
    HIGH_GAS = "high_gas", "High gas risk"
    SENSOR_FAILURE = "sensor_failure", "Sensor failure"
    CAMERA_FAILURE = "camera_failure", "Camera failure"
    DEVICE_OFFLINE = "device_offline", "Device offline"
    VISIBLE_DISTRESS = "visible_distress", "Possible visible distress"
    LETHARGY = "lethargy", "Lethargy"
    OPEN_BEAK = "open_beak_stress", "Open-beak stress"
    DISEASED_EYE = "diseased_eye", "Diseased eye"
    MOBILITY = "mobility_abnormality", "Mobility abnormality"
    PHYSICAL_ABNORMALITY = "physical_abnormality", "Visible physical abnormality"
    HUDDLING = "huddling", "Huddling"
    UNUSUAL_MORTALITY = "unusual_mortality", "Unusual mortality"
    LOW_STOCK = "low_stock", "Low stock"
    MISSED_VACCINATION = "missed_vaccination", "Missed vaccination"
    SYNC_FAILURE = "sync_failure", "Synchronisation failure"


class Severity(models.TextChoices):
    INFO = "info", "Information"
    WARNING = "warning", "Warning"
    CRITICAL = "critical", "Critical"


class Alert(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        INVESTIGATING = "investigating", "Under investigation"
        RESOLVED = "resolved", "Resolved"
        FALSE = "false", "False alert"
        ESCALATED = "escalated", "Escalated"

    class Source(models.TextChoices):
        SENSOR = "sensor", "Sensor"
        VISION = "vision", "Vision"
        SYSTEM = "system", "System"
        MANUAL = "manual", "Manual"

    alert_type = models.CharField(max_length=40, choices=AlertType.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, db_index=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.SYSTEM)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW, db_index=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)

    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="alerts")
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts"
    )
    device = models.ForeignKey(
        "iot.IoTDevice", on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts"
    )
    sensor_reading = models.ForeignKey(
        "iot.SensorReading", on_delete=models.SET_NULL, null=True, blank=True
    )
    vision_result = models.ForeignKey(
        "vision.VisionResult", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="alerts",
    )

    # Cooldown / dedup key: identical unchanged conditions share this key.
    dedup_key = models.CharField(max_length=200, blank=True, db_index=True)
    last_triggered_at = models.DateTimeField(default=timezone.now, db_index=True)
    trigger_count = models.PositiveIntegerField(default=1)

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="acknowledged_alerts",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="resolved_alerts",
    )
    corrective_action = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-last_triggered_at"]
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["farm", "status"]),
            models.Index(fields=["alert_type", "status"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title}"

    @property
    def is_open(self):
        return self.status in {self.Status.NEW, self.Status.ACKNOWLEDGED, self.Status.INVESTIGATING, self.Status.ESCALATED}


class AlertAction(TimeStampedModel):
    """Immutable log of each action taken on an alert."""

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="actions")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.alert_id}: {self.from_status}->{self.to_status}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    email_critical = models.BooleanField(default=True)
    email_warning = models.BooleanField(default=False)
    in_app = models.BooleanField(default=True)
    min_severity = models.CharField(
        max_length=10, choices=Severity.choices, default=Severity.WARNING
    )

    def __str__(self):
        return f"Notification prefs for {self.user}"
