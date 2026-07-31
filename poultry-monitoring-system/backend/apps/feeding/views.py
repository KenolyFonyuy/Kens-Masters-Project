from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import FeedTypeForm, FeedUsageForm
from .models import FeedType, FeedUsage

MANAGE = ("ADMIN", "OWNER", "MANAGER")
RECORD = ("ADMIN", "OWNER", "MANAGER", "WORKER")


class FeedUsageListView(LoginRequiredMixin, ListView):
    model = FeedUsage
    template_name = "feeding/feedusage_list.html"
    context_object_name = "records"
    paginate_by = 25

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        return (
            super()
            .get_queryset()
            .filter(batch__farm__in=allowed)
            .select_related("batch", "feed_type")
        )


class FeedUsageCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = RECORD
    model = FeedUsage
    form_class = FeedUsageForm
    template_name = "feeding/record_form.html"
    success_url = reverse_lazy("feeding:usage_list")
    extra_context = {"object_label": "Feed usage"}

    def form_valid(self, form):
        messages.success(self.request, "Feed usage recorded.")
        return super().form_valid(form)


class FeedTypeListView(RoleRequiredMixin, ListView):
    allowed_roles = MANAGE
    model = FeedType
    template_name = "feeding/feedtype_list.html"
    context_object_name = "feed_types"
    paginate_by = 25


class FeedTypeCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = FeedType
    form_class = FeedTypeForm
    template_name = "feeding/record_form.html"
    success_url = reverse_lazy("feeding:feedtype_list")
    extra_context = {"object_label": "Feed type"}


class FeedTypeUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = FeedType
    form_class = FeedTypeForm
    template_name = "feeding/record_form.html"
    success_url = reverse_lazy("feeding:feedtype_list")
    extra_context = {"object_label": "Feed type"}
