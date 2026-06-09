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

from datetime import date, datetime, timedelta
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
def build_nation_post(tla: str, *, today: date | None = None) -> dict | None:
    """Rich payload for the 3-slide nation showcase. None if TLA unknown.

    `today` defaults to date.today() and bounds the form window — so a post
    rendered on June 14 picks up any J1 result already on the books for this
    team. Pass an explicit date for deterministic test runs.
    """
    tla = tla.upper()
    if tla not in wc_data.NATIONS:
        return None
    today = today or date.today()
    before_iso = today.isoformat()

    ref = wc_data.NATIONS[tla]
    profile = wc_data.profile_for(tla) or {}
    stars = wc_data.stars_for(tla)
    star = stars[0] if stars else None

    letter, group_members = wc_data.group_for(tla)
    fixtures = _group_fixtures_for(tla)

    # WC history is DERIVED from the match dataset (+ a curated 22-podium table),
    # never hand-typed — appearances, years, titles, best finish and the per-year
    # finish for the last 5 WCs all come from nation_history. This is what fixes
    # the Scotland-style inaccuracies.
    import nation_history
    hist = nation_history.history_for(tla)

    # Honours line: WC titles are derived (always accurate); continental cups
    # (Euro/Copa/AFCON…) stay curated — marquees in NATION_PROFILES, tier-2 in
    # CONTINENTAL_HONOURS. Strip any stale WC entry so the derived count wins.
    honours = []
    if hist["titles"]:
        honours.append({"label": "WC", "count": hist["titles"]})
    curated = (profile.get("honours") or []) + wc_data.continental_honours_for(tla)
    honours += [h for h in curated if h.get("label") != "WC"]

    # Predictor signals — keyed by the post date so any J1 result already on the
    # books shifts the strength score appropriately.
    import nation_predict
    quali = nation_predict.quali_pct(tla, before_iso)
    pred_round = nation_predict.predicted_round(tla, before_iso)

    return {
        "post_id": f"WC2026-N-{tla}",
        "post_type": "nation",
        "post_date": before_iso,
        # ---- identity ----
        "tla": tla,
        "code": ref["a2"],
        "name": _nation_name(tla),
        "nickname": profile.get("nickname"),
        "confederation": profile.get("confederation"),
        "federation_crest": wc_data.crest_for(tla),
        "colors": profile.get("colors") or {"primary": "#0b1224", "secondary": "#FFFFFF", "accent": "#E7B549"},
        # ---- group context ----
        "group_letter": letter,
        "group_members": group_members,
        "fixtures": fixtures,
        # ---- squad ----
        "fifa_rank": ref["rank"],
        "squad_value_eur_m": ref["value"],
        "avg_age": ref.get("age"),
        "star_player": {**star, "photo_url": None} if star else None,
        "players_to_watch": wc_data.players_to_watch_for(tla),
        "coach": wc_data.coach_for(tla),
        # ---- WC history (derived from dataset + curated podiums) ----
        "wc_appearances": hist["appearances"],
        "wc_best_finish": hist["best_finish"],
        "wc_titles": hist["titles"],
        "wc_history": hist["last5"],       # [{year, finish}, ...] most recent first
        "is_first_wc": hist["is_first_wc"],
        "honours": honours,
        # ---- outlook ----
        "quali_pct": quali,
        "predicted_round": pred_round,
    }


