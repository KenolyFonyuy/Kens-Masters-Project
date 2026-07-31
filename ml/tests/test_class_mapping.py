
from src.common.class_mapping import map_class, trained_classes


def test_trained_classes_nonempty():
    classes = trained_classes()
    assert "healthy" in classes
    assert len(classes) >= 5


def test_map_known_class():
    assert map_class("slipped_tendon")["severity"] == "critical"


def test_map_unknown_class_is_uncertain():
    assert map_class("nope")["risk_category"] == "uncertain"
