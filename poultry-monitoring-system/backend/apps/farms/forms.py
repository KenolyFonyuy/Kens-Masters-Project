from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import Breed, Customer, Farm, Pen, Supplier


class FarmForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Farm
        fields = (
            "name", "code", "location", "city", "region", "country",
            "latitude", "longitude", "owner", "is_active", "notes",
        )


class PenForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Pen
        fields = ("farm", "name", "code", "capacity", "floor_area_m2", "is_active")


class BreedForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Breed
        fields = (
            "name", "species", "description",
            "typical_market_age_days", "target_market_weight_g",
        )


class SupplierForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = (
            "name", "contact_person", "phone", "email", "address",
            "supplies", "is_active",
        )


class CustomerForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            "name", "contact_person", "phone", "email", "address",
            "customer_type", "is_active",
        )
