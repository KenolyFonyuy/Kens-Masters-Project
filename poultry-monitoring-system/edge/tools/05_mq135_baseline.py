#!/usr/bin/env python3
"""Step 5 — establish this sensor's clean-air baseline and its risk span.

    python3 tools/05_mq135_baseline.py --backend ads1115 --minutes 10

Needs an ANALOGUE backend (ads1115 or mcp3008); the dout comparator reports a
trip point, not a magnitude, so there is nothing to baseline.

Why per-sensor: the MQ135's resistance in clean air varies by tens of percent
between individually identical parts, and drifts with temperature, humidity and
age. A baseline copied from another unit makes the risk index meaningless. Run
this on each sensor, in the room the sensor will live in, with the house at
rest — and re-run it every few weeks.

Writes a CSV of the sampling run so the calibration figure can be plotted, and
prints the two env lines to paste into your device's env file.
"""
import _bootstrap  # noqa: F401
import argparse
import csv
import statistics
import time

from src.hardware import gas as gas_mod

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--backend", default="ads1115", choices=["ads1115", "mcp3008"])
ap.add_argument("--channel", type=int, default=0)
ap.add_argument("--minutes", type=float, default=10.0, help="clean-air sampling duration")
ap.add_argument("--warmup", type=int, default=180, help="seconds to warm the element first")
ap.add_argument("--interval", type=float, default=2.0)
ap.add_argument("--out", default="mq135_baseline.csv")
args = ap.parse_args()

backend = gas_mod.make_backend(args.backend, channel=args.channel)

print(f"Warming the element for {args.warmup}s — leave the room at rest.")
time.sleep(args.warmup)

samples = []
deadline = time.monotonic() + args.minutes * 60
print(f"Sampling clean air for {args.minutes:.0f} min...")
with open(args.out, "w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["elapsed_s", "voltage_v"])
    start = time.monotonic()
    try:
        while time.monotonic() < deadline:
            voltage = backend.read_voltage()
            samples.append(voltage)
            writer.writerow([round(time.monotonic() - start, 1), round(voltage, 4)])
            print(f"\r  n={len(samples):4d}  latest={voltage:.4f} V", end="", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n  stopped early")

if len(samples) < 5:
    raise SystemExit("\nToo few samples to characterise a baseline.")

baseline = statistics.median(samples)  # median ignores transient spikes
spread = statistics.pstdev(samples)
print(f"\n\nSamples: {len(samples)}")
print(f"  median  {baseline:.4f} V   <- the baseline")
print(f"  st.dev  {spread:.4f} V")
print(f"  range   {min(samples):.4f} - {max(samples):.4f} V")
print(f"  CSV     {args.out}")

if spread > 0.05:
    print("\nWARNING: the baseline is still moving. Either the element has not")
    print("finished warming, or the air is not actually clean. Re-run for longer.")

# The span sets what counts as full risk. Absent a reference gas source, a
# pragmatic default is a rise of about four times the baseline noise floor,
# floored so a very quiet sensor does not make the index hair-triggered.
span = max(round(baseline * 1.5, 3), 0.3)
print("\nPaste into /etc/poultry-edge.env:")
print(f"  PMS_GAS_BASELINE_V={baseline:.4f}")
print(f"  PMS_GAS_SPAN_V={span}")
print("\nThe span above is a provisional default. Tighten it once you have")
print("observed the sensor's reading during a genuine litter-ammonia episode,")
print("and record in the dissertation that it is a relative index, not ppm.")
