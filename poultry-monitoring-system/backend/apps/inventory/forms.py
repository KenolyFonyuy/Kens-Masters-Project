from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import InventoryCategory, InventoryItem, StockMovement


class DateInput(forms.DateInput):
    input_type = "date"


class InventoryCategoryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = ("name", "description")


class InventoryItemForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = (
            "farm", "category", "name", "sku", "unit",
            "opening_stock", "reorder_level", "unit_cost", "is_active",
        )


class StockMovementForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = (
            "item", "movement_type", "quantity", "movement_date",
            "reference", "notes", "allow_negative",
        )
        widgets = {"movement_date": DateInput()}
