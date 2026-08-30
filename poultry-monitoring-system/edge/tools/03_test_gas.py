#!/usr/bin/env python3
"""Step 3 — read the MQ135 through whichever backend you have wired.

    python3 tools/03_test_gas.py --backend dout       # no ADC yet
    python3 tools/03_test_gas.py --backend ads1115    # ADS1115 on I2C
    python3 tools/03_test_gas.py --backend mcp3008    # MCP3008 on SPI

The sensor needs about 3 minutes from power-on before its readings settle, and
a brand-new element needs 24 h of burn-in before its baseline stops drifting.
Readings taken before that are high and falling, and would log as a false
ammonia event.

To provoke a response safely, hold a swab of household ammonia cleaner near the
sensor — the silicone tube in your kit works well to direct the vapour without
soaking the element. Do this in a ventilated room, and never breathe it.
"""
import _bootstrap  # noqa: F401
import argparse
import time

from src.hardware import gas as gas_mod

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--backend", default="dout", choices=["dout", "ads1115", "mcp3008"])
ap.add_argument("--pin", type=int, default=22, help="BCM pin for the dout backend")
ap.add_argument("--channel", type=int, default=0, help="ADC channel for ads1115/mcp3008")
ap.add_argument("--baseline", type=float, default=0.4, help="clean-air volts (step 5 measures this)")
ap.add_argument("--span", type=float, default=1.6, help="volts above baseline that read as risk 1.0")
ap.add_argument("--count", type=int, default=30)
args = ap.parse_args()

if args.backend == "dout":
    backend = gas_mod.make_backend("dout", pin_bcm=args.pin)
    print("Backend 'dout': this reads the board's comparator, so the risk value can")
    print("only be 0.0 or 1.0. Turn the blue potentiometer to set the trip point.")
    print("Fit an ADS1115 or MCP3008 before taking readings for the results chapter.\n")
else:
    backend = gas_mod.make_backend(args.backend, channel=args.channel)

sensor = gas_mod.Mq135(backend, baseline_v=args.baseline, span_v=args.span)
print(f"Reading MQ135 via {args.backend} — Ctrl-C to stop\n")
try:
    for i in range(1, args.count + 1):
        r = sensor.read()
        bar = "#" * int(r["gas_risk_value"] * 40)
        print(f"{i:3d}. {r['raw_gas_value']:6.3f} V   risk {r['gas_risk_value']:.3f}  |{bar:<40}|")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nstopped")
finally:
    sensor.close()
