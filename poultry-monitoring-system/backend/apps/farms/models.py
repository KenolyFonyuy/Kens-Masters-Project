"""Organisation models: Farm, Pen, Breed, Supplier, Customer."""
from apps.core.models import TimeStampedUserModel
from django.conf import settings
from django.db import models


class Farm(TimeStampedUserModel):
    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=40, unique=True, help_text="Short unique code")
    location = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, default="Yaoundé")
    region = models.CharField(max_length=100, default="Centre")
    country = models.CharField(max_length=100, default="Cameroon")
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_farms",
    )
    is_demo = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return self.name

    @property
    def pen_count(self):
        return self.pens.count()


class Pen(TimeStampedUserModel):
    """A house / pen / compartment within a farm."""

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="pens")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40)
    capacity = models.PositiveIntegerField(default=0, help_text="Max birds")
    floor_area_m2 = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["farm", "name"]
        unique_together = [("farm", "code")]
        indexes = [models.Index(fields=["farm", "is_active"])]

    def __str__(self):
        return f"{self.name} @ {self.farm.name}"


class Breed(TimeStampedUserModel):
    """Broiler breed / strain reference."""

    name = models.CharField(max_length=100, unique=True)
    species = models.CharField(max_length=60, default="Broiler chicken")
    description = models.TextField(blank=True)
    typical_market_age_days = models.PositiveIntegerField(default=42)
    target_market_weight_g = models.PositiveIntegerField(default=2200)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(TimeStampedUserModel):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    supplies = models.CharField(
        max_length=200, blank=True, help_text="e.g. chicks, feed, medication"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Customer(TimeStampedUserModel):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    customer_type = models.CharField(
        max_length=40,
        choices=[
            ("individual", "Individual"),
            ("retailer", "Retailer"),
            ("wholesaler", "Wholesaler"),
            ("restaurant", "Restaurant"),
        ],
        default="individual",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
