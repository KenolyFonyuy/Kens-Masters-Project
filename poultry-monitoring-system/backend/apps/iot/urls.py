from django.urls import path

from . import views

app_name = "iot"

urlpatterns = [
    path("devices/", views.DeviceListView.as_view(), name="device_list"),
    path("devices/add/", views.DeviceCreateView.as_view(), name="device_create"),
    path("devices/<str:device_id>/", views.DeviceDetailView.as_view(), name="device_detail"),
    path("devices/<str:device_id>/edit/", views.DeviceUpdateView.as_view(), name="device_update"),
    path("environment/", views.EnvironmentalDashboardView.as_view(), name="environment"),
    path("actuators/", views.ActuatorEventListView.as_view(), name="actuator_list"),
    path("chart-data/", views.sensor_chart_data, name="sensor_chart_data"),
    path("thresholds/", views.ThresholdListView.as_view(), name="threshold_list"),
    path("thresholds/add/", views.ThresholdCreateView.as_view(), name="threshold_create"),
    path("thresholds/<uuid:uid>/edit/", views.ThresholdUpdateView.as_view(), name="threshold_update"),
]