def _group_fixtures_for(tla: str) -> list[dict]:
    """All 3 group fixtures this team plays, sorted chronologically.

    Each fixture: { kickoff_utc, opponent_tla, opponent_code, opponent_name,
                    venue, matchday }
    """
    out = []
    for pair, venue_name in wc_data.GROUP_VENUES.items():
        if tla not in pair:
            continue
        opp = next(iter(pair - {tla}))
        fd_id = wc_data.GROUP_PAIR_ID.get(pair)
        kickoff = wc_data.MATCH_KICKOFF_UTC.get(fd_id) if fd_id else None
        out.append({
            "kickoff_utc": kickoff,
            "opponent_tla": opp,
            "opponent_code": wc_data.alpha2(opp),
            "opponent_name": TLA_DISPLAY.get(opp, opp.title()),
            "venue": venue_name,
        })
    out.sort(key=lambda m: m.get("kickoff_utc") or "9999")
    for i, m in enumerate(out, start=1):
        m["matchday"] = i
    return out


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
# REACTION — live result + our pre-match prediction vs reality
# ===========================================================================
def _outcome(h: int, a: int) -> str:
    return "H" if h > a else ("A" if a > h else "D")


def build_reaction_post(match_id: str, *, raw_override: dict | None = None) -> dict | None:
    """Post-match reaction payload: final score + the prediction we posted
    before the game (reproduced deterministically), with a verdict on how
    the call aged.

    Returns None if the match isn't finished yet (no score). `raw_override`
    lets tests inject a finished raw fixture without hitting the API.
    """
    import fetch_match as fm

    raw = raw_override
    if raw is None:
        raw = next((m for m in fm.list_matches() if str(m["id"]) == str(match_id)), None)
    if not raw or raw.get("status") != "FINISHED":
        return None
    ft = (raw.get("score") or {}).get("fullTime") or {}
    ah, aa = ft.get("home"), ft.get("away")
    if ah is None or aa is None:
        return None

    # Reproduce the exact pre-match prediction. fetch_match pins form to the
    # kickoff date (form_before), and predict is seeded by match_id, so this
    # returns the identical scoreline we published in the preview.
    match = fm.fetch_match(str(match_id))
    if not match:
        return None
    pred = match.get("prediction") or {}
    ph, pa = pred.get("home_score"), pred.get("away_score")

    home, away = match["home"], match["away"]
    # TLA comes straight from the raw fixture (the assembled match dict only
    # carries the alpha-2 'code', which won't key into NATION_TAGS).
    home_tla = (raw.get("homeTeam") or {}).get("tla") or (home.get("code") or "").upper()
    away_tla = (raw.get("awayTeam") or {}).get("tla") or (away.get("code") or "").upper()
    actual_o, pred_o = _outcome(ah, aa), _outcome(ph, pa)
    exact = (ah == ph and aa == pa)
    correct = (actual_o == pred_o)

    # Upset = the lower-ranked side got a result the prediction didn't give it.
    hr = home.get("fifa_rank") or 99
    ar = away.get("fifa_rank") or 99
    favourite = "H" if hr < ar else "A"
    underdog_won = (actual_o != "D" and actual_o != favourite)
    big_gap = abs(hr - ar) >= 10

    if exact:
        verdict = "nailed"
    elif correct:
        verdict = "called"
    elif underdog_won and big_gap:
        verdict = "upset"
    else:
        verdict = "missed"

    return {
        "post_id": f"WC2026-R-{match_id}",
        "post_type": "reaction",
        "match_id": str(match_id),
        "stage": match.get("stage"),
        "group": match.get("group"),
        "venue": (match.get("venue") or {}).get("stadium"),
        "kickoff_utc": match.get("kickoff_utc"),
        "home": {"name": home["name"], "code": home.get("code"),
                 "tla": home_tla, "fifa_rank": hr},
        "away": {"name": away["name"], "code": away.get("code"),
                 "tla": away_tla, "fifa_rank": ar},
        "actual": {"home": ah, "away": aa},
        "predicted": {"home": ph, "away": pa},
        "verdict": verdict,            # nailed | called | upset | missed
        "actual_outcome": actual_o,
        "winner_name": (home["name"] if actual_o == "H"
                        else away["name"] if actual_o == "A" else None),
        "loser_name": (away["name"] if actual_o == "H"
                       else home["name"] if actual_o == "A" else None),
    }


