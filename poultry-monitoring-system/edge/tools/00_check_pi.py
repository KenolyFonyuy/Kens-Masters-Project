#!/usr/bin/env python3
"""Step 0 — identify the board and confirm the OS is ready. Run this FIRST.

    python3 tools/00_check_pi.py

Nothing is switched and no GPIO is claimed; this only reports. Fix everything
it marks FAIL before wiring a single component.
"""
import _bootstrap  # noqa: F401
import importlib
import pathlib
import subprocess

OK, WARN, FAIL = "  OK  ", " WARN ", " FAIL "


def line(status, label, detail=""):
    print(f"[{status}] {label}" + (f" — {detail}" if detail else ""))


def board_model():
    try:
        return pathlib.Path("/proc/device-tree/model").read_text().strip("\x00").strip()
    except OSError:
        return None


def check_board():
    model = board_model()
    if not model:
        line(FAIL, "Raspberry Pi", "not running on a Pi — these scripts need real hardware")
        return None
    line(OK, "Board", model)
    if "Pi 5" in model:
        line(WARN, "Pi 5 GPIO", "needs gpiozero on the lgpio backend; RPi.GPIO will NOT work")
    if "Pi 3" in model:
        line(WARN, "Pi 3", "fine for sensors and relays, but too slow for comfortable YOLO inference")
    return model


def check_power():
    """Under-voltage silently corrupts DHT22 frames and makes relays chatter."""
    try:
        out = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        line(WARN, "Power", "vcgencmd unavailable; check the supply is 5 V and rated for the board")
        return
    flags = int(out.split("=")[-1], 16) if "=" in out else 0
    if flags == 0:
        line(OK, "Power", "no under-voltage or throttling recorded")
    else:
        line(FAIL, "Power", f"throttled=0x{flags:x} — supply is inadequate; readings will be unreliable")


def check_interfaces():
    for name, node, hint in (
        ("I2C (for ADS1115)", "/dev/i2c-1", "enable with: sudo raspi-config nonint do_i2c 0"),
        ("SPI (for MCP3008)", "/dev/spidev0.0", "enable with: sudo raspi-config nonint do_spi 0"),
    ):
        if pathlib.Path(node).exists():
            line(OK, name, node)
        else:
            line(WARN, name, f"{node} missing — {hint}")


def check_libraries():
    required = [("gpiozero", "relays, MCP3008, digital inputs"),
                ("lgpio", "gpiozero backend for Pi 5")]
    optional = [("adafruit_dht", "DHT22"),
                ("board", "Adafruit Blinka pin map"),
                ("adafruit_ads1x15", "ADS1115 ADC"),
                ("cv2", "camera capture")]
    for mod, why in required:
        try:
            importlib.import_module(mod)
            line(OK, f"python: {mod}", why)
        except ImportError:
            line(FAIL, f"python: {mod}", f"missing — needed for {why}")
    for mod, why in optional:
        try:
            importlib.import_module(mod)
            line(OK, f"python: {mod}", why)
        except ImportError:
            line(WARN, f"python: {mod}", f"missing — only needed for {why}")


def check_i2c_scan():
    """A wired, powered ADS1115 answers at 0x48 (ADDR to GND)."""
    try:
        out = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return
    if "48" in out:
        line(OK, "ADS1115", "device answering at 0x48")
    else:
        line(WARN, "ADS1115", "nothing at 0x48 — not wired yet, or SDA/SCL swapped")


if __name__ == "__main__":
    print("=== Step 0: Raspberry Pi readiness ===\n")
    if check_board():
        check_power()
        check_interfaces()
        check_libraries()
        check_i2c_scan()
    print("\nFix every FAIL before wiring. WARN is fine if you are not using that part yet.")
