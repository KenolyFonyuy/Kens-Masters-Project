"""Audit log browsing (admin/owner only)."""
from apps.core.mixins import RoleRequiredMixin
from django.views.generic import ListView

from .models import AuditLog


class AuditLogListView(RoleRequiredMixin, ListView):
    allowed_roles = ("ADMIN", "OWNER")
    model = AuditLog
    template_name = "audit/auditlog_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("user")
        action = self.request.GET.get("action")
        if action:
            qs = qs.filter(action=action)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(target_repr__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = AuditLog.Action.choices
        return ctx
