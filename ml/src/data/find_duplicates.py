"""Detect duplicate / near-duplicate images via average-hash.

Usage: python -m src.data.find_duplicates --dir data/raw/broiler_rgb
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def ahash(path, size=8) -> str:
    from PIL import Image  # lazy

    with Image.open(path) as im:
        im = im.convert("L").resize((size, size))
        pixels = list(im.getdata())
    avg = sum(pixels) / len(pixels)
    bits = "".join("1" if p >= avg else "0" for p in pixels)
    return f"{int(bits, 2):0{size * size // 4}x}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    d = Path(args.dir)
    buckets = defaultdict(list)
    for p in d.rglob("*"):
        if p.suffix.lower() in IMAGE_EXT:
            try:
                buckets[ahash(p)].append(str(p.relative_to(d)))
            except Exception:  # noqa: BLE001
                pass
    dups = {h: fs for h, fs in buckets.items() if len(fs) > 1}
    print(json.dumps({"duplicate_groups": len(dups), "groups": dups}, indent=2))


if __name__ == "__main__":
    main()
