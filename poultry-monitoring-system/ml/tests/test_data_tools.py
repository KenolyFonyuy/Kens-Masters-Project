
from src.data.generate_statistics import compute
from src.data.verify_labels import validate


def _make_dataset(tmp_path):
    img_dir = tmp_path / "images"
    lbl_dir = tmp_path / "labels"
    img_dir.mkdir(); lbl_dir.mkdir()
    # create 2 tiny valid PNGs
    from PIL import Image
    for name in ["a", "b"]:
        Image.new("RGB", (16, 16)).save(img_dir / f"{name}.png")
    (lbl_dir / "a.txt").write_text("0 0.5 0.5 0.2 0.2\n")
    (lbl_dir / "b.txt").write_text("1 0.4 0.4 0.1 0.1\n")
    return img_dir, lbl_dir


def test_validate_labels_ok(tmp_path):
    img_dir, lbl_dir = _make_dataset(tmp_path)
    report = validate(img_dir, lbl_dir, num_classes=6)
    assert report["ok"] == 2
    assert report["missing_labels"] == []
    assert report["issues"] == []


def test_validate_labels_out_of_range(tmp_path):
    img_dir, lbl_dir = _make_dataset(tmp_path)
    (lbl_dir / "a.txt").write_text("99 0.5 0.5 0.2 0.2\n")
    report = validate(img_dir, lbl_dir, num_classes=6)
    assert report["issues"]


def test_statistics(tmp_path):
    img_dir, lbl_dir = _make_dataset(tmp_path)
    stats = compute(img_dir, lbl_dir, num_classes=6)
    assert stats["images"] == 2
    assert stats["total_objects"] == 2
    assert stats["class_distribution"] == {"0": 1, "1": 1}
