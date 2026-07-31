from apps.accounts.forms import StyledFormMixin
from django import forms

from .models import DeviceConfiguration, EnvironmentalThreshold, IoTDevice


class IoTDeviceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = IoTDevice
        fields = (
            "device_id", "name", "farm", "pen", "firmware_version",
            "hardware", "status", "has_camera",
        )


class DeviceConfigurationForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DeviceConfiguration
        fields = (
            "sampling_interval_seconds", "heartbeat_interval_seconds",
            "capture_interval_seconds", "inference_enabled",
            "confidence_threshold", "frame_skip",
        )


class EnvironmentalThresholdForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = EnvironmentalThreshold
        fields = (
            "farm", "pen", "temp_min_c", "temp_max_c",
            "humidity_min_pct", "humidity_max_pct",
            "gas_risk_warning", "gas_risk_critical",
        )
