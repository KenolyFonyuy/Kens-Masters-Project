
from src.deployment.inference import MockDetector, build_payload


def test_mock_detector_returns_detection():
    dets = MockDetector().predict("dummy")
    assert dets and "cls" in dets[0]


def test_build_payload_shape():
    dets = [{"cls": "lethargic", "confidence": 0.8, "bbox": [0.1, 0.1, 0.2, 0.2]},
            {"cls": "healthy", "confidence": 0.3, "bbox": [0.3, 0.3, 0.1, 0.1]}]
    payload = build_payload(dets, device_id="PI-1", pen_code="P1", batch_code="B1")
    assert payload["predicted_class"] == "lethargic"  # top confidence
    assert payload["risk_category"] == "inactive_or_lethargic"
    assert payload["device_id"] == "PI-1"
    assert 0.0 <= payload["confidence"] <= 1.0
    assert len(payload["detections"]) == 2
    assert "result_uuid" in payload


def test_build_payload_empty_detection_defaults_healthy():
    payload = build_payload([], device_id="PI-1")
    assert payload["predicted_class"] == "healthy"
    assert payload["confidence"] == 0.0
