"""Vision class-mapping, prediction review immutability, and report/CSV tests."""
import uuid

import pytest
from apps.vision.class_mapping import map_class
from apps.vision.models import VisionResult
from apps.vision.services import process_vision_result
from django.test import Client

pytestmark = pytest.mark.django_db


def test_class_mapping_known_class():
    entry = map_class("slipped_tendon")
    assert entry["risk_category"] == "mobility_abnormality"
    assert entry["severity"] == "critical"


def test_class_mapping_unknown_is_uncertain():
    entry = map_class("does_not_exist")
    assert entry["risk_category"] == "uncertain"


def _make_result(farm, pen, batch, cls="lethargic", conf=0.8):
    return VisionResult.objects.create(
        farm=farm, pen=pen, batch=batch, predicted_class=cls, confidence=conf,
        result_uuid=uuid.uuid4(), detections=[{"cls": cls, "confidence": conf}],
    )


def test_process_vision_result_sets_risk(farm, pen, batch):
    r = _make_result(farm, pen, batch)
    process_vision_result(r)
    r.refresh_from_db()
    assert r.risk_category == "inactive_or_lethargic"


def test_review_preserves_original_prediction(farm, pen, batch, vet):
    vet.assigned_farms.add(farm)
    r = _make_result(farm, pen, batch, cls="lethargic", conf=0.8)
    c = Client()
    c.force_login(vet)
    resp = c.post(
        f"/vision/{r.result_uuid}/review/",
        {"decision": "correct", "corrected_class": "healthy", "review_notes": "looks fine"},
    )
    assert resp.status_code == 302
    r.refresh_from_db()
    # Original prediction is untouched; correction stored separately.
    assert r.predicted_class == "lethargic"
    assert r.corrected_class == "healthy"
    assert r.effective_class == "healthy"
    assert r.review_status == VisionResult.ReviewStatus.CORRECTED
    assert r.reviewed_by == vet


def test_csv_export(manager, farm, batch):
    manager.assigned_farms.add(farm)
    from apps.flocks.models import MortalityRecord

    MortalityRecord.objects.create(batch=batch, quantity=3)
    c = Client()
    c.force_login(manager)
    resp = c.get("/reports/mortality/?export=csv")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/csv"
    assert b"Quantity" in resp.content


def test_worker_blocked_from_sales_report(worker, farm):
    worker.assigned_farms.add(farm)
    c = Client()
    c.force_login(worker)
    resp = c.get("/reports/sales/")
    assert resp.status_code == 403


def test_healthz_endpoint():
    c = Client()
    resp = c.get("/healthz/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
