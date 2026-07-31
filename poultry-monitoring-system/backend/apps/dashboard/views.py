"""Main dashboard with role-aware aggregated metrics."""
from datetime import timedelta

from apps.alerts.models import Alert
from apps.alerts.services import alerts_visible_to
from apps.farms.services import farms_for_user
from apps.feeding.models import FeedUsage
from apps.finance.models import Expense, Sale
from apps.flocks.models import Batch, MortalityRecord
from apps.inventory.models import InventoryItem
from apps.iot.models import IoTDevice, SensorReading
from apps.vision.models import VisionResult
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        farms = farms_for_user(user)
        today = timezone.localdate()

        active_batches = Batch.objects.filter(farm__in=farms, status=Batch.Status.ACTIVE)
        ctx["active_batch_count"] = active_batches.count()
        ctx["current_population"] = sum(b.current_quantity for b in active_batches)

        mortality_today = (
            MortalityRecord.objects.filter(batch__farm__in=farms, record_date=today)
            .aggregate(t=Sum("quantity"))["t"]
            or 0
        )
        cumulative_mortality = (
            MortalityRecord.objects.filter(batch__farm__in=farms)
            .aggregate(t=Sum("quantity"))["t"]
            or 0
        )
        total_placed = sum(b.total_entries + b.total_transfers_in for b in active_batches)
        ctx["mortality_today"] = mortality_today
        ctx["cumulative_mortality"] = cumulative_mortality
        ctx["mortality_rate"] = (
            round(100.0 * cumulative_mortality / total_placed, 2) if total_placed else 0.0
        )

        ctx["feed_today_kg"] = (
            FeedUsage.objects.filter(batch__farm__in=farms, record_date=today)
            .aggregate(t=Sum("quantity_kg"))["t"]
            or 0
        )

        open_alerts = alerts_visible_to(user).filter(
            status__in=[Alert.Status.NEW, Alert.Status.ACKNOWLEDGED, Alert.Status.INVESTIGATING]
        )
        ctx["critical_alert_count"] = open_alerts.filter(severity="critical").count()
        ctx["open_alert_count"] = open_alerts.count()
        ctx["recent_alerts"] = open_alerts.select_related("farm")[:8]

        # Environmental summary from the last 24h of good readings.
        since = timezone.now() - timedelta(hours=24)
        readings = SensorReading.objects.filter(
            farm__in=farms, quality=SensorReading.Quality.GOOD, server_timestamp__gte=since
        )
        ctx["env_summary"] = {
            "temperature": _avg(readings, "temperature_c"),
            "humidity": _avg(readings, "humidity_pct"),
            "gas_risk": _avg(readings, "gas_risk_value"),
            "count": readings.count(),
        }

        devices = IoTDevice.objects.filter(farm__in=farms)
        online = sum(1 for d in devices if d.is_online)
        ctx["devices_online"] = online
        ctx["devices_offline"] = devices.count() - online

        ctx["recent_predictions"] = (
            VisionResult.objects.filter(farm__in=farms).select_related("farm")[:8]
        )

        ctx["low_stock_items"] = [
            i for i in InventoryItem.objects.filter(farm__in=farms, is_active=True)
            if i.is_low_stock
        ][:8]

        # Finance summary only for authorised roles.
        if user.is_superuser or user.has_any_role(("ADMIN", "OWNER", "MANAGER")):
            month_start = today.replace(day=1)
            ctx["show_finance"] = True
            ctx["sales_month"] = (
                Sale.objects.filter(
                    farm__in=farms, status=Sale.Status.CONFIRMED, sale_date__gte=month_start
                ).aggregate(t=Sum("unit_price"))["t"]
                or 0
            )
            ctx["expenses_month"] = (
                Expense.objects.filter(farm__in=farms, expense_date__gte=month_start)
                .aggregate(t=Sum("amount"))["t"]
                or 0
            )
        else:
            ctx["show_finance"] = False

        return ctx


def _avg(qs, field):
    from django.db.models import Avg

    val = qs.aggregate(v=Avg(field))["v"]
    return round(val, 1) if val is not None else None
