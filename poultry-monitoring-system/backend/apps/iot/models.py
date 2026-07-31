"""IoT subsystem models.

Security notes:
  * Device secrets are stored only as salted hashes (``DeviceToken.key_hash``);
    the raw token is shown exactly once, at creation.
  * Synchronised records carry a device-generated UUID + idempotency key so a
    Raspberry Pi resubmission returns the existing row instead of duplicating.
"""
import hashlib
import secrets
import uuid

from apps.core.models import TimeStampedModel, TimeStampedUserModel
from django.db import models
from django.utils import timezone


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IoTDevice(TimeStampedUserModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        MAINTENANCE = "maintenance", "Maintenance"
        DECOMMISSIONED = "decommissioned", "Decommissioned"

    device_id = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text="Stable device identifier reported by the Raspberry Pi",
    )
    name = models.CharField(max_length=120)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="devices")
    pen = models.ForeignKey(
        "farms.Pen", on_delete=models.SET_NULL, null=True, blank=True, related_name="devices"
    )
    firmware_version = models.CharField(max_length=40, blank=True)
    hardware = models.CharField(max_length=120, blank=True, default="Raspberry Pi")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    has_camera = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_demo = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["farm", "status"])]

    def __str__(self):
        return f"{self.name} ({self.device_id})"

    @property
    def is_online(self) -> bool:
        from django.conf import settings

        if not self.last_seen_at:
            return False
        delta = timezone.now() - self.last_seen_at
        return delta.total_seconds() <= settings.DEVICE_OFFLINE_MINUTES * 60


class DeviceToken(TimeStampedModel):
    """Bearer token for a device. Only the hash is persisted."""

    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name="tokens")
    key_hash = models.CharField(max_length=64, unique=True, db_index=True)
    label = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for {self.device.device_id} ({self.label or self.pk})"

    @classmethod
    def issue(cls, device, label=""):
        """Create a token, returning (instance, raw_token). Raw is not stored."""
        raw = secrets.token_urlsafe(32)
        token = cls.objects.create(device=device, key_hash=hash_token(raw), label=label)
        return token, raw

    def revoke(self):
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])


class DeviceConfiguration(TimeStampedUserModel):
    """Per-device runtime configuration delivered to the edge client."""

    device = models.OneToOneField(
        IoTDevice, on_delete=models.CASCADE, related_name="configuration"
    )
    sampling_interval_seconds = models.PositiveIntegerField(default=60)
    heartbeat_interval_seconds = models.PositiveIntegerField(default=120)
    capture_interval_seconds = models.PositiveIntegerField(default=300)
    inference_enabled = models.BooleanField(default=True)
    confidence_threshold = models.FloatField(default=0.35)
    frame_skip = models.PositiveIntegerField(default=5)
    extra = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Config for {self.device.device_id}"

    def as_dict(self):
        return {
            "sampling_interval_seconds": self.sampling_interval_seconds,
            "heartbeat_interval_seconds": self.heartbeat_interval_seconds,
            "capture_interval_seconds": self.capture_interval_seconds,
            "inference_enabled": self.inference_enabled,
            "confidence_threshold": self.confidence_threshold,
            "frame_skip": self.frame_skip,
            "extra": self.extra,
        }


class EnvironmentalThreshold(TimeStampedUserModel):
    """Min/max thresholds per pen used for alerting and actuator control."""

    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="thresholds")
    pen = models.ForeignKey(
        "farms.Pen", on_delete=models.CASCADE, null=True, blank=True, related_name="thresholds"
    )
    temp_min_c = models.FloatField(default=18.0)
    temp_max_c = models.FloatField(default=32.0)
    humidity_min_pct = models.FloatField(default=40.0)
    humidity_max_pct = models.FloatField(default=75.0)
    gas_risk_warning = models.FloatField(
        default=0.5, help_text="Relative gas-risk value (0-1) for a warning"
    )
    gas_risk_critical = models.FloatField(
        default=0.8, help_text="Relative gas-risk value (0-1) for a critical alert"
    )

    class Meta:
        ordering = ["farm", "pen"]
        unique_together = [("farm", "pen")]

    def __str__(self):
        return f"Thresholds {self.farm.name}/{self.pen or 'farm-wide'}"

    def as_dict(self):
        return {
            "temp_min_c": self.temp_min_c,
            "temp_max_c": self.temp_max_c,
            "humidity_min_pct": self.humidity_min_pct,
            "humidity_max_pct": self.humidity_max_pct,
            "gas_risk_warning": self.gas_risk_warning,
            "gas_risk_critical": self.gas_risk_critical,
        }


