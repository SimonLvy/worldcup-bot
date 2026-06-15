"""Build a match dict matching the series/ template contract.

DATA_MODE in .env:
  - mock : load series/match.example.json (the contract itself).
  - live : assemble from football-data.org (free) + The Odds API +
           Open-Meteo + static tables in wc_data.py.

The schema (series/match.example.json) is the single source of truth.
Prediction is computed locally (predict.py) — no paid API.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

import config
import predict
import wc_data

load_dotenv()

FD_BASE = "https://api.football-data.org/v4"
ODDS_BASE = "https://api.the-odds-api.com/v4"
METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# Nations whose name differs between football-data and The Odds API. Each entry
# is the full set of spellings for ONE nation, so matching works whichever API
# supplies the name (football-data, Odds API, etc.). Verified against both feeds
# on 2026-06-12; add a group here the moment a new mismatch shows up.
TEAM_NAME_GROUPS: list[set[str]] = [
    {"United States", "USA", "US"},
    {"Bosnia-Herzegovina", "Bosnia & Herzegovina", "Bosnia and Herzegovina"},
    {"Cape Verde Islands", "Cape Verde", "Cabo Verde"},
    {"Congo DR", "DR Congo", "Democratic Republic of Congo"},
    {"Czechia", "Czech Republic"},
    {"South Korea", "Korea Republic", "Korea"},
    {"Côte d'Ivoire", "Ivory Coast", "Cote d'Ivoire"},
    {"Curaçao", "Curacao"},
]


def _name_variants(name: str) -> set[str]:
    """All known spellings of a nation, given any one of them. Falls back to
    just the name itself if it isn't in a known mismatch group."""
    for group in TEAM_NAME_GROUPS:
        if name in group:
            return group
    return {name}


# ===========================================================================
# Public entry point
# ===========================================================================
def fetch_match(match_ref: str | None = None, target_date: date | None = None) -> dict | None:
    # Refresh the international results dataset if it's more than 23h old.
    # This ensures form data and H2H stay current throughout the tournament.
    try:
        import h2h as h2h_mod
        h2h_mod.refresh_dataset(max_age_hours=23)
    except Exception as exc:
        print(f"[warn] dataset refresh skipped: {exc!r}")

    mode = os.getenv("DATA_MODE", "mock").lower()
    match = _fetch_live(match_ref, target_date) if mode == "live" else _fetch_mock(match_ref)
    if match is None:
        return None
    _ensure_ratings(match)
    if not match.get("prediction"):
        match["prediction"] = predict.predict(match)
    return match


# ===========================================================================
# Mock
# ===========================================================================
def _fetch_mock(match_ref: str | None) -> dict:
    path = config.EXAMPLE_KNOCKOUT if (match_ref and "knockout" in match_ref.lower()) else config.EXAMPLE_MATCH
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ===========================================================================
# Live
# ===========================================================================
import time

_FD_CACHE: dict[str, dict] = {}  # in-process memoisation (path+params → json)


def _fd_get(path: str, params: dict | None = None, cache: bool = True) -> dict:
    """GET football-data with in-process caching and 429 backoff.

    The free tier allows 10 req/min. We memoise per (path, params) so a single
    match render never repeats a call, and we retry with backoff on 429 instead
    of silently failing (which previously produced empty standings/h2h slides).
    """
    key = os.getenv("FOOTBALL_DATA_API_KEY")
    if not key:
        raise RuntimeError("FOOTBALL_DATA_API_KEY missing in .env")

    cache_key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
    if cache and cache_key in _FD_CACHE:
        return _FD_CACHE[cache_key]

    last_exc: Exception | None = None
    for attempt in range(4):
        r = requests.get(f"{FD_BASE}{path}", headers={"X-Auth-Token": key},
                         params=params, timeout=25)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 0)) or (6 * (attempt + 1))
            print(f"[rate-limit] 429 on {path} — waiting {wait}s (attempt {attempt + 1}/4)")
            time.sleep(wait)
            continue
        try:
            r.raise_for_status()
        except requests.HTTPError as exc:
            last_exc = exc
            break
        data = r.json()
        if cache:
            _FD_CACHE[cache_key] = data
        return data
    raise RuntimeError(f"football-data GET {path} failed: {last_exc or 'rate-limited after retries'}")