def finished_match_ids(window_start_utc, window_end_utc) -> list[str]:
    """IDs of WC matches whose kickoff+settle time falls in the given UTC
    window AND that football-data reports FINISHED. Used by the reaction cron
    to pick exactly the matches that just wrapped up."""
    import fetch_match as fm
    out = []
    for m in fm.list_matches():
        if m.get("status") != "FINISHED":
            continue
        ko = m.get("utcDate")
        if not ko:
            continue
        settle = datetime.fromisoformat(ko.replace("Z", "+00:00")) + timedelta(minutes=150)
        if window_start_utc < settle <= window_end_utc:
            out.append(str(m["id"]))
    return out


# ===========================================================================
# STADIUM
# ===========================================================================
def build_stadium_post(name: str) -> dict | None:
    """Showcase payload for one venue (3 slides).

    Returns None if the stadium isn't in VENUES. The 3-slide concept:
      v1 — hero photo + city + capacity
      v2 — host-city emblem + motif explanation
      v3 — schedule of matches at this venue + map locator
    """
    v = wc_data.venue(name)
    if not v:
        return None
    brand = wc_data.city_brand(name) or {}
    return {
        "post_id": f"WC2026-S-{name.replace(' ', '').replace(chr(39),'')}",
        "post_type": "stadium",
        "stadium": name,
        "city": v["city"],
        "country": v["country"],
        "capacity": v["capacity"],
        "image_url": v.get("img"),
        "map_url": _stadium_map_relative(name),
        "lat": v["lat"],
        "lon": v["lon"],
        "city_logo": brand.get("logo_path"),
        "logo_scale": brand.get("logo_scale"),
        "city_motif": brand.get("motif", ""),
        "matches": _matches_at_venue(name),
    }


def _stadium_map_relative(stadium: str) -> str:
    """Return the relative path Playwright can use to load the locator map."""
    safe = stadium.replace(" ", "_").replace("'", "").replace("&", "and")
    return f"assets/maps/{safe}.png"


def _matches_at_venue(stadium: str) -> list[dict]:
    """All WC 2026 fixtures hosted at this venue, sorted chronologically.

    Group matches have resolved team pairs. Knockout matches stay TBD on the
    team side but ship with their kickoff date+time so the v3 schedule slide
    still tells the full venue story (e.g. Azteca hosts R32 + R16).
    """
    from fetch_match import VENUE_BY_MATCH

    matches = []

    # Group-stage: pair → venue is the source of truth; pair → fd_id lets us
    # join with the auto-generated kickoff table.
    for pair, venue_name in wc_data.GROUP_VENUES.items():
        if venue_name != stadium:
            continue
        fd_id = wc_data.GROUP_PAIR_ID.get(pair)
        kickoff = wc_data.MATCH_KICKOFF_UTC.get(fd_id) if fd_id else None
        teams = sorted(pair)
        matches.append({
            "stage": "group",
            "kickoff_utc": kickoff,
            "teams": [
                {"tla": t, "code": wc_data.alpha2(t),
                 "name": TLA_DISPLAY.get(t, t.title()), "short": t}
                for t in teams
            ],
        })

    # Knockout fixtures: teams are unknown until the bracket fills in, but the
    # date+venue is fixed. We show them as TBD rows with a stage badge so the
    # schedule slide reflects the venue's full footprint.
    for fd_id, venue_name in VENUE_BY_MATCH.items():
        if venue_name != stadium:
            continue
        kickoff = wc_data.MATCH_KICKOFF_UTC.get(fd_id)
        stage = wc_data.MATCH_STAGE.get(fd_id, "ko")
        matches.append({
            "stage": stage,
            "kickoff_utc": kickoff,
            "teams": [
                {"tla": "TBD", "name": "TBD", "short": "TBD"},
                {"tla": "TBD", "name": "TBD", "short": "TBD"},
            ],
        })

    matches.sort(key=lambda m: m.get("kickoff_utc") or "9999")
    return matches


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
