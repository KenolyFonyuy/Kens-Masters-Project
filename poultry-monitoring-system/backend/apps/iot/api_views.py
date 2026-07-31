"""Device ingestion API views (mounted under /api/v1/)."""
import logging

from apps.core.api import fail, ok
from apps.core.permissions import HasCapability, IsDevice, IsDeviceOrAuthenticatedUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import (
    ActuatorEvent,
    DeviceConfiguration,
    DeviceHeartbeat,
    DeviceToken,
    IoTDevice,
    SensorReading,
    SyncRecord,
)
from .serializers import (
    ActuatorEventSerializer,
    DeviceRegisterSerializer,
    HeartbeatSerializer,
    SensorReadingSerializer,
    resolve_pen_batch,
)
from .services import process_sensor_reading, touch_device_seen, validate_reading_values

logger = logging.getLogger("apps.iot")


class DeviceRegisterView(APIView):
    """Register (or update) a device and issue a one-time bearer token.

    Requires an authenticated user with the ``register_devices`` capability
    (admins/owners). The raw token is returned exactly once.
    """

    permission_classes = [IsAuthenticated, HasCapability]
    required_capability = "register_devices"
    throttle_scope = "device_config"

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid payload.", errors=serializer.errors)
        data = serializer.validated_data
        device, created = IoTDevice.objects.get_or_create(
            device_id=data["device_id"],
            defaults={
                "name": data.get("name") or data["device_id"],
                "farm": data["farm"],
                "pen": data.get("pen"),
                "firmware_version": data.get("firmware_version", ""),
                "has_camera": data.get("has_camera", True),
            },
        )
        if not created:
            device.farm = data["farm"]
            if data.get("pen"):
                device.pen = data["pen"]
            device.save()
        DeviceConfiguration.objects.get_or_create(device=device)
        token, raw = DeviceToken.issue(device, label="auto-issued")
        return ok(
            {
                "device_id": device.device_id,
                "created": created,
                "token": raw,  # shown ONCE; only the hash is persisted
                "token_id": str(token.pk),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class HeartbeatView(APIView):
    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        serializer = HeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid heartbeat payload.", errors=serializer.errors)
        DeviceHeartbeat.objects.create(device=device, **serializer.validated_data)
        touch_device_seen(device)
        return ok({"device_id": device.device_id, "received_at": timezone.now()})


class SensorReadingView(APIView):
    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        serializer = SensorReadingSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid sensor reading.", errors=serializer.errors)
        reading, created, alerts = _ingest_reading(device, serializer.validated_data)
        touch_device_seen(device)
        return ok(
            {
                "reading_uuid": str(reading.reading_uuid),
                "duplicate": not created,
                "quality": reading.quality,
                "gas_risk_category": reading.gas_risk_category,
                "alerts_raised": len(alerts),
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ActuatorEventView(APIView):
    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        serializer = ActuatorEventSerializer(data=request.data)
        if not serializer.is_valid():
            return fail("Invalid actuator event.", errors=serializer.errors)
        event, created = _ingest_actuator(device, serializer.validated_data)
        touch_device_seen(device)
        return ok(
            {"event_uuid": str(event.event_uuid), "duplicate": not created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class SyncBatchView(APIView):
    """Offline batch synchronisation with idempotency keys.

    Body: {"records": [{"idempotency_key", "record_type", "payload"}...]}
    record_type in {sensor_reading, actuator_event}. Replays are reported as
    duplicates and never create a second row.
    """

    permission_classes = [IsDevice]
    throttle_scope = "device_ingest"

    def post(self, request):
        device = request.device
        records = request.data.get("records")
        if not isinstance(records, list):
            return fail("'records' must be a list.")
        results = []
        for item in records:
            results.append(self._process(device, item))
        touch_device_seen(device)
        accepted = sum(1 for r in results if r["status"] == SyncRecord.Status.ACCEPTED)
        return ok({"processed": len(results), "accepted": accepted, "results": results})

    def _process(self, device, item):
        key = item.get("idempotency_key")
        rtype = item.get("record_type")
        payload = item.get("payload", {})
        if not key or not rtype:
            return {"idempotency_key": key, "status": SyncRecord.Status.REJECTED,
                    "detail": "Missing idempotency_key or record_type"}

        existing = SyncRecord.objects.filter(idempotency_key=key).first()
        if existing:
            return {"idempotency_key": key, "status": SyncRecord.Status.DUPLICATE,
                    "detail": "Already processed", "target_uuid": str(existing.target_uuid or "")}

        try:
            if rtype == "sensor_reading":
                ser = SensorReadingSerializer(data=payload)
                ser.is_valid(raise_exception=True)
                obj, _created, _alerts = _ingest_reading(device, ser.validated_data)
                target_uuid = obj.reading_uuid
            elif rtype == "actuator_event":
                ser = ActuatorEventSerializer(data=payload)
                ser.is_valid(raise_exception=True)
                obj, _created = _ingest_actuator(device, ser.validated_data)
                target_uuid = obj.event_uuid
            else:
                return {"idempotency_key": key, "status": SyncRecord.Status.REJECTED,
                        "detail": f"Unknown record_type '{rtype}'"}
        except Exception as exc:
            SyncRecord.objects.create(
                device=device, idempotency_key=key, record_type=rtype,
                status=SyncRecord.Status.REJECTED, detail=str(exc)[:255],
            )
            return {"idempotency_key": key, "status": SyncRecord.Status.REJECTED,
                    "detail": str(exc)[:255]}

        SyncRecord.objects.create(
            device=device, idempotency_key=key, record_type=rtype,
            status=SyncRecord.Status.ACCEPTED, target_uuid=target_uuid,
            device_timestamp=payload.get("device_timestamp"),
        )
        return {"idempotency_key": key, "status": SyncRecord.Status.ACCEPTED,
                "target_uuid": str(target_uuid)}


class DeviceConfigurationView(APIView):
    permission_classes = [IsDeviceOrAuthenticatedUser]
    throttle_scope = "device_config"

    def get(self, request, device_id):
        device = _get_scoped_device(request, device_id)
        config, _ = DeviceConfiguration.objects.get_or_create(device=device)
        return ok({"device_id": device.device_id, "configuration": config.as_dict()})


class DeviceThresholdsView(APIView):
    permission_classes = [IsDeviceOrAuthenticatedUser]
    throttle_scope = "device_config"

    def get(self, request, device_id):
        device = _get_scoped_device(request, device_id)
        from .services import get_threshold

        threshold = get_threshold(device.farm, device.pen)
        return ok({
            "device_id": device.device_id,
            "thresholds": threshold.as_dict() if threshold else None,
        })


# -- helpers --------------------------------------------------------------
def _get_scoped_device(request, device_id):
    device = get_object_or_404(IoTDevice, device_id=device_id)
    if getattr(request, "device", None) is not None:
        # A device may only read its own configuration.
        if request.device.pk != device.pk:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Devices may only access their own configuration.")
    return device


def _ingest_reading(device, data):
    """Idempotent creation of a sensor reading + alert processing."""
    pen, batch = resolve_pen_batch(device, data.get("pen_code"), data.get("batch_code"))
    quality, reason = validate_reading_values(
        data.get("temperature_c"), data.get("humidity_pct")
    )
    reading, created = SensorReading.objects.get_or_create(
        reading_uuid=data["reading_uuid"],
        defaults={
            "device": device,
            "farm": device.farm,
            "pen": pen,
            "batch": batch,
            "temperature_c": data.get("temperature_c"),
            "humidity_pct": data.get("humidity_pct"),
            "raw_gas_value": data.get("raw_gas_value"),
            "gas_risk_value": data.get("gas_risk_value"),
            "fan_state": data.get("fan_state", False),
            "heater_state": data.get("heater_state", False),
            "sensor_status": data.get("sensor_status", "ok"),
            "quality": quality,
            "rejection_reason": reason,
            "device_timestamp": data.get("device_timestamp"),
        },
    )
    alerts = []
    if created:
        alerts = process_sensor_reading(reading)
    return reading, created, alerts


def _ingest_actuator(device, data):
    pen, _ = resolve_pen_batch(device, data.get("pen_code"), None)
    event, created = ActuatorEvent.objects.get_or_create(
        event_uuid=data["event_uuid"],
        defaults={
            "device": device,
            "farm": device.farm,
            "pen": pen,
            "actuator": data["actuator"],
            "new_state": data["new_state"],
            "trigger": data.get("trigger", ""),
            "reason": data.get("reason", ""),
            "device_timestamp": data.get("device_timestamp"),
        },
    )
    return event, created
