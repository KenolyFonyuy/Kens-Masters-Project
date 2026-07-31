from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import Expense, Payment, Sale


class DateInput(forms.DateInput):
    input_type = "date"


class ExpenseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = (
            "farm", "batch", "category", "description", "amount",
            "expense_date", "supplier", "reference",
        )
        widgets = {"expense_date": DateInput()}


class SaleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Sale
        fields = (
            "farm", "batch", "customer", "sale_date", "quantity",
            "total_weight_kg", "unit_price", "status", "reference", "notes",
        )
        widgets = {"sale_date": DateInput()}


class PaymentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("sale", "payment_date", "amount", "method", "reference")
        widgets = {"payment_date": DateInput()}
