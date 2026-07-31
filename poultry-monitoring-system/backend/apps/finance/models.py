"""Finance: expenses, sales (bird sales) and payments.

A confirmed ``Sale`` reduces the live flock; its quantity is validated against
available birds. Sales are not silently deleted — cancelling sets a status.
"""
from decimal import Decimal

from apps.core.models import TimeStampedUserModel
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Expense(TimeStampedUserModel):
    class Category(models.TextChoices):
        FEED = "feed", "Feed"
        MEDICATION = "medication", "Medication / health"
        LABOUR = "labour", "Labour"
        UTILITIES = "utilities", "Utilities"
        EQUIPMENT = "equipment", "Equipment"
        CHICKS = "chicks", "Chick purchase"
        OTHER = "other", "Other"

    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="expenses")
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses"
    )
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(default=timezone.localdate)
    supplier = models.ForeignKey(
        "farms.Supplier", on_delete=models.SET_NULL, null=True, blank=True
    )
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-expense_date"]
        indexes = [models.Index(fields=["farm", "expense_date"])]

    def __str__(self):
        return f"{self.category} {self.amount} ({self.farm.name})"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})


class Sale(TimeStampedUserModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="sales")
    batch = models.ForeignKey(
        "flocks.Batch", on_delete=models.PROTECT, related_name="sales"
    )
    customer = models.ForeignKey(
        "farms.Customer", on_delete=models.SET_NULL, null=True, blank=True
    )
    sale_date = models.DateField(default=timezone.localdate)
    quantity = models.PositiveIntegerField(help_text="Number of birds sold")
    total_weight_kg = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CONFIRMED, db_index=True
    )
    reference = models.CharField(max_length=120, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-sale_date"]
        indexes = [models.Index(fields=["farm", "sale_date"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"Sale {self.quantity} birds ({self.batch.code})"

    @property
    def total_amount(self) -> Decimal:
        return (self.unit_price or Decimal("0")) * self.quantity

    @property
    def amount_paid(self) -> Decimal:
        return self.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def balance_due(self) -> Decimal:
        return self.total_amount - self.amount_paid

    def clean(self):
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be positive."})
        # Only confirmed sales consume flock; validate availability.
        if self.status == self.Status.CONFIRMED and self.batch_id:
            available = self.batch.current_quantity
            # Add back this sale's own previous confirmed quantity when editing.
            if self.pk:
                old = Sale.objects.get(pk=self.pk)
                if old.status == self.Status.CONFIRMED:
                    available += old.quantity
            if self.quantity > available:
                raise ValidationError(
                    {"quantity": f"Sale ({self.quantity}) exceeds the live flock "
                                 f"({available})."}
                )


class Payment(TimeStampedUserModel):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE = "mobile_money", "Mobile money"
        BANK = "bank_transfer", "Bank transfer"
        OTHER = "other", "Other"

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    payment_date = models.DateField(default=timezone.localdate)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return f"Payment {self.amount} for {self.sale}"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})
