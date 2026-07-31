"""Batch and flock-transaction views."""
from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import (
    BatchForm,
    ChickEntryForm,
    DailyObservationForm,
    MortalityForm,
    TransferForm,
    WeightForm,
)
from .models import (
    Batch,
    ChickEntry,
    DailyObservation,
    MortalityRecord,
    TransferRecord,
    WeightRecord,
)

MANAGE = ("ADMIN", "OWNER", "MANAGER")
RECORD = ("ADMIN", "OWNER", "MANAGER", "WORKER")


class _UserScopedMixin(LoginRequiredMixin):
    """List records belonging only to the user's accessible farms."""

    farm_path = "batch__farm__in"

    def scoped(self, qs):
        allowed = farms_for_user(self.request.user)
        return qs.filter(**{self.farm_path: allowed})


# -- Batch ----------------------------------------------------------------
class BatchListView(_UserScopedMixin, ListView):
    model = Batch
    template_name = "flocks/batch_list.html"
    context_object_name = "batches"
    paginate_by = 20
    farm_path = "farm__in"

    def get_queryset(self):
        qs = self.scoped(super().get_queryset().select_related("farm", "pen", "breed"))
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(code__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Batch.Status.choices
        return ctx


class BatchDetailView(UidUrlMixin, _UserScopedMixin, DetailView):
    model = Batch
    template_name = "flocks/batch_detail.html"
    farm_path = "farm__in"

    def get_queryset(self):
        return self.scoped(super().get_queryset())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        b = self.object
        ctx["mortality"] = b.mortality_records.all()[:10]
        ctx["weights"] = b.weight_records.all()[:10]
        ctx["observations"] = b.daily_observations.all()[:10]
        ctx["entries"] = b.chick_entries.all()
        return ctx


class BatchCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Batch
    form_class = BatchForm
    template_name = "flocks/batch_form.html"
    success_url = reverse_lazy("flocks:batch_list")


class BatchUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Batch
    form_class = BatchForm
    template_name = "flocks/batch_form.html"
    success_url = reverse_lazy("flocks:batch_list")


# -- Generic transaction list/create -------------------------------------
class _TxnList(_UserScopedMixin, ListView):
    paginate_by = 25

    def get_queryset(self):
        return self.scoped(super().get_queryset().select_related("batch"))


class ChickEntryListView(_TxnList):
    model = ChickEntry
    template_name = "flocks/chickentry_list.html"
    context_object_name = "records"


class ChickEntryCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = ChickEntry
    form_class = ChickEntryForm
    template_name = "flocks/record_form.html"
    success_url = reverse_lazy("flocks:chickentry_list")
    extra_context = {"object_label": "Chick entry"}


class MortalityListView(_TxnList):
    model = MortalityRecord
    template_name = "flocks/mortality_list.html"
    context_object_name = "records"


class MortalityCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = RECORD
    model = MortalityRecord
    form_class = MortalityForm
    template_name = "flocks/record_form.html"
    success_url = reverse_lazy("flocks:mortality_list")
    extra_context = {"object_label": "Mortality record"}

    def form_valid(self, form):
        # Model.clean already enforces the balance; full_clean runs on save via
        # ModelForm validation. Add a friendly confirmation.
        messages.success(self.request, "Mortality recorded.")
        return super().form_valid(form)


class TransferListView(_UserScopedMixin, ListView):
    model = TransferRecord
    template_name = "flocks/transfer_list.html"
    context_object_name = "records"
    paginate_by = 25
    farm_path = "source_batch__farm__in"

    def get_queryset(self):
        return self.scoped(super().get_queryset().select_related("source_batch"))


class TransferCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = TransferRecord
    form_class = TransferForm
    template_name = "flocks/record_form.html"
    success_url = reverse_lazy("flocks:transfer_list")
    extra_context = {"object_label": "Transfer"}


class WeightListView(_TxnList):
    model = WeightRecord
    template_name = "flocks/weight_list.html"
    context_object_name = "records"


class WeightCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = RECORD
    model = WeightRecord
    form_class = WeightForm
    template_name = "flocks/record_form.html"
    success_url = reverse_lazy("flocks:weight_list")
    extra_context = {"object_label": "Weight sample"}


class ObservationListView(_TxnList):
    model = DailyObservation
    template_name = "flocks/observation_list.html"
    context_object_name = "records"


class ObservationCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = RECORD
    model = DailyObservation
    form_class = DailyObservationForm
    template_name = "flocks/record_form.html"
    success_url = reverse_lazy("flocks:observation_list")
    extra_context = {"object_label": "Daily observation"}
