"""Computer-vision results and human review.

A ``VisionResult`` stores the *original, immutable* machine output (detections,
classes, confidences, bounding boxes). Human review is layered on top via
separate fields so the original prediction is never overwritten.

Predictions are early-warning indicators and do NOT replace veterinary
diagnosis — surfaced in the UI and serializers.
"""
import uuid

from apps.core.models import TimeStampedModel
from django.conf import settings
from django.db import models
from django.utils import timezone


class VisionResult(TimeStampedModel):
    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        ACCEPTED = "accepted", "Accepted"
        CORRECTED = "corrected", "Corrected"
        UNCERTAIN = "uncertain", "Marked uncertain"
        FALSE = "false", "False alert"
        ESCALATED = "escalated", "Escalated"

    # Idempotency key from the device.
    result_uuid = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)

    device = models.ForeignKey(
        "iot.IoTDevice", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vision_results",
    )
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="vision_results")
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vision_results",
    )

    model_name = models.CharField(max_length=80, default="yolo11n")
    model_version = models.CharField(max_length=60, blank=True)

    # Original machine output (immutable).
    predicted_class = models.CharField(max_length=60, db_index=True)
    confidence = models.FloatField(default=0.0)
    risk_category = models.CharField(max_length=60, blank=True, db_index=True)
    severity = models.CharField(max_length=10, blank=True)
    detection_count = models.PositiveIntegerField(default=0)
    detections = models.JSONField(
        default=list, blank=True,
        help_text="List of {class, confidence, bbox:[x,y,w,h]} from the model",
    )

    # Image reference (path/URL or stored file). We keep a reference rather than
    # always copying large media.
    image_reference = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to="vision/%Y/%m/", null=True, blank=True)

    device_timestamp = models.DateTimeField(null=True, blank=True)
    server_timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Human review (layered on top; never mutates the original prediction).
    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING, db_index=True
    )
    corrected_class = models.CharField(max_length=60, blank=True)
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_vision_results",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-server_timestamp"]
        indexes = [
            models.Index(fields=["farm", "server_timestamp"]),
            models.Index(fields=["predicted_class", "server_timestamp"]),
            models.Index(fields=["review_status"]),
        ]

    def __str__(self):
        return f"{self.predicted_class} ({self.confidence:.2f}) @ {self.server_timestamp:%Y-%m-%d %H:%M}"

    @property
    def effective_class(self):
        """The class to act on: corrected if reviewed, else the model's."""
        return self.corrected_class or self.predicted_class
