from django.contrib import admin

from .models import (
    HealthObservation,
    Medication,
    TreatmentRecord,
    VaccinationRecord,
    VaccinationSchedule,
)


@admin.register(HealthObservation)
class HealthObservationAdmin(admin.ModelAdmin):
    list_display = ("title", "batch", "severity", "observation_date", "reviewed_by")
    list_filter = ("severity", "observation_date")
    search_fields = ("title", "symptoms")


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("name", "medication_type", "unit", "withdrawal_days", "is_active")
    list_filter = ("medication_type", "is_active")


admin.site.register(TreatmentRecord)
admin.site.register(VaccinationSchedule)
admin.site.register(VaccinationRecord)
