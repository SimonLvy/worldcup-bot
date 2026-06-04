"""World Cup history — derived from the match dataset, NOT hand-typed.

The accuracy lesson: hand-curated per-nation histories are error-prone (e.g.
Scotland's appearances were wrong). So this module derives everything it can
straight from data/international_results.csv (the martj42 dataset, refreshed
daily), and curates only the ONE thing the dataset can't encode reliably:
the final standings of each tournament (penalty-shootout finals show as draws
in the raw scores, so champions aren't derivable from scores alone).

What's derived from the dataset (accurate, self-updating):
  - WC appearances (count of distinct years a nation played, year < 2026)
  - the list of those years
  - match count per (nation, year) → used to infer the round reached for
    teams that didn't make the top 4

What's curated (small, canonical, stable forever — 22 tournaments):
  - WC_PODIUMS: champion / runner-up / 3rd / 4th of every World Cup

From these two we compute, per nation: titles, best finish, and a per-year
"finish" label for the most recent appearances. Names follow the dataset's
convention (it consolidates West Germany→Germany and USSR→Russia).
"""
from __future__ import annotations

import csv
import functools
from collections import defaultdict
from pathlib import Path

import config


# ---------------------------------------------------------------------------
# Curated: final standings of every World Cup (champion, runner-up, 3rd, 4th).
# Canonical, stable, verifiable. Names match the dataset (Germany absorbs West
# Germany; Russia absorbs the Soviet Union).
# ---------------------------------------------------------------------------
WC_PODIUMS: dict[int, tuple[str, str, str, str]] = {
    1930: ("Uruguay", "Argentina", "United States", "Yugoslavia"),
    1934: ("Italy", "Czechoslovakia", "Germany", "Austria"),
    1938: ("Italy", "Hungary", "Brazil", "Sweden"),
    1950: ("Uruguay", "Brazil", "Sweden", "Spain"),
    1954: ("Germany", "Hungary", "Austria", "Uruguay"),
    1958: ("Brazil", "Sweden", "France", "Germany"),
    1962: ("Brazil", "Czechoslovakia", "Chile", "Yugoslavia"),
    1966: ("England", "Germany", "Portugal", "Russia"),
    1970: ("Brazil", "Italy", "Germany", "Uruguay"),
    1974: ("Germany", "Netherlands", "Poland", "Brazil"),
    1978: ("Argentina", "Netherlands", "Brazil", "Italy"),
    1982: ("Italy", "Germany", "Poland", "France"),
    1986: ("Argentina", "Germany", "France", "Belgium"),
    1990: ("Germany", "Argentina", "Italy", "England"),
    1994: ("Brazil", "Italy", "Sweden", "Bulgaria"),
    1998: ("France", "Brazil", "Croatia", "Netherlands"),
    2002: ("Brazil", "Germany", "Turkey", "South Korea"),
    2006: ("Italy", "France", "Germany", "Portugal"),
    2010: ("Spain", "Netherlands", "Germany", "Uruguay"),
    2014: ("Germany", "Argentina", "Netherlands", "Brazil"),
    2018: ("France", "Croatia", "Belgium", "England"),
    2022: ("Argentina", "France", "Croatia", "Morocco"),
}

# Placing → display label for podium finishers.
_PODIUM_LABEL = {0: "Champions", 1: "Runners-up", 2: "Third place", 3: "Fourth place"}

# TLA → the country name as it appears in the dataset / WC_PODIUMS. Only the
# divergences from a naive .title() need listing; the rest resolve directly.
TLA_TO_DATASET_NAME: dict[str, str] = {
    "USA": "United States", "KOR": "South Korea", "RSA": "South Africa",
    "CIV": "Ivory Coast", "IRN": "Iran", "KSA": "Saudi Arabia",
    "CPV": "Cape Verde", "COD": "DR Congo", "CUW": "Curaçao",
    "BIH": "Bosnia and Herzegovina", "CZE": "Czech Republic",
    "ARG": "Argentina", "FRA": "France", "ESP": "Spain", "ENG": "England",
    "BRA": "Brazil", "POR": "Portugal", "NED": "Netherlands", "GER": "Germany",
    "BEL": "Belgium", "CRO": "Croatia", "URY": "Uruguay", "COL": "Colombia",
    "MAR": "Morocco", "SUI": "Switzerland", "JPN": "Japan", "MEX": "Mexico",
    "SEN": "Senegal", "ECU": "Ecuador", "AUT": "Austria", "SWE": "Sweden",
    "TUR": "Turkey", "AUS": "Australia", "EGY": "Egypt", "NOR": "Norway",
    "SCO": "Scotland", "CAN": "Canada", "PAR": "Paraguay", "TUN": "Tunisia",
    "ALG": "Algeria", "PAN": "Panama", "GHA": "Ghana", "IRQ": "Iraq",
    "QAT": "Qatar", "JOR": "Jordan", "UZB": "Uzbekistan", "NZL": "New Zealand",
    "HAI": "Haiti",
}


