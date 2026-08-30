#!/usr/bin/env python3
"""Step 1 — read the DHT22. Wire ONLY the DHT22 before running this.

    python3 tools/01_test_dht22.py            # 10 samples on BCM4
    python3 tools/01_test_dht22.py --pin 4 --count 30

Expect a few failed reads: the DHT22 is bit-banged with no clock line, so Linux
preempting the driver mid-frame corrupts it. Anything above roughly 60% success
is normal. 0% success means wiring — check DATA is on the pin you passed, that
VCC is on 3.3 V (NOT 5 V), and that ground is shared.
"""
import _bootstrap  # noqa: F401
import argparse
import time

from src.hardware.dht22 import Dht22, Dht22Error

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--pin", type=int, default=4, help="BCM pin of the DATA line")
ap.add_argument("--count", type=int, default=10, help="number of samples")
args = ap.parse_args()

sensor = Dht22(pin_bcm=args.pin, retries=2, retry_delay=2.1)
print(f"Reading DHT22 on BCM{args.pin} — Ctrl-C to stop\n")
good = 0
try:
    for i in range(1, args.count + 1):
        try:
            temperature, humidity = sensor.read()
            good += 1
            print(f"{i:3d}. {temperature:5.1f} degC   {humidity:5.1f} %RH")
        except Dht22Error as exc:
            print(f"{i:3d}. read failed: {exc}")
        time.sleep(2.1)  # the DHT22 refuses to be polled faster than ~0.5 Hz
except KeyboardInterrupt:
    print("\nstopped")
finally:
    sensor.close()

print(f"\n{good}/{args.count} reads succeeded.")
if good == 0:
    print("Nothing read at all. Check: DATA on the right pin, VCC on 3.3 V, GND shared.")
elif good < args.count * 0.5:
    print("High failure rate. Usually a long/loose jumper or a missing pull-up.")
else:
    print("Sensor is working. Compare these against your reference thermometer,")
    print("record any offset, and move on to step 2 (relays).")
