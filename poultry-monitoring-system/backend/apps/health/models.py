"""Health: observations, medications, treatments, vaccination schedules/records.

Medication usage can optionally decrement a linked inventory item (configurable
per treatment), mirroring the feed-usage behaviour.
"""
from apps.core.models import TimeStampedUserModel
from django.conf import settings
from django.db import models
from django.utils import timezone


class HealthObservation(TimeStampedUserModel):
    """A recorded health concern for a batch/pen (clinical-style note)."""

    class Severity(models.TextChoices):
        INFO = "info", "Information"
        MILD = "mild", "Mild"
        MODERATE = "moderate", "Moderate"
        SEVERE = "severe", "Severe"

    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.CASCADE, related_name="health_observations"
    )
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    observation_date = models.DateField(default=timezone.localdate)
    title = models.CharField(max_length=150)
    symptoms = models.TextField(blank=True)
    severity = models.CharField(
        max_length=20, choices=Severity.choices, default=Severity.INFO, db_index=True
    )
    affected_count = models.PositiveIntegerField(default=0)
    # Optional link back to a machine-vision prediction that triggered this.
    vision_result = models.ForeignKey(
        "vision.VisionResult", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="health_observations",
    )
    # Veterinary review fields.
    vet_comment = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_health_observations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-observation_date"]
        indexes = [models.Index(fields=["batch", "observation_date"])]

    def __str__(self):
        return f"{self.title} ({self.batch.code})"


class Medication(TimeStampedUserModel):
    name = models.CharField(max_length=150, unique=True)
    medication_type = models.CharField(
        max_length=40,
        choices=[
            ("antibiotic", "Antibiotic"),
            ("vaccine", "Vaccine"),
            ("vitamin", "Vitamin / supplement"),
            ("antiparasitic", "Antiparasitic"),
            ("other", "Other"),
        ],
        default="other",
    )
    unit = models.CharField(max_length=20, default="dose")
    withdrawal_days = models.PositiveIntegerField(
        default=0, help_text="Days before birds may be sold after treatment"
    )
    inventory_item = models.ForeignKey(
        "inventory.InventoryItem", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="medications",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TreatmentRecord(TimeStampedUserModel):
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.CASCADE, related_name="treatments"
    )
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, related_name="treatments")
    health_observation = models.ForeignKey(
        HealthObservation, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="treatments",
    )
    treatment_date = models.DateField(default=timezone.localdate)
    dosage = models.CharField(max_length=120, blank=True)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    administered_by = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    decrement_inventory = models.BooleanField(default=False)
    stock_applied = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-treatment_date"]

    def __str__(self):
        return f"{self.medication} -> {self.batch.code}"


class VaccinationSchedule(TimeStampedUserModel):
    """A planned vaccination at a given bird age for a batch."""

    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.CASCADE, related_name="vaccination_schedules"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.PROTECT, related_name="vaccination_schedules"
    )
    vaccine_name = models.CharField(max_length=150)
    scheduled_age_days = models.PositiveIntegerField(default=7)
    scheduled_date = models.DateField(null=True, blank=True)
    route = models.CharField(max_length=80, blank=True)
    is_done = models.BooleanField(default=False, db_index=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["scheduled_age_days"]

    def __str__(self):
        return f"{self.vaccine_name} @ day {self.scheduled_age_days} ({self.batch.code})"


class VaccinationRecord(TimeStampedUserModel):
    schedule = models.ForeignKey(
        VaccinationSchedule, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="records",
    )
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.CASCADE, related_name="vaccination_records"
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.PROTECT, related_name="vaccination_records"
    )
    vaccine_name = models.CharField(max_length=150)
    administered_date = models.DateField(default=timezone.localdate)
    quantity = models.PositiveIntegerField(default=0, help_text="Birds vaccinated")
    administered_by = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-administered_date"]

    def __str__(self):
        return f"{self.vaccine_name} ({self.batch.code} {self.administered_date})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.schedule_id and not self.schedule.is_done:
            VaccinationSchedule.objects.filter(pk=self.schedule_id).update(is_done=True)
