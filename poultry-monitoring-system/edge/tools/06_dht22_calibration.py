#!/usr/bin/env python3
"""Step 6 — log DHT22 readings against a reference instrument.

    python3 tools/06_dht22_calibration.py --samples 20

This produces the paired data behind the sensor-calibration figure the study
currently carries as a placeholder. At each prompt, read your reference
thermometer/hygrometer and type the values; the script records them beside the
sensor's own reading and reports the mean offset at the end.

Take the readings across the range you actually care about, not just at room
temperature — early morning, midday and after the heat lamp has been running.
Two points that are 3 degrees apart cannot evidence a calibration.
"""
import _bootstrap  # noqa: F401
import argparse
import csv
import datetime as dt
import statistics

from src.hardware.dht22 import Dht22, Dht22Error

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--pin", type=int, default=4)
ap.add_argument("--samples", type=int, default=20)
ap.add_argument("--out", default="dht22_calibration.csv")
args = ap.parse_args()


def ask(prompt):
    while True:
        raw = input(prompt).strip()
        if raw.lower() in {"s", "skip"}:
            return None
        try:
            return float(raw)
        except ValueError:
            print("  Enter a number, or 's' to skip this sample.")


sensor = Dht22(pin_bcm=args.pin)
rows = []
print(f"Logging {args.samples} paired samples. Ctrl-C to stop early.\n")
try:
    for i in range(1, args.samples + 1):
        try:
            temperature, humidity = sensor.read()
        except Dht22Error as exc:
            print(f"{i:3d}. sensor read failed ({exc}); skipping")
            continue
        print(f"{i:3d}. DHT22 reads {temperature:.1f} degC / {humidity:.1f} %RH")
        ref_t = ask("     reference temperature (degC): ")
        ref_h = ask("     reference humidity (%RH):     ")
        rows.append({
            "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
            "sensor_temp_c": temperature, "reference_temp_c": ref_t,
            "sensor_humidity_pct": humidity, "reference_humidity_pct": ref_h,
        })
except KeyboardInterrupt:
    print("\nstopped")
finally:
    sensor.close()

if not rows:
    raise SystemExit("No samples recorded.")

with open(args.out, "w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)


def offset(sensor_key, ref_key, unit):
    pairs = [(r[sensor_key], r[ref_key]) for r in rows if r[ref_key] is not None]
    if len(pairs) < 2:
        print(f"  {sensor_key}: too few paired readings to report an offset")
        return
    diffs = [s - r for s, r in pairs]
    print(f"  {sensor_key}: n={len(pairs)}  mean offset {statistics.mean(diffs):+.2f} {unit}"
          f"  (sd {statistics.pstdev(diffs):.2f})")


print(f"\nWrote {len(rows)} rows to {args.out}")
offset("sensor_temp_c", "reference_temp_c", "degC")
offset("sensor_humidity_pct", "reference_humidity_pct", "%RH")
print("\nA consistent offset is correctable in software and worth reporting.")
print("A large, varying difference means the sensor is sited badly — check it is")
print("not in the fan's draught or in direct sun.")