def dataset_name(tla: str) -> str:
    return TLA_TO_DATASET_NAME.get((tla or "").upper(), (tla or "").title())


@functools.lru_cache(maxsize=1)
def _load() -> tuple[dict[str, set[int]], dict[tuple[str, int], int]]:
    """Return (years_by_team, matchcount_by_team_year) for WC matches < 2026."""
    path = config.ROOT / "data" / "international_results.csv"
    years: dict[str, set[int]] = defaultdict(set)
    counts: dict[tuple[str, int], int] = defaultdict(int)
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("tournament") != "FIFA World Cup":
                continue
            y = int(r["date"][:4])
            if y >= 2026:
                continue
            for team in (r["home_team"], r["away_team"]):
                years[team].add(y)
                counts[(team, y)] += 1
    return dict(years), dict(counts)


def _finish_for_year(name: str, year: int, matchcount: int) -> str:
    """Label the round a team reached in a given WC.

    Top-4 comes from the curated podium (always accurate). Everything else is
    inferred from how many matches they played — reliable for the modern
    knockout format (1986+: 3=group, 4=R16, 5=QF). Pre-1986 deep runs are rare
    among non-podium teams (most early exits are group stage = 2-3 games),
    so the same mapping holds up for the ranges we actually display.
    """
    podium = WC_PODIUMS.get(year)
    if podium and name in podium:
        return _PODIUM_LABEL[podium.index(name)]
    if matchcount >= 5:
        return "Quarter-final"
    if matchcount == 4:
        return "Round of 16"
    return "Group stage"


def history_for(tla: str) -> dict:
    """Full WC history payload for a nation, derived + curated.

    Returns:
      {
        "appearances": int,            # WCs played before 2026
        "years": [int, ...],           # ascending
        "titles": int,                 # WC wins
        "title_years": [int, ...],
        "best_finish": str | None,     # e.g. "Champions (1998, 2018)"
        "last5": [{"year": int, "finish": str}, ...],  # most recent first
        "is_first_wc": bool,           # 2026 is their debut
      }
    """
    name = dataset_name(tla)
    years_by_team, counts = _load()
    years = sorted(years_by_team.get(name, set()))

    title_years = [y for y, p in WC_PODIUMS.items() if p[0] == name]
    titles = len(title_years)

    # Best finish = the best placing ever reached (lower placing index = better).
    best_idx, best_years = 99, []
    for y in years:
        p = WC_PODIUMS.get(y)
        if p and name in p:
            idx = p.index(name)
            if idx < best_idx:
                best_idx, best_years = idx, [y]
            elif idx == best_idx:
                best_years.append(y)
    if best_idx <= 3:
        label = _PODIUM_LABEL[best_idx]
        yrs = ", ".join(str(y) for y in best_years)
        best_finish = f"{label} ({yrs})"
    elif years:
        # Never made the top 4 — report the deepest knockout round reached.
        deepest = "Group stage"
        order = {"Group stage": 0, "Round of 16": 1, "Quarter-final": 2}
        for y in years:
            f = _finish_for_year(name, y, counts.get((name, y), 0))
            if order.get(f, 0) > order.get(deepest, 0):
                deepest = f
        best_finish = deepest
    else:
        best_finish = None

    last5 = [
        {"year": y, "finish": _finish_for_year(name, y, counts.get((name, y), 0))}
        for y in years[::-1][:5]
    ]

    return {
        "appearances": len(years),
        "years": years,
        "titles": titles,
        "title_years": title_years,
        "best_finish": best_finish,
        "last5": last5,
        "is_first_wc": len(years) == 0,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for tla in ("SCO", "FRA", "BRA", "MAR", "CPV", "CZE", "GER"):
        h = history_for(tla)
        print(f"\n{tla} ({dataset_name(tla)}):")
        print(f"  appearances: {h['appearances']}  titles: {h['titles']}")
        print(f"  best: {h['best_finish']}")
        print(f"  first_wc: {h['is_first_wc']}")
        print(f"  last5: {[(d['year'], d['finish']) for d in h['last5']]}")
