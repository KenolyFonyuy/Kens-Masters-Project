"""Verify images are readable and non-corrupt (Pillow + optional OpenCV).

Usage: python -m src.data.verify_images --dir data/raw/broiler_rgb
Prints a JSON summary; never fabricates results — only reports what it finds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def verify_dir(directory: Path) -> dict:
    from PIL import Image  # lazy

    ok, corrupt = [], []
    for p in directory.rglob("*"):
        if p.suffix.lower() not in IMAGE_EXT:
            continue
        try:
            with Image.open(p) as im:
                im.verify()
            ok.append(str(p.relative_to(directory)))
        except Exception as exc:  # noqa: BLE001
            corrupt.append({"file": str(p.relative_to(directory)), "error": str(exc)})
    return {"checked": len(ok) + len(corrupt), "ok": len(ok), "corrupt": corrupt}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    if not d.exists():
        raise SystemExit(f"Directory not found: {d}")
    print(json.dumps(verify_dir(d), indent=2))


if __name__ == "__main__":
    main()
