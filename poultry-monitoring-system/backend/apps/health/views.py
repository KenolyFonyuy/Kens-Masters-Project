from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import (
    HealthObservationForm,
    MedicationForm,
    TreatmentForm,
    VaccinationRecordForm,
    VaccinationScheduleForm,
    VetReviewForm,
)
from .models import (
    HealthObservation,
    Medication,
    TreatmentRecord,
    VaccinationRecord,
    VaccinationSchedule,
)

MANAGE = ("ADMIN", "OWNER", "MANAGER")
HEALTH_RECORD = ("ADMIN", "OWNER", "MANAGER", "WORKER", "VET")
VIEW_ROLES = ("ADMIN", "OWNER", "MANAGER", "WORKER", "VET")


class _FarmScoped(LoginRequiredMixin):
    farm_path = "batch__farm__in"

    def scoped(self, qs):
        return qs.filter(**{self.farm_path: farms_for_user(self.request.user)})


class HealthObservationListView(_FarmScoped, ListView):
    model = HealthObservation
    template_name = "health/observation_list.html"
    context_object_name = "observations"
    paginate_by = 25

    def get_queryset(self):
        qs = self.scoped(super().get_queryset().select_related("batch"))
        sev = self.request.GET.get("severity")
        if sev:
            qs = qs.filter(severity=sev)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["severities"] = HealthObservation.Severity.choices
        return ctx


class HealthObservationDetailView(UidUrlMixin, _FarmScoped, DetailView):
    model = HealthObservation
    template_name = "health/observation_detail.html"

    def get_queryset(self):
        return self.scoped(super().get_queryset())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["review_form"] = VetReviewForm(instance=self.object)
        return ctx


class HealthObservationCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = HEALTH_RECORD
    model = HealthObservation
    form_class = HealthObservationForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:observation_list")
    extra_context = {"object_label": "Health observation"}


class VetReviewView(RoleRequiredMixin, UidUrlMixin, View):
    """A vet (or manager/owner/admin) adds a professional comment."""

    allowed_roles = ("ADMIN", "OWNER", "MANAGER", "VET")

    def post(self, request, uid):
        obs = get_object_or_404(HealthObservation, uid=uid)
        form = VetReviewForm(request.POST, instance=obs)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            obj.save()
            messages.success(request, "Review saved.")
        return redirect("health:observation_detail", uid=uid)


# -- Medication ----------------------------------------------------------
class MedicationListView(RoleRequiredMixin, ListView):
    allowed_roles = MANAGE + ("VET",)
    model = Medication
    template_name = "health/medication_list.html"
    context_object_name = "medications"
    paginate_by = 25


class MedicationCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Medication
    form_class = MedicationForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:medication_list")
    extra_context = {"object_label": "Medication"}


class MedicationUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Medication
    form_class = MedicationForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:medication_list")
    extra_context = {"object_label": "Medication"}


# -- Treatments ----------------------------------------------------------
class TreatmentListView(_FarmScoped, ListView):
    model = TreatmentRecord
    template_name = "health/treatment_list.html"
    context_object_name = "treatments"
    paginate_by = 25

    def get_queryset(self):
        return self.scoped(super().get_queryset().select_related("batch", "medication"))


class TreatmentCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE + ("VET",)
    model = TreatmentRecord
    form_class = TreatmentForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:treatment_list")
    extra_context = {"object_label": "Treatment"}


# -- Vaccinations --------------------------------------------------------
class VaccinationScheduleListView(_FarmScoped, ListView):
    model = VaccinationSchedule
    template_name = "health/vaccination_schedule_list.html"
    context_object_name = "schedules"
    paginate_by = 25

    def get_queryset(self):
        return self.scoped(super().get_queryset().select_related("batch"))


class VaccinationScheduleCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = VaccinationSchedule
    form_class = VaccinationScheduleForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:vaccination_schedule_list")
    extra_context = {"object_label": "Vaccination schedule"}


class VaccinationRecordListView(_FarmScoped, ListView):
    model = VaccinationRecord
    template_name = "health/vaccination_record_list.html"
    context_object_name = "records"
    paginate_by = 25

    def get_queryset(self):
        return self.scoped(super().get_queryset().select_related("batch"))


class VaccinationRecordCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE + ("WORKER",)
    model = VaccinationRecord
    form_class = VaccinationRecordForm
    template_name = "health/record_form.html"
    success_url = reverse_lazy("health:vaccination_record_list")
    extra_context = {"object_label": "Vaccination record"}
