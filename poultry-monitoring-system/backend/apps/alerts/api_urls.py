from django.urls import path

from . import api_views

urlpatterns = [
    path("device-alerts/", api_views.DeviceAlertView.as_view(), name="device-alerts"),
]
