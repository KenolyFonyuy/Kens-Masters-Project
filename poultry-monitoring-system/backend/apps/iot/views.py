"""Monitoring web views: devices, environmental history, chart data, thresholds."""
from datetime import timedelta

from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.db.models.functions import TruncHour
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import EnvironmentalThresholdForm, IoTDeviceForm
from .models import ActuatorEvent, EnvironmentalThreshold, IoTDevice, SensorReading

MANAGE = ("ADMIN", "OWNER", "MANAGER")


class DeviceListView(LoginRequiredMixin, ListView):
    model = IoTDevice
    template_name = "iot/device_list.html"
    context_object_name = "devices"
    paginate_by = 25

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(farm__in=farms_for_user(self.request.user))
            .select_related("farm", "pen")
        )


class DeviceDetailView(LoginRequiredMixin, DetailView):
    model = IoTDevice
    slug_field = "device_id"
    slug_url_kwarg = "device_id"
    template_name = "iot/device_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(farm__in=farms_for_user(self.request.user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["latest_reading"] = self.object.readings.first()
        ctx["recent_readings"] = self.object.readings.all()[:20]
        ctx["actuator_events"] = self.object.actuator_events.all()[:20]
        ctx["heartbeats"] = self.object.heartbeats.all()[:10]
        return ctx


class DeviceCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = IoTDevice
    form_class = IoTDeviceForm
    template_name = "iot/device_form.html"
    success_url = reverse_lazy("iot:device_list")


class DeviceUpdateView(RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = IoTDevice
    slug_field = "device_id"
    slug_url_kwarg = "device_id"
    form_class = IoTDeviceForm
    template_name = "iot/device_form.html"
    success_url = reverse_lazy("iot:device_list")


class EnvironmentalDashboardView(LoginRequiredMixin, ListView):
    """Current readings + entry point to historical charts."""

    model = SensorReading
    template_name = "iot/environment.html"
    context_object_name = "readings"
    paginate_by = 30

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(farm__in=farms_for_user(self.request.user))
            .select_related("device", "pen")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["devices"] = IoTDevice.objects.filter(
            farm__in=farms_for_user(self.request.user)
        )
        return ctx


class ActuatorEventListView(LoginRequiredMixin, ListView):
    model = ActuatorEvent
    template_name = "iot/actuator_list.html"
    context_object_name = "events"
    paginate_by = 30

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(farm__in=farms_for_user(self.request.user))
            .select_related("device", "pen")
        )


def sensor_chart_data(request):
    """JSON time-series for Chart.js (hourly averages over a date range).

    Query params: device (device_id), metric (temperature|humidity|gas),
    days (int, default 7).
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth required"}, status=403)
    allowed = farms_for_user(request.user)
    qs = SensorReading.objects.filter(farm__in=allowed, quality=SensorReading.Quality.GOOD)

    device_id = request.GET.get("device")
    if device_id:
        qs = qs.filter(device__device_id=device_id)

    try:
        days = min(int(request.GET.get("days", 7)), 90)
    except ValueError:
        days = 7
    since = timezone.now() - timedelta(days=days)
    qs = qs.filter(server_timestamp__gte=since)

    metric = request.GET.get("metric", "temperature")
    field = {
        "temperature": "temperature_c",
        "humidity": "humidity_pct",
        "gas": "gas_risk_value",
    }.get(metric, "temperature_c")

    rows = (
        qs.annotate(bucket=TruncHour("server_timestamp"))
        .values("bucket")
        .annotate(value=Avg(field))
        .order_by("bucket")
    )
    labels = [r["bucket"].strftime("%Y-%m-%d %H:%M") for r in rows]
    values = [round(r["value"], 2) if r["value"] is not None else None for r in rows]
    return JsonResponse({"labels": labels, "values": values, "metric": metric})


# -- Thresholds ----------------------------------------------------------
class ThresholdListView(RoleRequiredMixin, ListView):
    allowed_roles = MANAGE
    model = EnvironmentalThreshold
    template_name = "iot/threshold_list.html"
    context_object_name = "thresholds"

    def get_queryset(self):
        return super().get_queryset().filter(farm__in=farms_for_user(self.request.user))


class ThresholdCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = EnvironmentalThreshold
    form_class = EnvironmentalThresholdForm
    template_name = "iot/threshold_form.html"
    success_url = reverse_lazy("iot:threshold_list")


class ThresholdUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = EnvironmentalThreshold
    form_class = EnvironmentalThresholdForm
    template_name = "iot/threshold_form.html"
    success_url = reverse_lazy("iot:threshold_list")
