"""Vision-result ingestion API."""
import logging

from apps.core.api import fail, ok
from apps.core.permissions import IsDevice
from apps.iot.serializers import resolve_pen_batch
from apps.iot.services import touch_device_seen
from rest_framework import status
from rest_framework.views import APIView

from .models import VisionResult
from .serializers import VisionResultIngestSerializer
from .services import process_vision_result

logger = logging.getLogger("apps.vision")


class VisionResultView(APIView):
    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        serializer = VisionResultIngestSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid vision result.", errors=serializer.errors)
        data = serializer.validated_data
        pen, batch = resolve_pen_batch(device, data.get("pen_code"), data.get("batch_code"))
        detections = data.get("detections", [])

        result, created = VisionResult.objects.get_or_create(
            result_uuid=data["result_uuid"],
            defaults={
                "device": device,
                "farm": device.farm,
                "pen": pen,
                "batch": batch,
                "model_name": data.get("model_name") or "yolo11n",
                "model_version": data.get("model_version", ""),
                "predicted_class": data["predicted_class"],
                "confidence": data["confidence"],
                "detection_count": len(detections),
                "detections": [dict(d) for d in detections],
                "image_reference": data.get("image_reference", ""),
                "device_timestamp": data.get("device_timestamp"),
            },
        )
        alert = None
        if created:
            alert = process_vision_result(result)
        touch_device_seen(device)
        return ok(
            {
                "result_uuid": str(result.result_uuid),
                "duplicate": not created,
                "risk_category": result.risk_category,
                "severity": result.severity,
                "alert_raised": alert is not None,
                "disclaimer": (
                    "Machine-vision predictions are early-warning indicators and "
                    "do not replace veterinary diagnosis."
                ),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
