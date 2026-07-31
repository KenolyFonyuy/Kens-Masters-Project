"""Split a dataset into train/val/test WITHOUT leakage across groups.

Frames from the same video/session must not span splits. Provide a grouping
function via --group-by {filename_prefix,parent_dir}. Copies into
data/processed/{images,labels}/{train,val,test}.

Usage:
    python -m src.data.split_dataset --images data/interim/images \
        --labels data/interim/labels --group-by parent_dir \
        --train 0.7 --val 0.15 --test 0.15 --seed 42
"""
from __future__ import annotations

import argparse
import random
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def group_key(path: Path, mode: str) -> str:
    if mode == "parent_dir":
        return path.parent.name
    # filename_prefix: text before first underscore or digit run
    stem = path.stem
    return stem.split("_")[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--images", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--group-by", choices=["parent_dir", "filename_prefix"], default="parent_dir")
    ap.add_argument("--train", type=float, default=0.7)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    images = Path(args.images)
    labels = Path(args.labels)
    groups = defaultdict(list)
    for p in images.rglob("*"):
        if p.suffix.lower() in IMAGE_EXT:
            groups[group_key(p, args.group_by)].append(p)

    keys = sorted(groups)
    random.Random(args.seed).shuffle(keys)
    n = len(keys)
    n_train = int(n * args.train)
    n_val = int(n * args.val)
    split_of = {}
    for i, k in enumerate(keys):
        split_of[k] = "train" if i < n_train else "val" if i < n_train + n_val else "test"

    counts = defaultdict(int)
    for k, imgs in groups.items():
        split = split_of[k]
        for img in imgs:
            for kind, base in (("images", images), ("labels", labels)):
                if kind == "images":
                    src = img
                    dst_dir = PROCESSED / "images" / split
                else:
                    src = labels / (img.stem + ".txt")
                    dst_dir = PROCESSED / "labels" / split
                    if not src.exists():
                        continue
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / src.name)
            counts[split] += 1
    print(f"Split by {args.group_by}: {dict(counts)} (groups={n}, no cross-split leakage)")


if __name__ == "__main__":
    main()