def list_matches() -> list[dict]:
    """All 104 WC fixtures (raw football-data objects). Cached for the run."""
    return _fd_get("/competitions/WC/matches").get("matches", [])


def find_matches_on(target_date: date) -> list[dict]:
    """Raw fixtures kicking off on a given date, sorted by kickoff time so the
    daily batch always sends in chronological order regardless of the order the
    API returns them in."""
    out = []
    for m in list_matches():
        d = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).date()
        if d == target_date:
            out.append(m)
    out.sort(key=lambda m: m["utcDate"])
    return out


def _fetch_live(match_ref: str | None, target_date: date | None) -> dict | None:
    matches = list_matches()
    raw = None
    if match_ref:
        raw = next((m for m in matches if str(m["id"]) == str(match_ref)), None)
    elif target_date:
        raw = next((m for m in matches
                    if datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).date() == target_date), None)
    else:
        # Next upcoming fixture.
        now = datetime.now(timezone.utc)
        upcoming = [m for m in matches
                    if datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")) >= now]
        raw = upcoming[0] if upcoming else (matches[0] if matches else None)

    if raw is None:
        return None
    return _build_from_raw(raw)


def _build_from_raw(raw: dict) -> dict:
    fd_stage = raw.get("stage", "GROUP_STAGE")
    is_group = fd_stage == "GROUP_STAGE"
    group_letter = (raw.get("group") or "").replace("GROUP_", "") or None

    kickoff_date = raw["utcDate"][:10]
    home_raw, away_raw = raw["homeTeam"], raw["awayTeam"]
    home = _team_block(home_raw, kickoff_date)
    away = _team_block(away_raw, kickoff_date)

    kickoff_utc = raw["utcDate"]
    dt = datetime.fromisoformat(kickoff_utc.replace("Z", "+00:00"))

    venue = _venue_block(raw)
    # Local stadium time: shift UTC by the venue's offset so both the time
    # label AND the displayed date are correct (a 01:00 UTC match in Mexico
    # is the previous evening locally).
    offset, tz_label = wc_data.tz_for(venue["stadium"])
    local_dt = dt + timedelta(hours=offset)
    kickoff_local = local_dt.strftime("%Y-%m-%dT%H:%M:%S") + f"{offset:+03d}:00"
    kickoff_local_label = f"{local_dt.strftime('%H:%M')} {tz_label}"
    kickoff_utc_label = f"{dt.strftime('%H:%M')} UTC"

    match: dict = {
        "match_id": f"WC2026-{('G' + group_letter) if group_letter else 'KO'}-{raw['id']}",
        "competition": config.COMPETITION,
        "stage": "group" if is_group else "knockout",
        "kickoff_utc": kickoff_utc,
        "kickoff_local": kickoff_local,
        "kickoff_local_label": kickoff_local_label,
        "kickoff_utc_label": kickoff_utc_label,
        "venue": venue,
        "weather": None,
        "home": home,
        "away": away,
        "head_to_head": _h2h_block(home["name"], away["name"], kickoff_utc[:10], raw["id"], home_raw["id"]),
        "odds": _odds_block(home["name"], away["name"]),
    }

    # Weather from venue coords, if we know the stadium.
    v = wc_data.venue(match["venue"]["stadium"])
    if v:
        match["weather"] = _weather_block(v["lat"], v["lon"], dt)

    if is_group:
        match["group"] = group_letter
        match["match_number_in_group"] = raw.get("matchday")
        match["standings"] = _standings_block(group_letter)
        match["stakes"] = _stakes_block(match)
    else:
        match["knockout"] = _knockout_block(raw, home_raw, away_raw)

    # Stats + trivia computed last so they can draw on h2h, value, rank, etc.
    match["fun_stats"] = _fun_stats(match)
    match["did_you_know"] = _did_you_know(match)

    return match


def _team_block(team_raw: dict, kickoff_date: str) -> dict:
    tla = team_raw.get("tla", "")
    ref = wc_data.nation(tla)
    avg_age, squad_names = _squad_info(team_raw["id"])
    key_players = _key_players(tla, squad_names)
    return {
        "name": team_raw["name"],
        "code": ref["a2"],
        "fifa_rank": ref["rank"],
        "group_points": 0,  # filled from standings where relevant
        "last5": _form_from_fixtures(team_raw["id"], team_raw["name"], kickoff_date),
        "avg_age": avg_age,
        "squad_value_eur_m": ref["value"],
        "players_top5_leagues": ref["top5"],
        "key_players": key_players,
    }


def _squad_info(team_id: int) -> tuple[float, list[str]]:
    """Average age + player names from the (partial, free-tier) squad."""
    try:
        d = _fd_get(f"/teams/{team_id}")
    except Exception:
        return 26.5, []
    squad = d.get("squad", []) or []
    ages, names = [], []
    today = date.today()
    for p in squad:
        names.append(p.get("name", ""))
        dob = p.get("dateOfBirth")
        if dob:
            try:
                b = datetime.fromisoformat(dob).date()
                ages.append((today - b).days / 365.25)
            except ValueError:
                pass
    avg = round(sum(ages) / len(ages), 1) if ages else 26.5
    return avg, names


def _key_players(tla: str, squad_names: list[str]) -> list[dict]:
    stars = wc_data.stars_for(tla)
    if stars:
        return [{**s, "photo_url": None} for s in stars[:3]]
    # Fallback: first 3 names from the live squad (club/stat unknown).
    return [{"name": n, "club": "—", "stat": "Squad member", "photo_url": None}
            for n in squad_names[:3]] or [
        {"name": "TBD", "club": "—", "stat": "—", "photo_url": None}]


def _form_from_fixtures(team_id: int, team_name: str, kickoff_date: str) -> list[str]:
    """Last 5 W/D/L combining two sources:

    1. Pre-kickoff form from the full international dataset (friendlies included,
       everything up to the day before the fixture) — gives real pre-tournament
       form even in matchday 1.
    2. Once WC matches are in play, finished tournament fixtures are mixed in so
       form updates match-by-match during the group stage.

    The two sources are merged chronologically and we take the latest 5.
    """
    try:
        import h2h as h2h_mod
        pre = [(r, "") for r in h2h_mod.form_before(team_name, before=kickoff_date, last_n=5)]
    except Exception as exc:
        print(f"[warn] form_before failed ({exc!r})")
        pre = []

    # Also pick up any WC results already played (they appear in both sources
    # once the dataset is refreshed, but the WC fixture list is the freshest).
    wc_results = []
    for m in list_matches():
        if m.get("status") != "FINISHED":
            continue
        if m["utcDate"][:10] >= kickoff_date:
            continue
        if team_id not in (m["homeTeam"]["id"], m["awayTeam"]["id"]):
            continue
        w = m.get("score", {}).get("winner")
        date = m["utcDate"][:10]
        if w == "DRAW":
            wc_results.append(("D", date))
        elif w in ("HOME_TEAM", "AWAY_TEAM"):
            is_home = m["homeTeam"]["id"] == team_id
            won = (w == "HOME_TEAM" and is_home) or (w == "AWAY_TEAM" and not is_home)
            wc_results.append(("W" if won else "L", date))

    # Merge: prefer WC fixture data for tournament dates (dedup by date).
    wc_dates = {d for _, d in wc_results}
    combined = [(r, d) for r, d in pre if d not in wc_dates] + wc_results
    combined.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _ in combined[:5]]


