"""Pipeline configuration (Python side).

Visual layout, slide order, and the slide modules all live in series/
(the Claude Design template). This file only holds pipeline settings:
paths, the competition window, and publishing behaviour.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
SERIES_DIR = ROOT / "series"                 # the data-driven HTML template
TEMPLATE_HTML = SERIES_DIR / "template.html"
EXAMPLE_MATCH = SERIES_DIR / "match.example.json"
EXAMPLE_KNOCKOUT = SERIES_DIR / "match.knockout.example.json"
OUTPUT_DIR = ROOT / "output"                 # rendered PNGs, per match_id

# ---------------------------------------------------------------------------
# Competition window
# ---------------------------------------------------------------------------
COMPETITION = "FIFA World Cup 2026"
# football-data.org competition code; API-Football has its own league id.
COMPETITION_CODE = "WC"
# How far ahead main.py looks for "today's / tomorrow's" matches.
LOOKAHEAD_DAYS = 1

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
RENDER_SCALE = 2            # device_scale_factor → 2160×2700 source PNGs
DOWNSCALE_FOR_UPLOAD = True  # also write 1080×1350 copies for Instagram
UPLOAD_SIZE = (1080, 1350)

# ---------------------------------------------------------------------------
# Publishing behaviour
# ---------------------------------------------------------------------------
# The bot delivers each post to Telegram for the user to publish manually —
# there is no approval gate. PUBLISH_TARGETS / NOTIFY_AFTER_PUBLISH only matter
# if the auto-publish path in publish.py is ever wired up.
PUBLISH_TARGETS = ["instagram"]   # add "tiktok" once its API is wired
NOTIFY_AFTER_PUBLISH = False      # post-publish recap if auto-publish is enabled
