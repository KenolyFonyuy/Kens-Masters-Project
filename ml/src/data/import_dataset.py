"""Import / register a dataset into ml/data/raw and record provenance.

This does NOT download anything automatically: dataset licences must be
verified by a human first. It validates that a source path exists, copies it to
the raw area (preserving originals), and writes a provenance + checksum record.

Usage:
    python -m src.data.import_dataset --source /path/to/broiler_rgb --name broiler_rgb
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, help="Path to the verified source dataset")
    ap.add_argument("--name", required=True, help="Dataset name (folder under data/raw)")
    ap.add_argument("--licence", default="UNVERIFIED", help="Licence identifier (verify before use)")
    ap.add_argument("--no-copy", action="store_true", help="Only record provenance, do not copy")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"Source does not exist: {src}")

    RAW.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    dest = RAW / args.name

    if not args.no_copy:
        if dest.exists():
            raise SystemExit(f"Destination already exists (refusing to overwrite): {dest}")
        shutil.copytree(src, dest)
        target = dest
    else:
        target = src

    files = [p for p in target.rglob("*") if p.is_file()]
    checksums = {str(p.relative_to(target)): sha256_of(p) for p in files[:5000]}
    provenance = {
        "name": args.name,
        "source": str(src),
        "licence": args.licence,
        "imported_at": dt.datetime.now().isoformat(timespec="seconds"),
        "file_count": len(files),
        "checksum_sample": checksums,
        "note": "Counts are measured from disk, never fabricated. Verify licence before use.",
    }
    out = META / f"{args.name}_provenance.json"
    out.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    print(f"Imported '{args.name}': {len(files)} files. Provenance -> {out}")


if __name__ == "__main__":
    main()
