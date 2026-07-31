from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import (
    Batch,
    ChickEntry,
    DailyObservation,
    MortalityRecord,
    TransferRecord,
    WeightRecord,
)


class DateInput(forms.DateInput):
    input_type = "date"


class BatchForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Batch
        fields = (
            "farm", "pen", "breed", "code", "name", "start_date",
            "expected_end_date", "status", "notes",
        )
        widgets = {
            "start_date": DateInput(),
            "expected_end_date": DateInput(),
        }


class ChickEntryForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ChickEntry
        fields = (
            "batch", "supplier", "entry_date", "quantity", "unit_cost",
            "source_reference", "notes",
        )
        widgets = {"entry_date": DateInput()}


class MortalityForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = MortalityRecord
        fields = ("batch", "pen", "record_date", "quantity", "cause", "notes")
        widgets = {"record_date": DateInput()}


class TransferForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TransferRecord
        fields = (
            "source_batch", "destination_batch", "destination_pen",
            "transfer_date", "quantity", "reason",
        )
        widgets = {"transfer_date": DateInput()}


class WeightForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = WeightRecord
        fields = (
            "batch", "pen", "record_date", "sample_size",
            "average_weight_g", "notes",
        )
        widgets = {"record_date": DateInput()}


class DailyObservationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DailyObservation
        fields = (
            "batch", "pen", "record_date", "water_consumption_l",
            "behaviour", "remarks",
        )
        widgets = {"record_date": DateInput()}
