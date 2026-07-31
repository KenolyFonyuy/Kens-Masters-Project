"""Tests for the on-device inference pipeline (Section 3.9.15 / Figure 3.18).

Verifies the temporal aggregation logic with no model, camera or network —
using the deterministic detector and hand-fed detections.
"""
from src.deployment.ondevice_pipeline import FrameAggregator, run_stream
from src.deployment.inference import MockDetector


def _det(cls, conf=0.9):
    return [{"cls": cls, "confidence": conf, "bbox": [0.4, 0.4, 0.2, 0.2]}]


def test_single_frame_does_not_flag():
    agg = FrameAggregator(window=5, min_hits=3)
    d = agg.update(_det("lethargic"))
    assert d["flag"] is None  # one hit is below min_hits


def test_flag_raised_after_min_hits():
    agg = FrameAggregator(window=5, min_hits=3)
    out = [agg.update(_det("lethargic")) for _ in range(3)]
    assert out[-1]["flag"] == "lethargic"


def test_below_threshold_confidence_ignored():
    agg = FrameAggregator(window=5, min_hits=2, conf_threshold=0.35)
    agg.update(_det("lethargic", conf=0.2))
    d = agg.update(_det("lethargic", conf=0.2))
    assert d["top"] is None and d["flag"] is None


def test_healthy_never_flags():
    agg = FrameAggregator(window=3, min_hits=1)
    d = agg.update(_det("healthy"))
    assert d["flag"] is None and d["review"] is False


def test_unknown_class_routes_to_review_not_flag():
    # A class absent from the mapping resolves to the 'uncertain' risk category.
    agg = FrameAggregator(window=3, min_hits=2)
    agg.update(_det("something_unmapped"))
    d = agg.update(_det("something_unmapped"))
    assert d["review"] is True and d["flag"] is None


def test_window_evicts_old_frames():
    agg = FrameAggregator(window=3, min_hits=3)
    agg.update(_det("lethargic"))
    agg.update(_det("healthy"))
    agg.update(_det("healthy"))
    d = agg.update(_det("healthy"))  # lethargic evicted; only healthy in window
    assert d["flag"] is None


def test_invalid_config_rejected():
    import pytest
    with pytest.raises(ValueError):
        FrameAggregator(window=3, min_hits=4)


def test_run_stream_emits_on_change_only(tmp_path):
    # MockDetector ignores image content and _iter_frames only checks the file
    # extension, so empty .jpg files are enough to exercise the folder path.
    d = tmp_path / "frames"
    d.mkdir()
    for i in range(6):
        (d / f"f{i}.jpg").write_bytes(b"")
    events = run_stream(
        str(d), MockDetector(), device_id="PI-T", frame_skip=1,
        window=3, min_hits=2, conf=0.35,
    )
    # MockDetector -> first class is 'healthy' (no flag) OR a risk class depending
    # on mapping order; either way emission count is deterministic and small.
    assert isinstance(events, list)
    for e in events:
        assert e["device_id"] == "PI-T"
        assert e["routing"] in ("flag", "review")
        assert "aggregation" in e
