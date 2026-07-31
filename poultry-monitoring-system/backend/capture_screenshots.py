"""Capture real screenshots of the running app into the dissertation figures.

Logs in as demo_admin, visits each page, and saves PNGs to figures/screenshots/
using the canonical filenames the dissertation expects (auto-render on drop-in).

Run with the server up:
    python capture_screenshots.py
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Use the full Chromium build (headless-shell may still be downloading).
_CHROME = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright" / "chromium-1228" / "chrome-win64" / "chrome.exe"
LAUNCH_KW = {"headless": True}
if _CHROME.exists():
    LAUNCH_KW["executable_path"] = str(_CHROME)

BASE = "http://127.0.0.1:8000"
USER, PW = "demo_admin", "DemoPass123!"
# figures/screenshots at the dissertation root (…/Ken's Masters Project/)
# backend -> poultry-monitoring-system -> Ken's Masters Project == parents[2]
OUT = Path(__file__).resolve().parents[2] / "figures" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

# (filename, path, full_page)
PAGES = [
    ("web_dashboard.png", "/", True),
    ("web_farms.png", "/farms/", True),
    ("web_batches.png", "/flocks/", True),
    ("web_mortality.png", "/flocks/mortality/add/", False),
    ("web_feed.png", "/feeding/add/", False),
    ("web_health.png", "/health/", True),
    ("web_inventory.png", "/inventory/", True),
    ("web_expenses.png", "/finance/expenses/", True),
    ("web_sales.png", "/finance/sales/", True),
    ("web_iot.png", "/monitoring/devices/", True),
    ("web_charts.png", "/monitoring/environment/", True),
    ("web_reports.png", "/reports/", True),
    ("web_alert.png", "/alerts/", True),
    ("web_ai_review.png", "/vision/", True),
]


def main():
    saved = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**LAUNCH_KW)
        ctx = browser.new_context(viewport={"width": 1366, "height": 900})
        page = ctx.new_page()

        # Login
        page.goto(f"{BASE}/accounts/login/", wait_until="networkidle")
        page.screenshot(path=str(OUT / "web_login.png"))
        saved.append("web_login.png")
        page.fill("#id_username", USER)
        page.fill("#id_password", PW)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        for name, path, full in PAGES:
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(700)  # let Chart.js render
                page.screenshot(path=str(OUT / name), full_page=full)
                saved.append(name)
                print("captured", name)
            except Exception as exc:  # noqa: BLE001
                print("FAILED", name, "->", str(exc)[:100])

        # Mobile view of the dashboard
        mob = ctx.new_page()
        mob.set_viewport_size({"width": 390, "height": 844})
        try:
            mob.goto(f"{BASE}/", wait_until="networkidle")
            mob.wait_for_timeout(500)
            mob.screenshot(path=str(OUT / "web_mobile.png"), full_page=True)
            saved.append("web_mobile.png")
            print("captured web_mobile.png")
        except Exception as exc:  # noqa: BLE001
            print("FAILED web_mobile.png ->", str(exc)[:100])

        browser.close()

    # Duplicate login + dashboard to the Chapter-3 inline names (p10/p11).
    import shutil
    for src, dst in [("web_login.png", "p10_web_login.png"),
                     ("web_dashboard.png", "p11_web_dashboard.png")]:
        if (OUT / src).exists():
            shutil.copy2(OUT / src, OUT / dst)
            saved.append(dst)

    print(f"\nSaved {len(saved)} screenshots to {OUT}")
    return 0 if len(saved) >= 10 else 1


if __name__ == "__main__":
    sys.exit(main())
