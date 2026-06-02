"""Companion (off-match) post builders.

Outside of actual matchday posts, the bot publishes "filler" content to
keep the feed alive and build pre-tournament hype:

    - countdown : J-X daily teaser, one per day until kickoff.
    - nation    : profile of each of the 48 qualified nations.
    - stadium   : showcase of each of the 16 host venues.
    - group     : preview of each of the 12 groups.

Each builder returns a dict matching its template's data contract.
The Playwright renderer picks the matching HTML template via `post_type`.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import config
import wc_data

# ---------------------------------------------------------------------------
# Tournament reference dates
# ---------------------------------------------------------------------------
WC_OPENER_DATE = date(2026, 6, 11)
WC_FINAL_DATE = date(2026, 7, 19)
WC_OPENER = {
    "home": {"tla": "MEX", "code": "mx", "name": "Mexico", "short": "MEX"},
    "away": {"tla": "RSA", "code": "za", "name": "South Africa", "short": "RSA"},
    "venue": "Estadio Azteca",
    "city": "Mexico City",
    "country": "Mexico",
    "kickoff_utc_label": "19:00 UTC",
    "kickoff_local_label": "13:00 CDT",
}


# ===========================================================================
# COUNTDOWN
# ===========================================================================
# One distinct background gradient per countdown day so the series feels alive
# in the feed. All picks tested to keep white text + gold logo legible.
_COUNTDOWN_PALETTE = {
    10: ("#1B2A4E", "#3D2A6C"),  # deep navy → indigo
    9:  ("#2D1B4E", "#5A1B7A"),  # purple → magenta
    8:  ("#0F3D2E", "#1F5D45"),  # forest → emerald
    7:  ("#0E2A47", "#1E5A8C"),  # navy → royal blue
    6:  ("#4A1F0E", "#7A3F1E"),  # burnt orange → amber
    5:  ("#4E0F2E", "#7A1F45"),  # wine → magenta
    4:  ("#0E3D4E", "#1F6E7A"),  # dark teal → cyan
    3:  ("#4E0F0F", "#7A1F1F"),  # blood red → burgundy
    2:  ("#3A2E0E", "#7A5F1F"),  # bronze → dark gold
    1:  ("#1A1A1A", "#3D3D3D"),  # charcoal → slate (anticipation)
    0:  ("#0B0B0B", "#C9A227"),  # black → trophy gold (the day)
}


def build_countdown_post(target_date: date | None = None) -> dict | None:
    """Build the countdown payload for `target_date` (defaults to today).

    Single-slide hero: huge day count, "DAYS TO GO", kickoff date.
    Returns None outside the J-10 .. J-0 window (no countdown posts otherwise).

    The env var WCBOT_SIMULATE_DATE (YYYY-MM-DD) overrides "today" — handy
    when running the workflow on past/future days for testing.
    """
    if target_date is None:
        import os
        sim = os.getenv("WCBOT_SIMULATE_DATE")
        if sim:
            try:
                target_date = date.fromisoformat(sim)
            except ValueError:
                pass
        target_date = target_date or date.today()
    days_left = (WC_OPENER_DATE - target_date).days
    if days_left < 0 or days_left > 10:
        return None

    bg = _COUNTDOWN_PALETTE.get(days_left, _COUNTDOWN_PALETTE[10])
    label = "KICKOFF DAY" if days_left == 0 else (
        "1 DAY TO GO" if days_left == 1 else f"{days_left} DAYS TO GO"
    )

    return {
        "post_id": f"WC2026-CD-{days_left:02d}",
        "post_type": "countdown",
        "days_to_kickoff": days_left,
        "days_label": label,
        "kickoff_date": WC_OPENER_DATE.isoformat(),
        "kickoff_date_label": WC_OPENER_DATE.strftime("%B %d, %Y").upper(),
        "bg_color_top": bg[0],
        "bg_color_bottom": bg[1],
    }


# ===========================================================================
# NATION
# ===========================================================================
def build_nation_post(tla: str) -> dict | None:
    """Profile payload for one nation. None if the TLA isn't in NATIONS."""
    tla = tla.upper()
    if tla not in wc_data.NATIONS:
        return None
    ref = wc_data.NATIONS[tla]
    stars = wc_data.stars_for(tla)
    return {
        "post_id": f"WC2026-N-{tla}",
        "post_type": "nation",
        "tla": tla,
        "code": ref["a2"],
        "name": _nation_name(tla),
        "fifa_rank": ref["rank"],
        "squad_value_eur_m": ref["value"],
        "players_top5_leagues": ref["top5"],
        "key_players": [{**s, "photo_url": None} for s in stars],
    }


