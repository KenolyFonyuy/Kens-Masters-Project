from django.conf import settings


def site_context(request):
    """Expose site-wide constants and the active alert count to all templates."""
    context = {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_SHORT_NAME": settings.SITE_SHORT_NAME,
        "active_alert_count": 0,
    }
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        try:
            from apps.alerts.models import Alert
            from apps.alerts.services import alerts_visible_to

            context["active_alert_count"] = (
                alerts_visible_to(user)
                .filter(status__in=[Alert.Status.NEW, Alert.Status.ACKNOWLEDGED])
                .count()
            )
        except Exception:  # pragma: no cover - defensive for early migrations
            context["active_alert_count"] = 0
    return context
