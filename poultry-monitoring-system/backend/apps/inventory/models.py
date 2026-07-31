"""Inventory: categories, items and an append-only stock-movement ledger.

Available stock is derived from the movement ledger so history is preserved and
auditable rather than stored as a single mutable number:

    available = opening_stock + sum(signed movements)

where receipts / positive adjustments are positive, and issues / expiry /
damage / negative adjustments are negative.
"""
from decimal import Decimal

from apps.core.models import TimeStampedUserModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class InventoryCategory(TimeStampedUserModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Inventory categories"

    def __str__(self):
        return self.name


class InventoryItem(TimeStampedUserModel):
    farm = models.ForeignKey(
        "farms.Farm", on_delete=models.CASCADE, related_name="inventory_items"
    )
    category = models.ForeignKey(
        InventoryCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="items",
    )
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=60, blank=True)
    unit = models.CharField(max_length=20, default="kg", help_text="kg, bag, dose, ...")
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("farm", "name")]
        indexes = [models.Index(fields=["farm", "is_active"])]

    def __str__(self):
        return f"{self.name} ({self.farm.name})"

    @property
    def movement_balance(self) -> Decimal:
        total = self.movements.aggregate(t=Sum("signed_quantity"))["t"]
        return total or Decimal("0")

    @property
    def current_stock(self) -> Decimal:
        return (self.opening_stock or Decimal("0")) + self.movement_balance

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.reorder_level


class StockMovement(TimeStampedUserModel):
    """An immutable change to an item's stock. ``signed_quantity`` is derived
    from ``movement_type`` and ``quantity`` on save."""

    class Type(models.TextChoices):
        RECEIPT = "receipt", "Stock received"
        ISSUE = "issue", "Stock issued"
        ADJUST_POS = "adjust_pos", "Positive adjustment"
        ADJUST_NEG = "adjust_neg", "Negative adjustment"
        EXPIRY = "expiry", "Expired"
        DAMAGE = "damage", "Damaged"

    POSITIVE = {Type.RECEIPT, Type.ADJUST_POS}

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="movements"
    )
    movement_type = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    signed_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    movement_date = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    # Privileged override allows a movement that would drive stock negative.
    allow_negative = models.BooleanField(default=False)

    class Meta:
        ordering = ["-movement_date", "-created_at"]
        indexes = [models.Index(fields=["item", "movement_date"])]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} {self.item.name}"

    @property
    def is_positive(self) -> bool:
        return self.movement_type in self.POSITIVE

    def clean(self):
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be positive."})
        if not self.is_positive and not self.allow_negative and self.item_id:
            projected = self.item.current_stock - self.quantity
            # When editing, ignore this record's previous effect.
            if self.pk:
                old = StockMovement.objects.get(pk=self.pk)
                projected += -old.signed_quantity
            if projected < 0:
                raise ValidationError(
                    "This movement would make stock negative "
                    f"({projected}). Authorise an adjustment to override."
                )

    def save(self, *args, **kwargs):
        self.signed_quantity = self.quantity if self.is_positive else -self.quantity
        super().save(*args, **kwargs)
