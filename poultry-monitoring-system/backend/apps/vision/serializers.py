from rest_framework import serializers

from .models import VisionResult


class DetectionSerializer(serializers.Serializer):
    cls = serializers.CharField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    bbox = serializers.ListField(
        child=serializers.FloatField(), min_length=4, max_length=4, required=False
    )


class VisionResultIngestSerializer(serializers.Serializer):
    result_uuid = serializers.UUIDField()
    pen_code = serializers.CharField(required=False, allow_blank=True)
    batch_code = serializers.CharField(required=False, allow_blank=True)
    model_name = serializers.CharField(required=False, allow_blank=True, default="yolo11n")
    model_version = serializers.CharField(required=False, allow_blank=True)
    predicted_class = serializers.CharField()
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    detections = DetectionSerializer(many=True, required=False)
    image_reference = serializers.CharField(required=False, allow_blank=True)
    device_timestamp = serializers.DateTimeField(required=False, allow_null=True)


class VisionResultOutSerializer(serializers.ModelSerializer):
    effective_class = serializers.CharField(read_only=True)

    class Meta:
        model = VisionResult
        fields = [
            "result_uuid", "predicted_class", "confidence", "risk_category",
            "severity", "detection_count", "review_status", "corrected_class",
            "effective_class", "image_reference", "server_timestamp",
        ]
