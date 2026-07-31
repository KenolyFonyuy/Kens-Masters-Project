"""Serializers for the device ingestion API."""
from apps.farms.models import Farm, Pen
from apps.flocks.models import Batch
from rest_framework import serializers

from .models import (
    ActuatorEvent,
    IoTDevice,
    SensorReading,
)


class DeviceRegisterSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    farm = serializers.SlugRelatedField(slug_field="code", queryset=Farm.objects.all())
    pen_code = serializers.CharField(required=False, allow_blank=True)
    firmware_version = serializers.CharField(required=False, allow_blank=True)
    has_camera = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs):
        pen_code = attrs.get("pen_code")
        if pen_code:
            try:
                attrs["pen"] = Pen.objects.get(farm=attrs["farm"], code=pen_code)
            except Pen.DoesNotExist:
                raise serializers.ValidationError({"pen_code": "Unknown pen for farm."})
        return attrs


class HeartbeatSerializer(serializers.Serializer):
    cpu_percent = serializers.FloatField(required=False, allow_null=True)
    memory_percent = serializers.FloatField(required=False, allow_null=True)
    disk_percent = serializers.FloatField(required=False, allow_null=True)
    cpu_temp_c = serializers.FloatField(required=False, allow_null=True)
    uptime_seconds = serializers.IntegerField(required=False, allow_null=True)
    queued_records = serializers.IntegerField(required=False, default=0)
    firmware_version = serializers.CharField(required=False, allow_blank=True)
    device_timestamp = serializers.DateTimeField(required=False, allow_null=True)


class SensorReadingSerializer(serializers.Serializer):
    reading_uuid = serializers.UUIDField()
    pen_code = serializers.CharField(required=False, allow_blank=True)
    batch_code = serializers.CharField(required=False, allow_blank=True)
    temperature_c = serializers.FloatField(required=False, allow_null=True)
    humidity_pct = serializers.FloatField(required=False, allow_null=True)
    raw_gas_value = serializers.FloatField(required=False, allow_null=True)
    gas_risk_value = serializers.FloatField(required=False, allow_null=True)
    fan_state = serializers.BooleanField(required=False, default=False)
    heater_state = serializers.BooleanField(required=False, default=False)
    sensor_status = serializers.CharField(required=False, allow_blank=True, default="ok")
    device_timestamp = serializers.DateTimeField(required=False, allow_null=True)


class ActuatorEventSerializer(serializers.Serializer):
    event_uuid = serializers.UUIDField()
    pen_code = serializers.CharField(required=False, allow_blank=True)
    actuator = serializers.ChoiceField(choices=ActuatorEvent.Actuator.choices)
    new_state = serializers.BooleanField()
    trigger = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    device_timestamp = serializers.DateTimeField(required=False, allow_null=True)


# -- Read serializers for responses --------------------------------------
class SensorReadingOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = [
            "reading_uuid", "temperature_c", "humidity_pct", "raw_gas_value",
            "gas_risk_value", "gas_risk_category", "fan_state", "heater_state",
            "quality", "server_timestamp",
        ]


class IoTDeviceSerializer(serializers.ModelSerializer):
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = IoTDevice
        fields = [
            "device_id", "name", "status", "firmware_version", "has_camera",
            "last_seen_at", "is_online",
        ]


def resolve_pen_batch(device, pen_code, batch_code):
    """Resolve pen/batch from codes within the device's farm; falls back to
    the device's configured pen."""
    pen = None
    batch = None
    if pen_code:
        pen = Pen.objects.filter(farm=device.farm, code=pen_code).first()
    if pen is None:
        pen = device.pen
    if batch_code:
        batch = Batch.objects.filter(farm=device.farm, code=batch_code).first()
    return pen, batch
