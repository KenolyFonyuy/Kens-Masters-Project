"""DRF permission classes for capability- and device-based access."""
from rest_framework.permissions import BasePermission


class HasCapability(BasePermission):
    """Allow access if the authenticated user has ``required_capability``.

    Attach via a small subclass or set ``view.required_capability``.
    """

    def has_permission(self, request, view):
        cap = getattr(view, "required_capability", None)
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if not hasattr(user, "has_capability"):
            return False
        return cap is None or user.has_capability(cap)


class IsDevice(BasePermission):
    """Allow only requests authenticated with a device token."""

    def has_permission(self, request, view):
        return getattr(request, "device", None) is not None


class IsDeviceOrAuthenticatedUser(BasePermission):
    def has_permission(self, request, view):
        if getattr(request, "device", None) is not None:
            return True
        return bool(request.user and request.user.is_authenticated)
