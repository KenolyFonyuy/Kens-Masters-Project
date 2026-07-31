from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_index, name="index"),
    path("mortality/", views.mortality_report, name="mortality"),
    path("feeding/", views.feeding_report, name="feeding"),
    path("batch-performance/", views.batch_performance_report, name="batch_performance"),
    path("health/", views.health_report, name="health"),
    path("vaccination/", views.vaccination_report, name="vaccination"),
    path("inventory/", views.inventory_report, name="inventory"),
    path("environmental/", views.environmental_report, name="environmental"),
    path("vision/", views.vision_report, name="vision"),
    path("alert-response/", views.alert_response_report, name="alert_response"),
    path("sales/", views.sales_report, name="sales"),
    path("expenses/", views.expense_report, name="expenses"),
]
