"""Reusable view mixins for permission enforcement and farm data isolation."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a view to users in one of ``allowed_roles`` (or superusers)."""

    allowed_roles: tuple[str, ...] = ()

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        if not self.allowed_roles:
            return True
        return user.has_any_role(self.allowed_roles)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You do not have access to this resource.")
        return super().handle_no_permission()


class FarmScopedQuerysetMixin:
    """Limit a list/detail queryset to farms the current user may access.

    The model (or its related path given by ``farm_lookup``) must reach a
    ``Farm``. Superusers and admins see everything; other users see only farms
    they own, manage, or are assigned to.
    """

    farm_lookup = "farm"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or user.has_role("ADMIN"):
            return qs
        from apps.farms.services import farms_for_user

        allowed = farms_for_user(user).values_list("pk", flat=True)
        return qs.filter(**{f"{self.farm_lookup}__in": list(allowed)})


class UidUrlMixin:
    """Look an object up by its ``uid`` UUID field from a ``uid`` URL kwarg."""

    slug_field = "uid"
    slug_url_kwarg = "uid"


class AuditCreateUpdateMixin:
    """For ModelForm CreateView/UpdateView — stamp the acting user.

    ``created_by``/``updated_by`` are also set by the model ``save`` via the
    current-user middleware; this mixin is a belt-and-braces fallback for code
    paths that bypass the middleware (e.g. management commands run as a user).
    """

    def form_valid(self, form):
        obj = form.save(commit=False)
        if obj.pk is None and getattr(obj, "created_by_id", None) is None:
            obj.created_by = self.request.user
        obj.updated_by = self.request.user
        obj.save()
        form.save_m2m()
        self.object = obj
        return super().form_valid(form)
