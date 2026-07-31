from django.urls import path

from . import views

app_name = "health"

urlpatterns = [
    path("", views.HealthObservationListView.as_view(), name="observation_list"),
    path("add/", views.HealthObservationCreateView.as_view(), name="observation_create"),
    path("<uuid:uid>/", views.HealthObservationDetailView.as_view(), name="observation_detail"),
    path("<uuid:uid>/review/", views.VetReviewView.as_view(), name="observation_review"),
    # Medications
    path("medications/", views.MedicationListView.as_view(), name="medication_list"),
    path("medications/add/", views.MedicationCreateView.as_view(), name="medication_create"),
    path("medications/<uuid:uid>/edit/", views.MedicationUpdateView.as_view(), name="medication_update"),
    # Treatments
    path("treatments/", views.TreatmentListView.as_view(), name="treatment_list"),
    path("treatments/add/", views.TreatmentCreateView.as_view(), name="treatment_create"),
    # Vaccinations
    path("vaccinations/schedule/", views.VaccinationScheduleListView.as_view(), name="vaccination_schedule_list"),
    path("vaccinations/schedule/add/", views.VaccinationScheduleCreateView.as_view(), name="vaccination_schedule_create"),
    path("vaccinations/records/", views.VaccinationRecordListView.as_view(), name="vaccination_record_list"),
    path("vaccinations/records/add/", views.VaccinationRecordCreateView.as_view(), name="vaccination_record_create"),
]
