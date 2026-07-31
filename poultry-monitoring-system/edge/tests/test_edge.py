import os
import tempfile

from src.camera import MockCamera
from src.config import EdgeConfig
from src.control_service import ControlService
from src.heartbeat import build_heartbeat
from src.inference_service import InferenceService
from src.local_queue import LocalQueue
from src.sensor_service import MockSensorAdapter


def test_mock_sensor_read():
    r = MockSensorAdapter(seed=1).read()
    assert "temperature_c" in r and "gas_risk_value" in r
    assert 0.0 <= r["gas_risk_value"] <= 1.0


def test_local_queue_idempotent():
    with tempfile.TemporaryDirectory() as d:
        q = LocalQueue(os.path.join(d, "q.db"))
        assert q.enqueue("k1", "/sensor-readings/", {"a": 1}) is True
        q.enqueue("k1", "/sensor-readings/", {"a": 2})  # duplicate ignored
        assert q.pending_count() == 1
        q.mark_sent("k1")
        assert q.pending_count() == 0
        q.close()


def test_queue_survives_reopen():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "q.db")
        q = LocalQueue(path); q.enqueue("k1", "/x/", {"a": 1}); q.close()
        q2 = LocalQueue(path)
        assert q2.pending_count() == 1  # durable across restart
        q2.close()


def test_control_fan_on_when_hot():
    c = ControlService(temp_min_c=20, temp_max_c=30)
    events = c.evaluate({"temperature_c": 35})
    assert any(e["actuator"] == "fan" and e["new_state"] for e in events)
    # no change -> no new event
    assert c.evaluate({"temperature_c": 35}) == []


def test_control_heater_on_when_cold():
    c = ControlService(temp_min_c=20, temp_max_c=30)
    events = c.evaluate({"temperature_c": 15})
    assert any(e["actuator"] == "heater" and e["new_state"] for e in events)


def test_inference_mock_payload():
    infer = InferenceService(weights="")
    payload = infer.infer(MockCamera().capture(), device_id="PI-1", pen_code="P1")
    assert payload["predicted_class"]
    assert "result_uuid" in payload
    assert 0.0 <= payload["confidence"] <= 1.0


def test_heartbeat_payload():
    hb = build_heartbeat(queued_records=5)
    assert hb["queued_records"] == 5
    assert "device_timestamp" in hb


def test_config_defaults_to_mock():
    cfg = EdgeConfig()
    assert cfg.mock in (True, False)
    assert cfg.device_id
