from rest_framework import serializers

from .models import Alert, AlertType, Severity


class DeviceAlertSerializer(serializers.Serializer):
    """A device-raised alert (e.g. camera failure, local threshold breach)."""

    alert_type = serializers.ChoiceField(choices=AlertType.choices)
    severity = serializers.ChoiceField(choices=Severity.choices, default=Severity.WARNING)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField(required=False, allow_blank=True)
    pen_code = serializers.CharField(required=False, allow_blank=True)
    dedup_key = serializers.CharField(required=False, allow_blank=True)


class AlertOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "uid", "alert_type", "severity", "status", "source", "title",
            "message", "trigger_count", "last_triggered_at", "created_at",
        ]
