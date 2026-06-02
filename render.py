"""Pipeline wrapper around series/render_slides.py.

Keeps the Claude Design renderer untouched; adds the operational bits the
pipeline needs:
  - clean the per-match output dir first (so a removed slide can't leave a
    stale PNG behind from a previous run)
  - optionally write 1080×1350 upload copies alongside the 2160×2700 source
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import config

# series/ is a sibling package of plain scripts; import the renderer directly.
sys.path.insert(0, str(config.SERIES_DIR))
import render_slides  # noqa: E402  (path inserted above)


def render(match: dict) -> dict:
    """Render all configured slides for one match.

    Returns {"source_dir": Path, "upload_paths": [Path, ...]}.
    """
    match_id = match.get("match_id", "match")
    source_dir = config.OUTPUT_DIR / match_id

    # Clean slate — drop any stale slides from a prior render.
    if source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)

    render_slides.render_match(
        match,
        out_root=config.OUTPUT_DIR,
        scale=config.RENDER_SCALE,
    )

    source_paths = sorted(source_dir.glob("slide_*.png"))
    upload_paths = source_paths
    if config.DOWNSCALE_FOR_UPLOAD:
        upload_paths = _make_upload_copies(source_paths)

    return {"source_dir": source_dir, "upload_paths": upload_paths}


def _make_upload_copies(source_paths: list[Path]) -> list[Path]:
    """Downscale each source PNG to UPLOAD_SIZE into an `upload/` subfolder."""
    from PIL import Image

    out = []
    for src in source_paths:
        upload_dir = src.parent / "upload"
        upload_dir.mkdir(exist_ok=True)
        dst = upload_dir / src.name
        Image.open(src).resize(config.UPLOAD_SIZE, Image.LANCZOS).save(dst, "PNG", optimize=True)
        out.append(dst)
    return out


if __name__ == "__main__":
    import json
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    example = json.loads(config.EXAMPLE_MATCH.read_text(encoding="utf-8"))
    result = render(example)
    print(f"[OK] {len(result['upload_paths'])} slides → {result['source_dir']}")
