#!/usr/bin/env python3
"""
render_slides.py — screenshot the World Cup template into Instagram-ready PNGs.

One match.json  ->  output/<match_id>/slide_01.png … slide_08.png  (1080×1350, 4:5).

The template renders entirely from the data object you inject as `window.__match`.
It exposes `window.WC.ready === true` once fonts, flags (flagcdn) and the radar
canvas have all settled, so we just wait on that flag before capturing.

Each slide is a `<section class="post" id="sN">` sized exactly 1080×1350 in capture
mode, so we screenshot the *element* (not the viewport) for a pixel-perfect crop.

    pip install playwright
    playwright install chromium
    python render_slides.py            # uses match.example.json

Industrialise: call render_match(match_dict) in a loop over your 104 fixtures.
"""

import json
import pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"


def render_match(match: dict, out_root: str | pathlib.Path = "output", scale: int = 2) -> pathlib.Path:
    """Render every slide for one match. `scale=2` → crisp 2160×2700 (downscale for IG)."""
    out_dir = pathlib.Path(out_root) / match.get("match_id", "match")
    out_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1120, "height": 1400},
            device_scale_factor=scale,
        )
        # Inject the data BEFORE any page script runs, so the engine auto-renders it.
        page.add_init_script(f"window.__match = {json.dumps(match, ensure_ascii=False)};")
        page.goto(f"{TEMPLATE.as_uri()}?mode=capture")

        # Wait until the engine reports everything (incl. images) is ready.
        page.wait_for_function("window.WC && window.WC.ready === true", timeout=20000)
        page.wait_for_timeout(250)  # final paint settle (radar / fonts)

        # Slide ids come from config.js (via the engine) — add/remove slides without touching Python.
        slide_ids = page.evaluate("window.WC.slideIds")
        for i, sid in enumerate(slide_ids, start=1):
            el = page.query_selector(f"#{sid}")
            if not el:
                continue
            el.screenshot(path=str(out_dir / f"slide_{i:02d}.png"))

        browser.close()
    return out_dir


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252 by default
    match = json.loads((HERE / "match.example.json").read_text(encoding="utf-8"))
    out = render_match(match)
    print(f"[OK] Slides written to {out}")
