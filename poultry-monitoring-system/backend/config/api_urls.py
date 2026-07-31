"""Versioned REST API routes (mounted under /api/v1/)."""
from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("", include("apps.iot.api_urls")),
    path("", include("apps.vision.api_urls")),
    path("", include("apps.alerts.api_urls")),
]
