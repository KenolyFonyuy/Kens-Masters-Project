from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import FeedType, FeedUsage


class DateInput(forms.DateInput):
    input_type = "date"


class FeedTypeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FeedType
        fields = ("name", "phase", "protein_pct", "inventory_item", "is_active")


class FeedUsageForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FeedUsage
        fields = ("batch", "pen", "feed_type", "record_date", "quantity_kg", "notes")
        widgets = {"record_date": DateInput()}
