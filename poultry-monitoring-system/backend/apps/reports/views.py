"""Reporting views with date filtering, search and CSV export.

Each report supports ``?export=csv`` and ``?start=YYYY-MM-DD&end=YYYY-MM-DD``.
Querysets are scoped to the farms the user can access and paginated to avoid
loading unbounded datasets.
"""
from datetime import datetime

from apps.core.export import csv_response
from apps.core.mixins import RoleRequiredMixin
from apps.farms.services import farms_for_user
from apps.feeding.models import FeedUsage
from apps.finance.models import Expense, Sale
from apps.flocks.models import Batch, MortalityRecord
from apps.health.models import HealthObservation, VaccinationRecord
from apps.inventory.models import InventoryItem
from apps.iot.models import SensorReading
from apps.vision.models import VisionResult
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render

FINANCE_ROLES = ("ADMIN", "OWNER", "MANAGER")


def _date_range(request):
    def parse(name):
        val = request.GET.get(name)
        if not val:
            return None
        try:
            return datetime.strptime(val, "%Y-%m-%d").date()
        except ValueError:
            return None

    return parse("start"), parse("end")


def _paginate(request, qs, per_page=50):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get("page"))


def reports_index(request):
    if not request.user.is_authenticated:
        from django.shortcuts import redirect

        return redirect("accounts:login")
    can_finance = request.user.is_superuser or request.user.has_any_role(FINANCE_ROLES)
    return render(request, "reports/index.html", {"can_finance": can_finance})


class _BaseReport(LoginRequiredMixin):
    template_name = "reports/report_table.html"
    title = "Report"
    headers: list[str] = []
    filename = "report.csv"

    def farms(self):
        return farms_for_user(self.request.user)

    def get_rows(self, queryset):
        raise NotImplementedError

    def get_queryset(self):
        raise NotImplementedError

    def render(self, request):
        self.request = request
        start, end = _date_range(request)
        qs = self.get_queryset()
        rows = list(self.get_rows(qs))
        if request.GET.get("export") == "csv":
            from apps.audit.models import AuditLog
            from apps.audit.services import log_action

            log_action(AuditLog.Action.EXPORT, message=f"CSV export: {self.title}")
            return csv_response(self.filename, self.headers, rows)
        page = _paginate(request, rows)
        return render(
            request,
            self.template_name,
            {
                "title": self.title,
                "headers": self.headers,
                "page_obj": page,
                "rows": page.object_list,
                "start": request.GET.get("start", ""),
                "end": request.GET.get("end", ""),
            },
        )


class MortalityReport(_BaseReport):
    title = "Mortality report"
    headers = ["Date", "Farm", "Batch", "Quantity", "Cause"]
    filename = "mortality_report.csv"

    def get_queryset(self):
        qs = MortalityRecord.objects.filter(batch__farm__in=self.farms()).select_related(
            "batch", "batch__farm"
        )
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(record_date__gte=start)
        if end:
            qs = qs.filter(record_date__lte=end)
        return qs

    def get_rows(self, qs):
        for r in qs:
            yield [r.record_date, r.batch.farm.name, r.batch.code, r.quantity, r.get_cause_display()]


class FeedingReport(_BaseReport):
    title = "Feeding report"
    headers = ["Date", "Farm", "Batch", "Feed type", "Quantity (kg)"]
    filename = "feeding_report.csv"

    def get_queryset(self):
        qs = FeedUsage.objects.filter(batch__farm__in=self.farms()).select_related(
            "batch", "batch__farm", "feed_type"
        )
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(record_date__gte=start)
        if end:
            qs = qs.filter(record_date__lte=end)
        return qs

    def get_rows(self, qs):
        for r in qs:
            yield [r.record_date, r.batch.farm.name, r.batch.code, r.feed_type.name, r.quantity_kg]


class BatchPerformanceReport(_BaseReport):
    title = "Batch performance report"
    headers = [
        "Batch", "Farm", "Status", "Start date", "Age (days)", "Placed",
        "Current", "Mortality", "Mortality %",
    ]
    filename = "batch_performance.csv"

    def get_queryset(self):
        return Batch.objects.filter(farm__in=self.farms()).select_related("farm")

    def get_rows(self, qs):
        for b in qs:
            yield [
                b.code, b.farm.name, b.get_status_display(), b.start_date, b.age_days,
                b.total_entries, b.current_quantity, b.total_mortality,
                b.cumulative_mortality_rate,
            ]


class HealthReport(_BaseReport):
    title = "Health report"
    headers = ["Date", "Farm", "Batch", "Title", "Severity", "Affected", "Reviewed"]
    filename = "health_report.csv"

    def get_queryset(self):
        qs = HealthObservation.objects.filter(batch__farm__in=self.farms()).select_related(
            "batch", "batch__farm"
        )
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(observation_date__gte=start)
        if end:
            qs = qs.filter(observation_date__lte=end)
        return qs

    def get_rows(self, qs):
        for r in qs:
            yield [
                r.observation_date, r.batch.farm.name, r.batch.code, r.title,
                r.get_severity_display(), r.affected_count,
                "yes" if r.reviewed_by_id else "no",
            ]


