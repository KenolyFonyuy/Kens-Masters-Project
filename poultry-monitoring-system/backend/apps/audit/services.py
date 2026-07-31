"""Helpers for writing audit log entries."""
from .middleware import get_current_request, get_current_user
from .models import AuditLog


def _client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(action, *, target=None, message="", user=None, request=None, **metadata):
    """Create an AuditLog entry; never raises into the calling code path."""
    request = request or get_current_request()
    user = user or get_current_user()
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None
    try:
        return AuditLog.objects.create(
            user=user,
            action=action,
            target_repr=str(target)[:255] if target is not None else "",
            object_type=target.__class__.__name__ if target is not None else "",
            object_id=str(getattr(target, "pk", "")) if target is not None else "",
            message=message,
            ip_address=_client_ip(request),
            metadata=metadata or {},
        )
    except Exception:  # pragma: no cover - auditing must never break a request
        return None
