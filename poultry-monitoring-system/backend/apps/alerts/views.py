"""Alert list/detail and state-transition views."""
from apps.core.mixins import UidUrlMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from .models import Alert
from .services import alerts_visible_to, transition

RESOLVE_ROLES = ("ADMIN", "OWNER", "MANAGER")


class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = "alerts/alert_list.html"
    context_object_name = "alerts"
    paginate_by = 25

    def get_queryset(self):
        qs = alerts_visible_to(self.request.user).select_related("farm", "pen", "device")
        status = self.request.GET.get("status")
        severity = self.request.GET.get("severity")
        if status:
            qs = qs.filter(status=status)
        if severity:
            qs = qs.filter(severity=severity)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Alert.Status.choices
        ctx["severities"] = Alert._meta.get_field("severity").choices
        return ctx


class AlertDetailView(UidUrlMixin, LoginRequiredMixin, DetailView):
    model = Alert
    template_name = "alerts/alert_detail.html"

    def get_queryset(self):
        return alerts_visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = self.object.actions.select_related("actor").all()
        ctx["can_resolve"] = self.request.user.has_any_role(RESOLVE_ROLES) or self.request.user.is_superuser
        return ctx


class AlertTransitionView(LoginRequiredMixin, View):
    """Acknowledge / investigate / resolve / mark-false / escalate an alert."""

    VALID = {
        "acknowledge": Alert.Status.ACKNOWLEDGED,
        "investigate": Alert.Status.INVESTIGATING,
        "resolve": Alert.Status.RESOLVED,
        "false": Alert.Status.FALSE,
        "escalate": Alert.Status.ESCALATED,
    }

    def post(self, request, uid, action):
        alert = get_object_or_404(alerts_visible_to(request.user), uid=uid)
        to_status = self.VALID.get(action)
        if not to_status:
            messages.error(request, "Unknown action.")
            return redirect("alerts:alert_detail", uid=uid)
        # Resolving / false / escalate require resolve role; acknowledge is open.
        if action in {"resolve", "false", "escalate", "investigate"} and not (
            request.user.has_any_role(RESOLVE_ROLES) or request.user.is_superuser
        ):
            messages.error(request, "You are not allowed to perform that action.")
            return redirect("alerts:alert_detail", uid=uid)
        note = request.POST.get("note", "")
        if to_status in {Alert.Status.RESOLVED, Alert.Status.FALSE}:
            alert.corrective_action = request.POST.get("corrective_action", alert.corrective_action)
            alert.save(update_fields=["corrective_action"])
        transition(alert, to_status=to_status, actor=request.user, note=note)
        messages.success(request, f"Alert marked {alert.get_status_display()}.")
        return redirect("alerts:alert_detail", uid=uid)
