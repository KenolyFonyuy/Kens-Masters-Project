from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import (
    HealthObservation,
    Medication,
    TreatmentRecord,
    VaccinationRecord,
    VaccinationSchedule,
)


class DateInput(forms.DateInput):
    input_type = "date"


class HealthObservationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = HealthObservation
        fields = (
            "batch", "pen", "observation_date", "title", "symptoms",
            "severity", "affected_count",
        )
        widgets = {"observation_date": DateInput(), "symptoms": forms.Textarea(attrs={"rows": 3})}


class VetReviewForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = HealthObservation
        fields = ("vet_comment",)
        widgets = {"vet_comment": forms.Textarea(attrs={"rows": 3})}


class MedicationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Medication
        fields = (
            "name", "medication_type", "unit", "withdrawal_days",
            "inventory_item", "is_active",
        )


class TreatmentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TreatmentRecord
        fields = (
            "batch", "pen", "medication", "health_observation", "treatment_date",
            "dosage", "quantity_used", "administered_by", "notes", "decrement_inventory",
        )
        widgets = {"treatment_date": DateInput()}


class VaccinationScheduleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = VaccinationSchedule
        fields = (
            "batch", "medication", "vaccine_name", "scheduled_age_days",
            "scheduled_date", "route", "notes",
        )
        widgets = {"scheduled_date": DateInput()}


class VaccinationRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = (
            "schedule", "batch", "medication", "vaccine_name",
            "administered_date", "quantity", "administered_by", "notes",
        )
        widgets = {"administered_date": DateInput()}
