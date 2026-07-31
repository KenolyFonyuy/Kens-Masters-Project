"""Root URL configuration for the Poultry Monitoring System."""
from apps.core import views as core_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Server-rendered application
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("farms/", include("apps.farms.urls")),
    path("flocks/", include("apps.flocks.urls")),
    path("feeding/", include("apps.feeding.urls")),
    path("health/", include("apps.health.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("finance/", include("apps.finance.urls")),
    path("monitoring/", include("apps.iot.urls")),
    path("vision/", include("apps.vision.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("reports/", include("apps.reports.urls")),
    path("audit/", include("apps.audit.urls")),
    # Health check
    path("healthz/", core_views.health_check, name="health-check"),
    # Versioned REST API
    path("api/v1/", include("config.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
