"""Device ingestion API tests."""
import uuid

import pytest
from apps.alerts.models import Alert
from apps.iot.models import EnvironmentalThreshold, SensorReading
from apps.vision.models import VisionResult

pytestmark = pytest.mark.django_db


def auth(client, raw):
    client.credentials(HTTP_AUTHORIZATION=f"Device {raw}")
    return client


# -- authentication -------------------------------------------------------
def test_sensor_requires_token(api_client):
    r = api_client.post("/api/v1/sensor-readings/", {}, format="json")
    assert r.status_code in (401, 403)


def test_invalid_token_rejected(api_client):
    auth(api_client, "not-a-real-token")
    r = api_client.post("/api/v1/sensor-readings/", {"reading_uuid": str(uuid.uuid4())}, format="json")
    assert r.status_code in (401, 403)


# -- sensor readings ------------------------------------------------------
def test_sensor_reading_created(api_client, device, device_token):
    auth(api_client, device_token)
    rid = str(uuid.uuid4())
    r = api_client.post(
        "/api/v1/sensor-readings/",
        {"reading_uuid": rid, "temperature_c": 27.5, "humidity_pct": 60, "gas_risk_value": 0.2},
        format="json",
    )
    assert r.status_code == 201
    assert r.json()["data"]["duplicate"] is False
    assert SensorReading.objects.filter(reading_uuid=rid).count() == 1


def test_sensor_reading_idempotent(api_client, device, device_token):
    auth(api_client, device_token)
    rid = str(uuid.uuid4())
    payload = {"reading_uuid": rid, "temperature_c": 25, "humidity_pct": 55}
    r1 = api_client.post("/api/v1/sensor-readings/", payload, format="json")
    r2 = api_client.post("/api/v1/sensor-readings/", payload, format="json")
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r2.json()["data"]["duplicate"] is True
    assert SensorReading.objects.filter(reading_uuid=rid).count() == 1


def test_invalid_temperature_flagged(api_client, device, device_token):
    auth(api_client, device_token)
    r = api_client.post(
        "/api/v1/sensor-readings/",
        {"reading_uuid": str(uuid.uuid4()), "temperature_c": 999, "humidity_pct": 60},
        format="json",
    )
    assert r.status_code == 201
    assert r.json()["data"]["quality"] == "rejected"


def test_high_temperature_raises_alert(api_client, device, device_token, farm, pen):
    EnvironmentalThreshold.objects.create(farm=farm, pen=pen, temp_max_c=30)
    auth(api_client, device_token)
    r = api_client.post(
        "/api/v1/sensor-readings/",
        {"reading_uuid": str(uuid.uuid4()), "temperature_c": 40, "humidity_pct": 60},
        format="json",
    )
    assert r.json()["data"]["alerts_raised"] >= 1
    assert Alert.objects.filter(alert_type="high_temp").exists()


def test_missing_payload_returns_400(api_client, device, device_token):
    auth(api_client, device_token)
    r = api_client.post("/api/v1/sensor-readings/", {}, format="json")
    assert r.status_code == 400
    assert r.json()["success"] is False


# -- heartbeat ------------------------------------------------------------
def test_heartbeat(api_client, device, device_token):
    auth(api_client, device_token)
    r = api_client.post("/api/v1/devices/heartbeat/", {"cpu_percent": 12.0, "queued_records": 0}, format="json")
    assert r.status_code == 200
    device.refresh_from_db()
    assert device.last_seen_at is not None


# -- vision ---------------------------------------------------------------
def test_vision_result_created_and_alert(api_client, device, device_token):
    auth(api_client, device_token)
    rid = str(uuid.uuid4())
    r = api_client.post(
        "/api/v1/vision-results/",
        {"result_uuid": rid, "predicted_class": "lethargic", "confidence": 0.8,
         "detections": [{"cls": "lethargic", "confidence": 0.8, "bbox": [1, 2, 3, 4]}]},
        format="json",
    )
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["alert_raised"] is True
    assert "disclaimer" in body
    vr = VisionResult.objects.get(result_uuid=rid)
    assert vr.risk_category == "inactive_or_lethargic"


def test_vision_healthy_no_alert(api_client, device, device_token):
    auth(api_client, device_token)
    r = api_client.post(
        "/api/v1/vision-results/",
        {"result_uuid": str(uuid.uuid4()), "predicted_class": "healthy", "confidence": 0.95},
        format="json",
    )
    assert r.json()["data"]["alert_raised"] is False


def test_vision_idempotent(api_client, device, device_token):
    auth(api_client, device_token)
    rid = str(uuid.uuid4())
    payload = {"result_uuid": rid, "predicted_class": "healthy", "confidence": 0.9}
    api_client.post("/api/v1/vision-results/", payload, format="json")
    r2 = api_client.post("/api/v1/vision-results/", payload, format="json")
    assert r2.json()["data"]["duplicate"] is True


# -- sync batch -----------------------------------------------------------
def test_sync_batch_idempotent(api_client, device, device_token):
    auth(api_client, device_token)
    key = "sync-key-1"
    record = {
        "idempotency_key": key,
        "record_type": "sensor_reading",
        "payload": {"reading_uuid": str(uuid.uuid4()), "temperature_c": 24, "humidity_pct": 50},
    }
    r1 = api_client.post("/api/v1/sync/batch/", {"records": [record]}, format="json")
    r2 = api_client.post("/api/v1/sync/batch/", {"records": [record]}, format="json")
    assert r1.json()["data"]["results"][0]["status"] == "accepted"
    assert r2.json()["data"]["results"][0]["status"] == "duplicate"


# -- configuration / thresholds ------------------------------------------
def test_get_configuration(api_client, device, device_token):
    auth(api_client, device_token)
    r = api_client.get(f"/api/v1/devices/{device.device_id}/configuration/")
    assert r.status_code == 200
    assert "sampling_interval_seconds" in r.json()["data"]["configuration"]


def test_get_thresholds(api_client, device, device_token, farm, pen):
    EnvironmentalThreshold.objects.create(farm=farm, pen=pen, temp_max_c=33)
    auth(api_client, device_token)
    r = api_client.get(f"/api/v1/devices/{device.device_id}/thresholds/")
    assert r.status_code == 200
    assert r.json()["data"]["thresholds"]["temp_max_c"] == 33


def test_device_cannot_read_other_device_config(api_client, device, device_token, other_farm):
    from apps.iot.models import IoTDevice

    other = IoTDevice.objects.create(device_id="OTHER", name="o", farm=other_farm)
    auth(api_client, device_token)
    r = api_client.get(f"/api/v1/devices/{other.device_id}/configuration/")
    assert r.status_code in (403, 404)


def test_register_requires_capability(api_client, worker, farm):
    api_client.force_authenticate(user=worker)
    r = api_client.post(
        "/api/v1/devices/register/",
        {"device_id": "NEW-1", "farm": farm.code, "name": "x"},
        format="json",
    )
    assert r.status_code == 403


def test_register_as_owner_issues_token(api_client, owner, farm):
    api_client.force_authenticate(user=owner)
    r = api_client.post(
        "/api/v1/devices/register/",
        {"device_id": "NEW-1", "farm": farm.code, "name": "x"},
        format="json",
    )
    assert r.status_code == 201
    assert "token" in r.json()["data"]
