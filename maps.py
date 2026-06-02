"""Generate a dark-themed country locator map (country shape + red stadium dot).

Free, no API key: country borders come from the public johan/world.geo.json
dataset; rendering is done with Pillow so it matches the slide theme. The map
is cached per stadium so we only build it once.

Usage:
    from maps import stadium_map
    path = stadium_map("Estadio Azteca", "MEX", lat, lon)  # → PNG path
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import requests
from PIL import Image, ImageDraw

import config

GEO_URL = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/{code}.geo.json"
MAPS_DIR = config.SERIES_DIR / "assets" / "maps"

# Theme — optimised for 78×78 icon rendering on slide 2.
# The CSS gives `object-fit:contain` inside a 78×78 box, so we use a square
# canvas at 4× retina (312×312) with thick strokes and a bold dot.
BG = (0, 0, 0, 0)                 # transparent — CSS provides the backdrop
LAND = (255, 255, 255, 60)        # land fill (visible at icon size)
LAND_EDGE = (244, 196, 48, 255)   # gold outline (full opacity, thick stroke)
DOT = (230, 57, 70, 255)          # red dot
DOT_RING = (255, 255, 255, 255)   # white halo
EDGE_WIDTH = 8                    # outline thickness (≈2px at 78×78)

# Square canvas at 4× the display size (78×78 → 312×312).
W, H = 312, 312
PAD = 16


def stadium_map(stadium: str, country_code3: str, lat: float, lon: float,
                force: bool = False) -> Path | None:
    """Render (and cache) a locator map. Returns the PNG path, or None on failure."""
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    safe = stadium.replace(" ", "_").replace("'", "").replace("&", "and")
    out = MAPS_DIR / f"{safe}.png"
    if out.exists() and not force:
        return out

    polys = _country_polygons(country_code3)
    if not polys:
        return None

    # Render at 2x then downsample for clean anti-aliased edges at icon size.
    ss = 2
    Wx, Hx = W * ss, H * ss
    view = _view_bbox(polys, lat, lon)
    img = Image.new("RGBA", (Wx, Hx), BG)
    draw = ImageDraw.Draw(img)

    project = _projector(view, Wx, Hx, PAD * ss)
    # 1) Fill all polygons first (no outline) so internal edges between
    #    multipolygon rings don't paint a gold line.
    for ring in polys:
        pts = [project(lon_, lat_) for lon_, lat_ in ring]
        if len(pts) >= 3:
            draw.polygon(pts, fill=LAND)
    # 2) Then trace the outline on top.
    for ring in polys:
        pts = [project(lon_, lat_) for lon_, lat_ in ring]
        if len(pts) >= 3:
            draw.line(pts + [pts[0]], fill=LAND_EDGE, width=EDGE_WIDTH * ss, joint="curve")

    # Stadium marker — sized to read clearly at 78×78 display.
    x, y = project(lon, lat)
    r_out, r_in = 36, 22
    draw.ellipse((x - r_out, y - r_out, x + r_out, y + r_out), fill=DOT_RING)
    draw.ellipse((x - r_in, y - r_in, x + r_in, y + r_in), fill=DOT)

    img = img.resize((W, H), Image.LANCZOS)
    img.save(out, "PNG")
    return out


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _country_polygons(code3: str) -> list[list[tuple[float, float]]]:
    """Return a list of outer rings (each a list of (lon, lat))."""
    cache = MAPS_DIR / f"_geo_{code3}.json"
    try:
        if cache.exists():
            geo = json.loads(cache.read_text(encoding="utf-8"))
        else:
            r = requests.get(GEO_URL.format(code=code3),
                             headers={"User-Agent": "WorldCupBot/1.0"}, timeout=20)
            r.raise_for_status()
            geo = r.json()
            cache.write_text(json.dumps(geo), encoding="utf-8")
    except Exception as exc:
        print(f"[warn] map geojson failed for {code3}: {exc}")
        return []

    geom = geo["features"][0]["geometry"]
    rings: list[list[tuple[float, float]]] = []
    if geom["type"] == "Polygon":
        rings.append([(c[0], c[1]) for c in geom["coordinates"][0]])
    else:  # MultiPolygon
        for poly in geom["coordinates"]:
            rings.append([(c[0], c[1]) for c in poly[0]])
    return rings


def _ring_area(ring: list[tuple[float, float]]) -> float:
    a = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def _view_bbox(polys: list[list[tuple[float, float]]], lat: float, lon: float):
    """View = bounding box of the LARGEST landmass (drops Alaska/Hawaii/islands
    that would otherwise zoom the map out and distort it), with a margin, always
    including the stadium point."""
    largest = max(polys, key=_ring_area)
    lons = [p[0] for p in largest]
    lats = [p[1] for p in largest]
    minlon, maxlon = min(lons + [lon]), max(lons + [lon])
    minlat, maxlat = min(lats + [lat]), max(lats + [lat])
    mlon = (maxlon - minlon) * 0.08 + 0.5
    mlat = (maxlat - minlat) * 0.08 + 0.5
    return (minlon - mlon, minlat - mlat, maxlon + mlon, maxlat + mlat)


def _projector(view, width: int = W, height: int = H, pad: int = PAD):
    minlon, minlat, maxlon, maxlat = view
    mean_lat = math.radians((minlat + maxlat) / 2)
    kx = math.cos(mean_lat) or 1e-6           # longitude compression by latitude
    span_x = (maxlon - minlon) * kx
    span_y = (maxlat - minlat)
    scale = min((width - 2 * pad) / span_x, (height - 2 * pad) / span_y)
    draw_w = span_x * scale
    draw_h = span_y * scale
    off_x = (width - draw_w) / 2
    off_y = (height - draw_h) / 2

    def project(lon_: float, lat_: float) -> tuple[float, float]:
        x = off_x + (lon_ - minlon) * kx * scale
        y = off_y + (maxlat - lat_) * scale   # invert Y (north up)
        return (x, y)

    return project


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import wc_data
    samples = [
        ("Estadio Azteca", "MEX"),
        ("SoFi Stadium", "USA"),
        ("BC Place", "CAN"),
    ]
    for stadium, code in samples:
        v = wc_data.venue(stadium)
        p = stadium_map(stadium, code, v["lat"], v["lon"], force=True)
        print(f"{stadium}: {p}")