class VaccinationReport(_BaseReport):
    title = "Vaccination report"
    headers = ["Date", "Farm", "Batch", "Vaccine", "Quantity", "By"]
    filename = "vaccination_report.csv"

    def get_queryset(self):
        return VaccinationRecord.objects.filter(batch__farm__in=self.farms()).select_related(
            "batch", "batch__farm"
        )

    def get_rows(self, qs):
        for r in qs:
            yield [r.administered_date, r.batch.farm.name, r.batch.code, r.vaccine_name,
                   r.quantity, r.administered_by]


class InventoryReport(_BaseReport):
    title = "Inventory report"
    headers = ["Item", "Farm", "Unit", "Current stock", "Reorder level", "Low?"]
    filename = "inventory_report.csv"

    def get_queryset(self):
        return InventoryItem.objects.filter(farm__in=self.farms()).select_related("farm")

    def get_rows(self, qs):
        for i in qs:
            yield [i.name, i.farm.name, i.unit, i.current_stock, i.reorder_level,
                   "yes" if i.is_low_stock else "no"]


class EnvironmentalReport(_BaseReport):
    title = "Environmental report"
    headers = ["Timestamp", "Device", "Temp °C", "Humidity %", "Gas risk", "Category", "Quality"]
    filename = "environmental_report.csv"

    def get_queryset(self):
        qs = SensorReading.objects.filter(farm__in=self.farms()).select_related("device")
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(server_timestamp__date__gte=start)
        if end:
            qs = qs.filter(server_timestamp__date__lte=end)
        return qs[:5000]

    def get_rows(self, qs):
        for r in qs:
            yield [
                r.server_timestamp.strftime("%Y-%m-%d %H:%M"),
                r.device.device_id, r.temperature_c, r.humidity_pct,
                r.gas_risk_value, r.gas_risk_category, r.quality,
            ]


class VisionReport(_BaseReport):
    title = "Vision-result report"
    headers = ["Timestamp", "Farm", "Predicted", "Confidence", "Risk", "Review status"]
    filename = "vision_report.csv"

    def get_queryset(self):
        return VisionResult.objects.filter(farm__in=self.farms()).select_related("farm")

    def get_rows(self, qs):
        for r in qs:
            yield [
                r.server_timestamp.strftime("%Y-%m-%d %H:%M"), r.farm.name,
                r.predicted_class, round(r.confidence, 3), r.risk_category,
                r.get_review_status_display(),
            ]


class AlertResponseReport(_BaseReport):
    title = "Alert-response report"
    headers = ["Created", "Type", "Severity", "Status", "Acknowledged", "Resolved"]
    filename = "alert_response_report.csv"

    def get_queryset(self):
        from apps.alerts.services import alerts_visible_to

        return alerts_visible_to(self.request.user)

    def get_rows(self, qs):
        for a in qs:
            yield [
                a.created_at.strftime("%Y-%m-%d %H:%M"), a.get_alert_type_display(),
                a.get_severity_display(), a.get_status_display(),
                a.acknowledged_at.strftime("%Y-%m-%d %H:%M") if a.acknowledged_at else "",
                a.resolved_at.strftime("%Y-%m-%d %H:%M") if a.resolved_at else "",
            ]


class SalesReport(RoleRequiredMixin, _BaseReport):
    allowed_roles = FINANCE_ROLES
    title = "Sales report"
    headers = ["Date", "Farm", "Batch", "Quantity", "Unit price", "Total", "Status"]
    filename = "sales_report.csv"

    def get_queryset(self):
        qs = Sale.objects.filter(farm__in=self.farms()).select_related("batch", "farm")
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(sale_date__gte=start)
        if end:
            qs = qs.filter(sale_date__lte=end)
        return qs

    def get_rows(self, qs):
        for s in qs:
            yield [s.sale_date, s.farm.name, s.batch.code, s.quantity, s.unit_price,
                   s.total_amount, s.get_status_display()]


class ExpenseReport(RoleRequiredMixin, _BaseReport):
    allowed_roles = FINANCE_ROLES
    title = "Expense report"
    headers = ["Date", "Farm", "Category", "Description", "Amount"]
    filename = "expense_report.csv"

    def get_queryset(self):
        qs = Expense.objects.filter(farm__in=self.farms()).select_related("farm")
        start, end = _date_range(self.request)
        if start:
            qs = qs.filter(expense_date__gte=start)
        if end:
            qs = qs.filter(expense_date__lte=end)
        return qs

    def get_rows(self, qs):
        for e in qs:
            yield [e.expense_date, e.farm.name, e.get_category_display(), e.description, e.amount]


# Functional dispatch wrappers (class instances need a request).
def _make(view_cls):
    def view(request):
        instance = view_cls()
        # Enforce role gate for finance reports.
        if isinstance(instance, RoleRequiredMixin):
            user = request.user
            if not (user.is_authenticated and (
                user.is_superuser or user.has_any_role(view_cls.allowed_roles)
            )):
                from django.core.exceptions import PermissionDenied

                raise PermissionDenied("Not allowed.")
        instance.request = request
        return instance.render(request)

    return view


mortality_report = _make(MortalityReport)
feeding_report = _make(FeedingReport)
batch_performance_report = _make(BatchPerformanceReport)
health_report = _make(HealthReport)
vaccination_report = _make(VaccinationReport)
inventory_report = _make(InventoryReport)
environmental_report = _make(EnvironmentalReport)
vision_report = _make(VisionReport)
alert_response_report = _make(AlertResponseReport)
sales_report = _make(SalesReport)
expense_report = _make(ExpenseReport)