def _h2h_block(home_name: str, away_name: str, before: str,
               match_id: int, home_id: int) -> dict:
    """Complete all-time head-to-head from the international results dataset
    (martj42), authoritative. Falls back to football-data only if the dataset
    module itself fails to load.
    """
    try:
        import h2h
        return h2h.head_to_head(home_name, away_name, before=before, last_n=3)
    except Exception as exc:
        print(f"[warn] dataset h2h failed ({exc!r}); falling back to football-data")

    try:
        d = _fd_get(f"/matches/{match_id}/head2head", params={"limit": 10})
    except Exception:
        return {"total": {"home_wins": 0, "draws": 0, "away_wins": 0}, "last3": []}
    agg = d.get("aggregates", {})
    ht, at = agg.get("homeTeam", {}), agg.get("awayTeam", {})
    total = {"home_wins": ht.get("wins", 0), "draws": ht.get("draws", 0),
             "away_wins": at.get("wins", 0)}
    last3 = []
    for m in (d.get("matches", []) or [])[:3]:
        sc = m.get("score", {}).get("fullTime", {})
        hs, as_ = sc.get("home"), sc.get("away")
        w = m.get("score", {}).get("winner")
        winner = "draw" if w == "DRAW" else ("home" if w == "HOME_TEAM" else "away")
        last3.append({"date": m.get("utcDate", "")[:10],
                      "competition": m.get("competition", {}).get("name", "Match"),
                      "score": f"{hs}-{as_}" if hs is not None else "-",
                      "winner": winner})
    return {"total": total, "last3": last3}