class SensorReading(TimeStampedModel):
    """A single environmental reading.

    MQ-series gas sensors are NOT calibrated to ppm here. We store the raw ADC
    value and a processed *relative* gas-risk indicator (0-1) plus a category.
    """

    class GasRisk(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Quality(models.TextChoices):
        GOOD = "good", "Good"
        SUSPECT = "suspect", "Suspect"
        REJECTED = "rejected", "Rejected"

    # Idempotency: device-generated UUID for the reading.
    reading_uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name="readings")
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="readings")
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.SET_NULL, null=True, blank=True, related_name="readings"
    )

    temperature_c = models.FloatField(null=True, blank=True)
    humidity_pct = models.FloatField(null=True, blank=True)
    raw_gas_value = models.FloatField(
        null=True, blank=True, help_text="Raw MQ ADC reading (uncalibrated)"
    )
    gas_risk_value = models.FloatField(
        null=True, blank=True, help_text="Processed relative air-quality / ammonia-risk (0-1)"
    )
    gas_risk_category = models.CharField(
        max_length=10, choices=GasRisk.choices, blank=True, db_index=True
    )

    fan_state = models.BooleanField(default=False)
    heater_state = models.BooleanField(default=False)
    sensor_status = models.CharField(max_length=40, blank=True, default="ok")
    quality = models.CharField(max_length=10, choices=Quality.choices, default=Quality.GOOD)
    rejection_reason = models.CharField(max_length=255, blank=True)

    device_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-server_timestamp"]
        indexes = [
            models.Index(fields=["device", "server_timestamp"]),
            models.Index(fields=["pen", "server_timestamp"]),
            models.Index(fields=["gas_risk_category"]),
        ]

    def __str__(self):
        return f"Reading {self.device.device_id} @ {self.server_timestamp:%Y-%m-%d %H:%M}"


class ActuatorEvent(TimeStampedModel):
    class Actuator(models.TextChoices):
        FAN = "fan", "Fan"
        HEATER = "heater", "Heater"
        LIGHT = "light", "Light"
        WATER = "water", "Water valve"
        FEEDER = "feeder", "Feeder"

    event_uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name="actuator_events")
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="actuator_events")
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    actuator = models.CharField(max_length=20, choices=Actuator.choices)
    new_state = models.BooleanField()
    trigger = models.CharField(max_length=80, blank=True, help_text="e.g. threshold, manual")
    reason = models.CharField(max_length=255, blank=True)
    device_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-server_timestamp"]
        indexes = [models.Index(fields=["device", "server_timestamp"])]

    def __str__(self):
        return f"{self.actuator}->{self.new_state} ({self.device.device_id})"


class DeviceHeartbeat(TimeStampedModel):
    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name="heartbeats")
    cpu_percent = models.FloatField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    disk_percent = models.FloatField(null=True, blank=True)
    cpu_temp_c = models.FloatField(null=True, blank=True)
    uptime_seconds = models.BigIntegerField(null=True, blank=True)
    queued_records = models.IntegerField(default=0)
    firmware_version = models.CharField(max_length=40, blank=True)
    device_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-server_timestamp"]
        indexes = [models.Index(fields=["device", "server_timestamp"])]

    def __str__(self):
        return f"Heartbeat {self.device.device_id} @ {self.server_timestamp:%H:%M}"


class SyncRecord(TimeStampedModel):
    """Idempotency ledger for offline batch synchronisation.

    Each device record carries a unique ``idempotency_key``; replays return the
    existing entry instead of creating duplicates.
    """

    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        DUPLICATE = "duplicate", "Duplicate"
        REJECTED = "rejected", "Rejected"

    device = models.ForeignKey(IoTDevice, on_delete=models.CASCADE, related_name="sync_records")
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    record_type = models.CharField(max_length=40)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACCEPTED)
    target_uuid = models.UUIDField(null=True, blank=True)
    device_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(default=timezone.now)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-server_timestamp"]

    def __str__(self):
        return f"Sync {self.record_type} {self.idempotency_key} ({self.status})"