def _nation_name(tla: str) -> str:
    """Display name from the TLA (the live match flow uses football-data names)."""
    return TLA_DISPLAY.get(tla, tla.title())


TLA_DISPLAY: dict[str, str] = {
    "ARG": "Argentina", "FRA": "France", "ESP": "Spain", "ENG": "England", "BRA": "Brazil",
    "POR": "Portugal", "NED": "Netherlands", "GER": "Germany", "BEL": "Belgium", "CRO": "Croatia",
    "URY": "Uruguay", "COL": "Colombia", "MAR": "Morocco", "USA": "United States", "SUI": "Switzerland",
    "JPN": "Japan", "SEN": "Senegal", "MEX": "Mexico", "AUT": "Austria", "SWE": "Sweden",
    "TUR": "Turkey", "AUS": "Australia", "CIV": "Ivory Coast", "EGY": "Egypt", "NOR": "Norway",
    "SCO": "Scotland", "PAR": "Paraguay", "TUN": "Tunisia", "CZE": "Czechia", "ALG": "Algeria",
    "PAN": "Panama", "GHA": "Ghana", "COD": "DR Congo", "IRN": "Iran", "KSA": "Saudi Arabia",
    "QAT": "Qatar", "JOR": "Jordan", "IRQ": "Iraq", "UZB": "Uzbekistan", "RSA": "South Africa",
    "BIH": "Bosnia-Herzegovina", "CPV": "Cape Verde", "HAI": "Haiti", "NZL": "New Zealand",
    "CUW": "Curaçao", "KOR": "South Korea", "ECU": "Ecuador", "CAN": "Canada",
}


# ===========================================================================
# STADIUM
# ===========================================================================
def build_stadium_post(name: str) -> dict | None:
    """Showcase payload for one venue. None if the stadium isn't in VENUES."""
    v = wc_data.venue(name)
    if not v:
        return None
    return {
        "post_id": f"WC2026-S-{name.replace(' ', '_')}",
        "post_type": "stadium",
        "stadium": name,
        "city": v["city"],
        "country": v["country"],
        "capacity": v["capacity"],
        "image_url": v.get("img"),
        "lat": v["lat"],
        "lon": v["lon"],
    }


# ===========================================================================
# GROUP
# ===========================================================================
def build_group_post(group_letter: str) -> dict | None:
    """Preview payload for one of the 12 groups."""
    group_letter = group_letter.upper()
    # Tla list per group, mirrored from official schedule (matches our venue map)
    members = GROUP_MEMBERS.get(group_letter)
    if not members:
        return None
    teams = []
    for tla in members:
        ref = wc_data.NATIONS.get(tla, {})
        teams.append({
            "tla": tla,
            "code": ref.get("a2"),
            "name": _nation_name(tla),
            "fifa_rank": ref.get("rank"),
            "squad_value_eur_m": ref.get("value"),
        })
    teams.sort(key=lambda t: t.get("fifa_rank") or 99)
    return {
        "post_id": f"WC2026-G-{group_letter}",
        "post_type": "group",
        "group": group_letter,
        "teams": teams,
    }


GROUP_MEMBERS: dict[str, list[str]] = {
    "A": ["MEX", "RSA", "KOR", "CZE"],
    "B": ["CAN", "QAT", "SUI", "BIH"],
    "C": ["BRA", "MAR", "HAI", "SCO"],
    "D": ["USA", "PAR", "AUS", "TUR"],
    "E": ["GER", "CUW", "CIV", "ECU"],
    "F": ["NED", "JPN", "SWE", "TUN"],
    "G": ["BEL", "EGY", "IRN", "NZL"],
    "H": ["ESP", "CPV", "KSA", "URY"],
    "I": ["FRA", "SEN", "NOR", "IRQ"],
    "J": ["AUT", "JOR", "ARG", "ALG"],
    "K": ["POR", "COD", "UZB", "COL"],
    "L": ["ENG", "CRO", "GHA", "PAN"],
}


# ===========================================================================
# CLI
# ===========================================================================
if __name__ == "__main__":
    import json, sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    today = date.today()
    print("=== COUNTDOWN today ===")
    print(json.dumps(build_countdown_post(today), ensure_ascii=False, indent=2))
    print()
    print("=== NATION FRA ===")
    print(json.dumps(build_nation_post("FRA"), ensure_ascii=False, indent=2))
    print()
    print("=== STADIUM MetLife ===")
    print(json.dumps(build_stadium_post("MetLife Stadium"), ensure_ascii=False, indent=2))
    print()
    print("=== GROUP I ===")
    print(json.dumps(build_group_post("I"), ensure_ascii=False, indent=2))
