"""Flock management: batches, chick entries, transfers, mortality, weights,
daily observations — plus the flock-balance logic enforced via transactions.
"""
from apps.core.models import TimeStampedUserModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Batch(TimeStampedUserModel):
    """A cohort of birds placed together (a production batch)."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="batches")
    pen = models.ForeignKey(
        "farms.Pen", on_delete=models.SET_NULL, null=True, blank=True, related_name="batches"
    )
    breed = models.ForeignKey(
        "farms.Breed", on_delete=models.SET_NULL, null=True, blank=True, related_name="batches"
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    initial_quantity = models.PositiveIntegerField(
        default=0, help_text="Total chicks placed (sum of chick entries)"
    )
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-start_date"]
        unique_together = [("farm", "code")]
        indexes = [
            models.Index(fields=["farm", "status"]),
            models.Index(fields=["status", "start_date"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.farm.name})"

    # -- flock balance ----------------------------------------------------
    def _sum(self, related, field="quantity"):
        return getattr(self, related).aggregate(t=Sum(field))["t"] or 0

    @property
    def total_entries(self):
        return self._sum("chick_entries")

    @property
    def total_transfers_in(self):
        return self.transfers_in.aggregate(t=Sum("quantity"))["t"] or 0

    @property
    def total_transfers_out(self):
        return self.transfers_out.aggregate(t=Sum("quantity"))["t"] or 0

    @property
    def total_mortality(self):
        return self._sum("mortality_records")

    @property
    def total_sold(self):
        from apps.finance.models import Sale

        return (
            self.sales.filter(status=Sale.Status.CONFIRMED).aggregate(
                t=Sum("quantity")
            )["t"]
            or 0
        )

    @property
    def current_quantity(self) -> int:
        """Authoritative live bird count derived from transactions."""
        return (
            self.total_entries
            + self.total_transfers_in
            - self.total_transfers_out
            - self.total_mortality
            - self.total_sold
        )

    @property
    def cumulative_mortality_rate(self) -> float:
        base = self.total_entries + self.total_transfers_in
        if base <= 0:
            return 0.0
        return round(100.0 * self.total_mortality / base, 2)

    @property
    def age_days(self) -> int:
        end = self.actual_end_date or timezone.localdate()
        return max((end - self.start_date).days, 0)


class ChickEntry(TimeStampedUserModel):
    """A placement of chicks into a batch (supports staggered placement)."""

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="chick_entries")
    supplier = models.ForeignKey(
        "farms.Supplier", on_delete=models.SET_NULL, null=True, blank=True
    )
    entry_date = models.DateField(default=timezone.localdate)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    source_reference = models.CharField(max_length=100, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-entry_date"]
        indexes = [models.Index(fields=["batch", "entry_date"])]

    def __str__(self):
        return f"{self.quantity} chicks -> {self.batch.code}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep the denormalised initial_quantity in sync.
        Batch.objects.filter(pk=self.batch_id).update(
            initial_quantity=self.batch.total_entries
        )


class TransferRecord(TimeStampedUserModel):
    """Move birds between batches/pens. Validated against available flock."""

    source_batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="transfers_out"
    )
    destination_batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="transfers_in",
        null=True,
        blank=True,
    )
    destination_pen = models.ForeignKey(
        "farms.Pen", on_delete=models.SET_NULL, null=True, blank=True
    )
    transfer_date = models.DateField(default=timezone.localdate)
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-transfer_date"]

    def __str__(self):
        return f"Transfer {self.quantity} from {self.source_batch.code}"

    def clean(self):
        if self.quantity and self.source_batch_id:
            available = self.source_batch.current_quantity
            # When editing, add back this record's own quantity.
            if self.pk:
                available += TransferRecord.objects.get(pk=self.pk).quantity
            if self.quantity > available:
                raise ValidationError(
                    {"quantity": f"Only {available} birds available to transfer."}
                )
        if self.destination_batch_id == self.source_batch_id and self.destination_batch_id:
            raise ValidationError("Source and destination batch must differ.")


class MortalityRecord(TimeStampedUserModel):
    """Daily mortality. Cannot exceed the live flock."""

    class Cause(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        DISEASE = "disease", "Disease"
        HEAT = "heat_stress", "Heat stress"
        INJURY = "injury", "Injury"
        PREDATION = "predation", "Predation"
        CULLING = "culling", "Culling"
        OTHER = "other", "Other"

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="mortality_records"
    )
    pen = models.ForeignKey(
        "farms.Pen", on_delete=models.SET_NULL, null=True, blank=True
    )
    record_date = models.DateField(default=timezone.localdate)
    quantity = models.PositiveIntegerField()
    cause = models.CharField(max_length=20, choices=Cause.choices, default=Cause.UNKNOWN)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-record_date"]
        indexes = [models.Index(fields=["batch", "record_date"])]

    def __str__(self):
        return f"{self.quantity} deaths ({self.batch.code} {self.record_date})"

    def clean(self):
        if self.quantity and self.batch_id:
            available = self.batch.current_quantity
            if self.pk:
                available += MortalityRecord.objects.get(pk=self.pk).quantity
            if self.quantity > available:
                raise ValidationError(
                    {"quantity": f"Mortality ({self.quantity}) exceeds the live "
                                 f"flock ({available})."}
                )


class WeightRecord(TimeStampedUserModel):
    """Weight sampling for growth tracking."""

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="weight_records")
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    record_date = models.DateField(default=timezone.localdate)
    sample_size = models.PositiveIntegerField(default=1)
    average_weight_g = models.DecimalField(max_digits=8, decimal_places=1)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-record_date"]
        indexes = [models.Index(fields=["batch", "record_date"])]

    def __str__(self):
        return f"{self.average_weight_g} g ({self.batch.code} {self.record_date})"


class DailyObservation(TimeStampedUserModel):
    """Free-form daily log of behaviour/environment observed by staff."""

    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, related_name="daily_observations"
    )
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    record_date = models.DateField(default=timezone.localdate)
    water_consumption_l = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    behaviour = models.CharField(
        max_length=30,
        choices=[
            ("normal", "Normal / active"),
            ("lethargic", "Lethargic"),
            ("huddling", "Huddling"),
            ("panting", "Panting / heat stress"),
            ("restless", "Restless"),
        ],
        default="normal",
    )
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["-record_date"]

    def __str__(self):
        return f"Observation {self.batch.code} {self.record_date}"