def _standings_block(group_letter: str | None) -> list[dict]:
    if not group_letter:
        return []
    # _fd_get retries on 429; a failure here now raises (instead of silently
    # producing an empty table) so the pipeline never ships a blank standings slide.
    d = _fd_get("/competitions/WC/standings")
    for g in d.get("standings", []):
        if (g.get("group") or "").endswith(group_letter):
            rows = []
            for row in g.get("table", []):
                t = row["team"]
                rows.append({
                    "pos": row["position"],
                    "code": wc_data.alpha2(t.get("tla", "")),
                    "name": t["name"],
                    "played": row["playedGames"],
                    "won": row["won"], "drawn": row["draw"], "lost": row["lost"],
                    "gd": row["goalDifference"], "points": row["points"],
                })
            return rows
    return []


def _rng_for(match: dict) -> "random.Random":
    import random
    key = str(match.get("match_id") or (match["home"]["name"] + match["away"]["name"]))
    h = 1469598103934665603
    for c in key:
        h = ((h ^ ord(c)) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def _team_standing(match: dict, code: str) -> dict | None:
    for row in match.get("standings", []) or []:
        if row.get("code") == code:
            return row
    return None


def _stakes_block(match: dict) -> dict:
    """Real, varied qualification scenarios driven by the live standings.

    Pre-tournament (everyone on 0 pts) we use opener framing; once games are
    played we reference actual points and positions. Phrasing is picked from
    seeded pools so no two matches read identically.
    """
    rng = _rng_for(match)
    home, away = match["home"]["name"], match["away"]["name"]
    hs = _team_standing(match, match["home"]["code"])
    as_ = _team_standing(match, match["away"]["code"])
    hp = hs["points"] if hs else 0
    ap = as_["points"] if as_ else 0
    played = (hs or {}).get("played", 0)

    if played == 0:
        # Matchday 1 — no points on the board yet.
        home_needs = rng.choice([
            f"A winning start would put {home} in the driver's seat.",
            f"{home} want three points to set the tone in the group.",
            f"Open with a win and {home} control their own destiny.",
        ])
        away_needs = rng.choice([
            f"{away} can announce themselves with an opening-day result.",
            f"A point or more keeps {away} firmly in the mix.",
            f"{away} will fancy a statement performance here.",
        ])
        scenarios = rng.sample([
            f"{home} win: top of the group on day one.",
            f"{away} win: the early statement nobody saw coming.",
            "A draw: honours even, all to play for in matchday two.",
            "Both groups are tight, so even one point could matter at the end.",
            "Goal difference could decide things, so a big win carries weight.",
        ], 3)
    else:
        lead = "level on points" if hp == ap else (f"{home} lead by {hp - ap}" if hp > ap else f"{away} lead by {ap - hp}")
        home_needs = rng.choice([
            f"On {hp} points, a win would all but seal {home}'s place in the last 32.",
            f"{home} ({hp} pts) know another result keeps qualification in their hands.",
            f"Three points lifts {home} clear at the top.",
        ])
        away_needs = rng.choice([
            f"{away} sit on {ap} points and need more to be sure of going through.",
            f"For {away} ({ap} pts), this is close to a must-win.",
            f"{away} can leapfrog their rivals with a victory here.",
        ])
        scenarios = rng.sample([
            f"{home} win: qualification all but confirmed.",
            f"{away} win: the group order flips on its head.",
            f"A draw: {lead}, but nothing is settled yet.",
            "Goal difference is tight, so the margin of victory matters.",
            f"With {3 - played} game(s) left, every point is heavy now.",
        ], 3)

    return {"home_needs": home_needs, "away_needs": away_needs, "scenarios": scenarios}


def _knockout_block(raw: dict, home_raw: dict, away_raw: dict) -> dict:
    """Minimal bracket: current pairing populated, rest as TBD.

    A full live bracket would stitch all knockout fixtures together; this is a
    safe starting point that renders cleanly and can be enriched later.
    """
    round_names = {
        "LAST_32": "Round of 32", "LAST_16": "Round of 16",
        "QUARTER_FINALS": "Quarter-final", "SEMI_FINALS": "Semi-final",
        "FINAL": "Final", "THIRD_PLACE": "Third-place play-off",
    }
    def team(t):
        return {"code": wc_data.alpha2(t.get("tla", "")), "name": t["name"], "short": t.get("tla", "")}
    empty_side = {"r16": [[None, None]] * 4, "qf": [[None, None]] * 2, "sf": [[None, None]]}
    left = {"r16": [[team(home_raw), team(away_raw)]] + [[None, None]] * 3,
            "qf": [[None, None]] * 2, "sf": [[None, None]]}
    return {
        "round": round_names.get(raw.get("stage", ""), "Knockout stage"),
        "bracket": {"left": left, "right": empty_side, "final": [None, None]},
    }


def _venue_block(raw: dict) -> dict:
    """Resolve the match's stadium using the official FIFA schedule maps.

    Lookup order:
      1. VENUE_BY_MATCH (manual seed by football-data id — for edge cases)
      2. GROUP_VENUES by unordered (home_tla, away_tla) — covers 72 group games
      3. KO_VENUES by (date, host_city) — covers all KO rounds
    Falls back to "Venue TBD" if none match.
    """
    # Knockouts are seeded by match_id; groups by unordered team pair.
    stadium = VENUE_BY_MATCH.get(raw["id"]) or wc_data.venue_for(
        raw["homeTeam"].get("tla", ""), raw["awayTeam"].get("tla", "")
    )

    if stadium and wc_data.venue(stadium):
        v = wc_data.venue(stadium)
        return {"stadium": stadium, "city": v["city"], "country": v["country"],
                "capacity": v["capacity"], "image_url": v.get("img"),
                "lat": v["lat"], "lon": v["lon"],
                "map_url": _map_url(stadium, v)}
    return {"stadium": "Venue TBD", "city": "", "country": "", "capacity": None,
            "image_url": None, "lat": None, "lon": None, "map_url": None}


_COUNTRY3 = {"Mexico": "MEX", "USA": "USA", "Canada": "CAN"}


def _map_url(stadium: str, v: dict) -> str | None:
    """Generate (and cache) the locator map; return a path relative to series/."""
    import maps
    code3 = _COUNTRY3.get(v["country"])
    if not code3:
        return None
    path = maps.stadium_map(stadium, code3, v["lat"], v["lon"])
    if not path:
        return None
    # Template loads via file:// relative to series/ → use a relative URL.
    return f"assets/maps/{path.name}"


def refresh_odds(match: dict) -> None:
    """Update match['odds'] with fresh odds from The Odds API.

    Call this just before publishing to ensure odds are current.
    Modifies match dict in-place; silently skips if API call fails.
    """
    if not match or "home" not in match or "away" not in match:
        return
    home_name = match["home"].get("name")
    away_name = match["away"].get("name")
    if not home_name or not away_name:
        return
    fresh_odds = _odds_block(home_name, away_name)
    if fresh_odds and fresh_odds.get("home_win"):
        match["odds"] = fresh_odds


def _odds_block(home_name: str, away_name: str) -> dict:
    key = os.getenv("THE_ODDS_API_KEY")
    fallback = {"home_win": None, "draw": None, "away_win": None, "source": None}
    if not key:
        return fallback
    try:
        r = requests.get(f"{ODDS_BASE}/sports/soccer_fifa_world_cup/odds",
                         params={"apiKey": key, "regions": "eu", "markets": "h2h",
                                 "oddsFormat": "decimal"}, timeout=25)
        if r.status_code != 200:
            return fallback

        # All spellings of each team, so the match works even when the two
        # APIs name a nation differently (USA vs United States, etc).
        home_variants = _name_variants(home_name)
        away_variants = _name_variants(away_name)

        for ev in r.json():
            api_home = ev.get("home_team", "")
            api_away = ev.get("away_team", "")
            if api_home in home_variants and api_away in away_variants:
                bm = (ev.get("bookmakers") or [None])[0]
                if not bm:
                    break
                outcomes = bm["markets"][0]["outcomes"]
                price = {o["name"]: o["price"] for o in outcomes}
                return {
                    "home_win": price.get(api_home),
                    "draw": price.get("Draw"),
                    "away_win": price.get(api_away),
                    "source": bm.get("title", "bookmaker"),
                }
    except Exception:
        pass
    return fallback


def _weather_block(lat: float, lon: float, dt: datetime) -> dict | None:
    """Live forecast for the kickoff hour. Open-Meteo only forecasts ~16 days
    out, so this returns None for fixtures further away (a knockout previewed
    early). That's fine: previews are built J-1, when the real forecast exists,
    and the slide hides the weather block when there's no data rather than
    inventing a (possibly very wrong) estimate. One retry covers the transient
    API hiccup that blanked the odd group-stage preview."""
    for _ in range(2):
        try:
            r = requests.get(METEO_BASE, params={
                "latitude": lat, "longitude": lon,
                "hourly": "temperature_2m,wind_speed_10m,weather_code",
                "start_date": dt.date().isoformat(), "end_date": dt.date().isoformat(),
            }, timeout=25)
            if r.status_code != 200:
                return None  # out-of-range date etc. — hide the block
            h = r.json().get("hourly", {})
            times = h.get("time", [])
            if not times:
                return None
            target = dt.strftime("%Y-%m-%dT%H:00")
            i = times.index(target) if target in times else (12 if len(times) > 12 else 0)
            code = h.get("weather_code", [0])[i]
            return {
                "summary": _wmo(code),
                "temp_c": round(h.get("temperature_2m", [20])[i]),
                "wind_kph": round(h.get("wind_speed_10m", [0])[i]),
                "icon": _wmo_icon(code),
            }
        except Exception:
            continue  # transient — retry once, then give up (None)
    return None


def _wmo(code: int) -> str:
    if code == 0: return "Clear"
    if code in (1, 2, 3): return "Partly cloudy"
    if code in (45, 48): return "Fog"
    if 51 <= code <= 67: return "Rain"
    if 71 <= code <= 77: return "Snow"
    if 80 <= code <= 99: return "Showers"
    return "Cloudy"


def _wmo_icon(code: int) -> str:
    if code == 0: return "sun"
    if code in (1, 2, 3): return "cloud-sun"
    if 51 <= code <= 99: return "rain"
    return "cloud"


def _fun_stats(match: dict) -> list[dict]:
    """Pick 3 real, varied facts from a computed pool (seeded per match)."""
    rng = _rng_for(match)
    home, away = match["home"], match["away"]
    h2h = (match.get("head_to_head") or {}).get("total") or {}
    hw, aw, dr = h2h.get("home_wins", 0), h2h.get("away_wins", 0), h2h.get("draws", 0)
    n_meet = hw + aw + dr

    pool: list[dict] = []

    # Market value
    combined = home["squad_value_eur_m"] + away["squad_value_eur_m"]
    pool.append({"value": _money(combined),
                 "label": "in combined squad market value lines up on the pitch."})
    richer, poorer = (home, away) if home["squad_value_eur_m"] >= away["squad_value_eur_m"] else (away, home)
    if poorer["squad_value_eur_m"] > 0:
        ratio = richer["squad_value_eur_m"] / poorer["squad_value_eur_m"]
        if ratio >= 1.5:
            pool.append({"value": f"{ratio:.1f}x",
                         "label": f"{richer['name']}'s squad is worth {ratio:.1f} times {poorer['name']}'s."})

    # Head-to-head
    if n_meet > 0:
        pool.append({"value": str(n_meet),
                     "label": f"times {home['name']} and {away['name']} have met before."})
        if hw != aw:
            dom, dw = (home, hw) if hw > aw else (away, aw)
            pool.append({"value": str(dw),
                         "label": f"of those wins belong to {dom['name']} in the head-to-head."})
    else:
        # The dataset is complete (since 1872), so 0 here genuinely means a
        # first-ever meeting.
        pool.append({"value": "1st",
                     "label": f"ever meeting between {home['name']} and {away['name']} at any level."})

    # Ranking gap
    gap = abs(home["fifa_rank"] - away["fifa_rank"])
    if gap >= 8:
        higher = home if home["fifa_rank"] < away["fifa_rank"] else away
        pool.append({"value": str(gap),
                     "label": f"places separate them in the FIFA ranking, with {higher['name']} on top."})

    # Top-5 league representation
    top5 = home["players_top5_leagues"] + away["players_top5_leagues"]
    if top5 > 0:
        pool.append({"value": str(top5),
                     "label": "players on show ply their trade in Europe's top-5 leagues."})

    # Age contrast
    age_gap = abs(home["avg_age"] - away["avg_age"])
    if age_gap >= 1.5:
        younger = home if home["avg_age"] < away["avg_age"] else away
        pool.append({"value": f"{younger['avg_age']:.0f}",
                     "label": f"is {younger['name']}'s average age, the younger side here."})

    rng.shuffle(pool)
    # Always keep at least the market-value fact; fill to 3.
    chosen = pool[:3]
    while len(chosen) < 3:
        chosen.append({"value": f"#{home['fifa_rank']}",
                       "label": f"is {home['name']}'s current FIFA world ranking."})
    return chosen[:3]


def _money(m: int) -> str:
    return f"€{m/1000:.2f}B" if m >= 1000 else f"€{m}M"


def _did_you_know(match: dict) -> str:
    rng = _rng_for(match)
    home, away = match["home"], match["away"]
    h2h = (match.get("head_to_head") or {}).get("total") or {}
    hw, aw, dr = h2h.get("home_wins", 0), h2h.get("away_wins", 0), h2h.get("draws", 0)
    facts = []
    if hw + aw + dr > 0:
        if hw > aw:
            facts.append(f"{home['name']} have the upper hand historically, winning {hw} of their {hw+aw+dr} meetings with {away['name']}.")
        elif aw > hw:
            facts.append(f"{away['name']} have edged the history books, winning {aw} of {hw+aw+dr} against {home['name']}.")
        else:
            facts.append(f"There is nothing between them historically: {hw} wins each across {hw+aw+dr} meetings.")
    facts.append(f"Between them, {home['name']} and {away['name']} send {home['players_top5_leagues']+away['players_top5_leagues']} players from Europe's top-5 leagues onto the pitch.")
    if home["squad_value_eur_m"] + away["squad_value_eur_m"] >= 1000:
        facts.append(f"There is over {_money(home['squad_value_eur_m']+away['squad_value_eur_m'])} of talent on the field tonight.")
    return rng.choice(facts)


# ---------------------------------------------------------------------------
# Optional: football-data match id → host stadium (enables weather + slide 2).
# Fill as you confirm the schedule; unknown ids fall back to "Venue TBD".
# ---------------------------------------------------------------------------
VENUE_BY_MATCH: dict[int, str] = {
    # Knockout fixtures from the official FIFA WC 2026 schedule
    # (group matches are resolved automatically via wc_data.GROUP_VENUES).
    # Round of 32
    537417: "SoFi Stadium",                # 28 Jun — 2A vs 2B
    537423: "NRG Stadium",                 # 29 Jun — 1C vs 2F
    537415: "Gillette Stadium",            # 29 Jun — 1E vs 3
    537418: "Estadio BBVA",                # 30 Jun — 1F vs 2C
    537424: "AT&T Stadium",                # 30 Jun — 2E vs 2I
    537416: "MetLife Stadium",             # 30 Jun — 1I vs 3
    537425: "Estadio Azteca",              # 01 Jul — 1A vs 3
    537426: "Mercedes-Benz Stadium",       # 01 Jul — 1L vs 3
    537422: "Lumen Field",                 # 01 Jul — 1G vs 3
    537421: "Levi's Stadium",              # 02 Jul — 1D vs 3
    537420: "SoFi Stadium",                # 02 Jul — 1H vs 2J
    537419: "BMO Field",                   # 02 Jul — 2K vs 2L
    537429: "BC Place",                    # 03 Jul — 1B vs 3
    537428: "AT&T Stadium",                # 03 Jul — 2D vs 2G
    537427: "Hard Rock Stadium",           # 03 Jul — 1J vs 2H
    537430: "Arrowhead Stadium",           # 04 Jul — 1K vs 3
    # Round of 16 (eighth-finals)
    537376: "NRG Stadium",                 # 04 Jul — R16/2
    537375: "Lincoln Financial Field",     # 04 Jul — R16/1
    537377: "MetLife Stadium",             # 05 Jul — R16/5
    537378: "Estadio Azteca",              # 06 Jul — R16/6
    537379: "AT&T Stadium",                # 06 Jul — R16/3
    537380: "Lumen Field",                 # 07 Jul — R16/4
    537381: "Mercedes-Benz Stadium",       # 07 Jul — R16/7
    537382: "BC Place",                    # 07 Jul — R16/8
    # Quarter-finals
    537383: "Gillette Stadium",            # 09 Jul — QF1
    537384: "SoFi Stadium",                # 10 Jul — QF2
    537385: "Hard Rock Stadium",           # 11 Jul — QF3
    537386: "Arrowhead Stadium",           # 12 Jul — QF4
    # Semi-finals
    537387: "AT&T Stadium",                # 14 Jul — SF1
    537388: "Mercedes-Benz Stadium",       # 15 Jul — SF2
    # Third-place & Final
    537389: "Hard Rock Stadium",           # 18 Jul — third place
    537390: "MetLife Stadium",             # 19 Jul — Final
}


# ===========================================================================
# Enrichment — ratings (radar)
# ===========================================================================
def _ensure_ratings(match: dict) -> None:
    for side in ("home", "away"):
        team = match.get(side, {})
        if not team.get("ratings"):
            team["ratings"] = _derive_ratings(team)


def _derive_ratings(team: dict) -> dict:
    rank = team.get("fifa_rank", 20)
    value = team.get("squad_value_eur_m", 300)
    age = team.get("avg_age", 27)
    top5 = team.get("players_top5_leagues", 10)
    rank_score = _clamp(100 - (rank - 1) * 2.0)
    value_score = _clamp(45 + (value - 300) / 12)
    exp_score = _clamp(40 + (age - 24) * 8)
    depth_score = _clamp(40 + top5 * 2.5)
    return {
        "attack":     round(_clamp(rank_score * 0.6 + value_score * 0.4)),
        "midfield":   round(_clamp(rank_score * 0.5 + depth_score * 0.5)),
        "defense":    round(_clamp(rank_score * 0.55 + depth_score * 0.45)),
        "experience": round(exp_score),
        "value":      round(value_score),
    }


def _clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))


# ===========================================================================
# CLI
# ===========================================================================
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    m = fetch_match(ref)
    if m is None:
        print("No match found.")
    else:
        print(f"{m['home']['name']} vs {m['away']['name']} — "
              f"{m.get('kickoff_local_label')} ({m['stage']})")
        p = m.get("prediction", {})
        print(f"Prediction: {p.get('home_score')}-{p.get('away_score')} — {p.get('reasoning')}")
