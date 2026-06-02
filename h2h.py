"""Complete head-to-head history from the international results dataset.

Source: martj42/international_results — every international match since 1872,
all competitions including friendlies (~49k matches), baked into
data/international_results.csv (one-time download, no runtime scraping).

We compute the full all-time record and the most recent meetings between any
two teams, which is far deeper and more accurate than the football-data free
tier (recent matches only). Solves the "0 meetings" false positive
(e.g. France vs Senegal, who met at the 2002 World Cup).
"""
from __future__ import annotations

import csv
from pathlib import Path

import config

CSV_PATH = config.ROOT / "data" / "international_results.csv"

# football-data team name → dataset team name (only the 4 that differ).
ALIAS = {
    "Czechia": "Czech Republic",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
}

_ROWS: list[dict] | None = None


def _load() -> list[dict]:
    global _ROWS
    if _ROWS is None:
        with CSV_PATH.open(encoding="utf-8") as f:
            _ROWS = list(csv.DictReader(f))
    return _ROWS


def _ds_name(name: str) -> str:
    return ALIAS.get(name, name)


def head_to_head(home_name: str, away_name: str, before: str | None = None,
                 last_n: int = 3) -> dict:
    """Full record + last N meetings, in THIS fixture's home/away orientation.

    `before` (ISO date) restricts to meetings strictly before the fixture, so
    we never show a result that hasn't happened yet. Returns the contract:
      {total: {home_wins, draws, away_wins}, last3: [{date, competition, score, winner}]}
    where winner is 'home' | 'away' | 'draw' relative to this fixture.
    """
    a, b = _ds_name(home_name), _ds_name(away_name)
    home_wins = away_wins = draws = 0
    meetings = []

    for m in _load():
        h, aw = m["home_team"], m["away_team"]
        if {h, aw} != {a, b}:
            continue
        if before and m["date"] >= before:
            continue
        try:
            hs, as_ = int(m["home_score"]), int(m["away_score"])
        except (ValueError, KeyError):
            continue

        # Re-orient to THIS fixture's home/away.
        if h == a:
            fixt_home_goals, fixt_away_goals = hs, as_
        else:
            fixt_home_goals, fixt_away_goals = as_, hs

        if fixt_home_goals > fixt_away_goals:
            home_wins += 1; winner = "home"
        elif fixt_away_goals > fixt_home_goals:
            away_wins += 1; winner = "away"
        else:
            draws += 1; winner = "draw"

        meetings.append({
            "date": m["date"],
            "competition": m.get("tournament", "Match"),
            "score": f"{fixt_home_goals}-{fixt_away_goals}",
            "winner": winner,
        })

    meetings.sort(key=lambda x: x["date"], reverse=True)
    return {
        "total": {"home_wins": home_wins, "draws": draws, "away_wins": away_wins},
        "last3": meetings[:last_n],
    }


def form_before(team_name: str, before: str, last_n: int = 5) -> list[str]:
    """Last N results (W/D/L) for a team from matches before `before` (ISO date).

    Uses the full dataset (friendlies included), so gives real pre-tournament
    form even before any WC match is played.
    """
    name = _ds_name(team_name)
    results = []
    for m in _load():
        if m["date"] >= before:
            continue
        h, aw = m["home_team"], m["away_team"]
        if name not in (h, aw):
            continue
        try:
            hs, as_ = int(m["home_score"]), int(m["away_score"])
        except (ValueError, KeyError):
            continue
        if hs == as_:
            results.append(("D", m["date"]))
        elif (hs > as_ and h == name) or (as_ > hs and aw == name):
            results.append(("W", m["date"]))
        else:
            results.append(("L", m["date"]))

    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:last_n]]


def refresh_dataset(max_age_hours: float = 23) -> bool:
    """Re-download the CSV if it's older than `max_age_hours`. Returns True if refreshed."""
    import time
    import requests as req

    if CSV_PATH.exists():
        age_h = (time.time() - CSV_PATH.stat().st_mtime) / 3600
        if age_h < max_age_hours:
            return False

    url = ("https://raw.githubusercontent.com/"
           "martj42/international_results/master/results.csv")
    print("[dataset] refreshing international_results.csv…")
    try:
        r = req.get(url, headers={"User-Agent": "WorldCupBot/1.0"}, timeout=60)
        r.raise_for_status()
        CSV_PATH.write_bytes(r.content)
        global _ROWS
        _ROWS = None  # invalidate in-process cache
        print(f"[dataset] downloaded {len(r.content)//1024} KB")
        return True
    except Exception as exc:
        print(f"[dataset] refresh failed ({exc!r}) — using cached copy")
        return False


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for a, b in [("France", "Senegal"), ("Brazil", "Argentina"), ("Spain", "Cape Verde Islands")]:
        r = head_to_head(a, b)
        t = r["total"]
        print(f"{a} {t['home_wins']}-{t['draws']}-{t['away_wins']} {b}  "
              f"({t['home_wins']+t['draws']+t['away_wins']} meetings)")
        for mt in r["last3"]:
            print("   ", mt["date"], mt["score"], mt["winner"], "|", mt["competition"])
