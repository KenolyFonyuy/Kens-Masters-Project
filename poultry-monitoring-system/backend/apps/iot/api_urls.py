from django.urls import path

from . import api_views

urlpatterns = [
    path("devices/register/", api_views.DeviceRegisterView.as_view(), name="device-register"),
    path("devices/heartbeat/", api_views.HeartbeatView.as_view(), name="device-heartbeat"),
    path("sensor-readings/", api_views.SensorReadingView.as_view(), name="sensor-readings"),
    path("actuator-events/", api_views.ActuatorEventView.as_view(), name="actuator-events"),
    path("sync/batch/", api_views.SyncBatchView.as_view(), name="sync-batch"),
    path(
        "devices/<str:device_id>/configuration/",
        api_views.DeviceConfigurationView.as_view(),
        name="device-configuration",
    ),
    path(
        "devices/<str:device_id>/thresholds/",
        api_views.DeviceThresholdsView.as_view(),
        name="device-thresholds",
    ),
]
