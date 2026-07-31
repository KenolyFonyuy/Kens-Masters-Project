"""Feeding: feed types and per-batch feed usage."""
from apps.core.models import TimeStampedUserModel
from django.db import models
from django.utils import timezone


class FeedType(TimeStampedUserModel):
    """A feed product / formulation (starter, grower, finisher, ...)."""

    class Phase(models.TextChoices):
        STARTER = "starter", "Starter"
        GROWER = "grower", "Grower"
        FINISHER = "finisher", "Finisher"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120, unique=True)
    phase = models.CharField(max_length=20, choices=Phase.choices, default=Phase.STARTER)
    protein_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    # Optional link to a tracked inventory item so usage can decrement stock.
    inventory_item = models.ForeignKey(
        "inventory.InventoryItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feed_types",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeedUsage(TimeStampedUserModel):
    """A feeding event consuming a quantity (kg) of feed for a batch."""

    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.CASCADE, related_name="feed_usages"
    )
    pen = models.ForeignKey("farms.Pen", on_delete=models.SET_NULL, null=True, blank=True)
    feed_type = models.ForeignKey(FeedType, on_delete=models.PROTECT, related_name="usages")
    record_date = models.DateField(default=timezone.localdate)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)
    # Set once the linked inventory item has been decremented (idempotency).
    stock_applied = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-record_date"]
        indexes = [models.Index(fields=["batch", "record_date"])]

    def __str__(self):
        return f"{self.quantity_kg} kg {self.feed_type} -> {self.batch.code}"
