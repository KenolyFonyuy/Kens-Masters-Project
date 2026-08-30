#!/usr/bin/env python3
"""Step 2 — click each relay with LEDs standing in for the mains actuators.

    python3 tools/02_test_relay.py

SAFETY: run this with NO mains load connected. LEDs on the switched side prove
the contacts move; the fan and heat lamp go on only after this passes.

You should HEAR each relay click and SEE the matching LED change. If a channel
is inverted (LED on when it should be off) the board is active-high — rerun
with --active-high and set PMS_RELAY_ACTIVE_LOW=false in your env file.
"""
import _bootstrap  # noqa: F401
import argparse
import time

from src.hardware.relays import RelayBank

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--fan-pin", type=int, default=17)
ap.add_argument("--heater-pin", type=int, default=27)
ap.add_argument("--active-high", action="store_true", help="board energises on a HIGH input")
ap.add_argument("--dwell", type=float, default=2.0, help="seconds to hold each state")
args = ap.parse_args()

bank = RelayBank(
    fan_pin=args.fan_pin,
    heater_pin=args.heater_pin,
    active_low=not args.active_high,
    interlock=False,  # tested individually here; the interlock is control-law logic
)

print(f"fan=BCM{args.fan_pin}  heater=BCM{args.heater_pin}  "
      f"active_{'high' if args.active_high else 'low'}\n")
print("Both channels should be OFF right now. Confirm before continuing.")
input("Press Enter to start the switching test... ")

try:
    for actuator in ("fan", "heater"):
        for state in (True, False):
            bank.set(actuator, state)
            print(f"  {actuator:>6} -> {'ON ' if state else 'OFF'}   "
                  f"(expect a click and the {actuator} LED to follow)")
            time.sleep(args.dwell)
    print("\nBoth channels exercised.")
except KeyboardInterrupt:
    print("\ninterrupted")
finally:
    bank.all_off()
    bank.close()
    print("Both channels de-energised.")
