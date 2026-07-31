from apps.core.api import fail, ok
from apps.core.permissions import IsDevice
from apps.farms.models import Pen
from apps.iot.services import touch_device_seen
from rest_framework import status
from rest_framework.views import APIView

from .models import Alert
from .serializers import DeviceAlertSerializer
from .services import raise_alert


class DeviceAlertView(APIView):
    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        serializer = DeviceAlertSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid device alert.", errors=serializer.errors)
        data = serializer.validated_data
        pen = None
        if data.get("pen_code"):
            pen = Pen.objects.filter(farm=device.farm, code=data["pen_code"]).first()
        pen = pen or device.pen
        alert, created = raise_alert(
            alert_type=data["alert_type"],
            severity=data["severity"],
            source=Alert.Source.SENSOR,
            title=data["title"],
            message=data.get("message", ""),
            farm=device.farm,
            pen=pen,
            device=device,
            dedup_key=data.get("dedup_key") or None,
        )
        touch_device_seen(device)
        return ok(
            {"alert_uid": str(alert.uid), "created": created, "trigger_count": alert.trigger_count},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
