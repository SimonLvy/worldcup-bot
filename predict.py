"""Heuristic match predictor — free, deterministic, varied.

Design goals (vs. the old "always 2-1 favourite" version):
  - DETERMINISTIC per match: same match_id → same prediction, every run.
  - VARIED scorelines: 0-0, 1-0, 2-0, 2-1, 3-1, 1-1, 2-2 — depending on the
    expected intensity, not always 2-1.
  - REALISTIC upsets: tight matches can produce draws; medium-gap matches
    can occasionally see an upset; big favourites win the vast majority.
  - DIVERSE narrative: a pool of sentences per outcome category, picked by
    seed so the feed doesn't read like a stuck record.

The "strength gap" between home and away is built from four signals
(odds when present, FIFA rank, recent form, head-to-head), then the gap
selects a probability band that determines the outcome distribution.
"""
from __future__ import annotations

import random


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def predict(match: dict) -> dict:
    home, away = match["home"], match["away"]
    s_home = _strength(home, away, match, side="home")
    s_away = _strength(away, home, match, side="away")
    gap = s_home - s_away
    fav_side = "home" if gap >= 0 else "away"

    rng = random.Random(_seed(match))
    outcome = _choose_outcome(gap, rng)   # "fav" | "draw" | "upset"
    home_score, away_score = _choose_scoreline(outcome, gap, fav_side, rng)
    reasoning = _reason(match, outcome, gap, home_score, away_score, fav_side, rng)
    return {"home_score": home_score, "away_score": away_score, "reasoning": reasoning}


def _seed(match: dict) -> int:
    """Stable per-match seed so re-renders are idempotent."""
    key = str(match.get("match_id") or
              (match["home"]["name"] + match["away"]["name"]))
    # Python's hash() is salted per process — use a stable one.
    h = 1469598103934665603
    for c in key:
        h = (h ^ ord(c)) * 1099511628211
        h &= 0xFFFFFFFFFFFFFFFF
    return h


# ---------------------------------------------------------------------------
# Strength model
# ---------------------------------------------------------------------------
def _strength(team: dict, opp: dict, match: dict, side: str) -> float:
    rank = team.get("fifa_rank", 25)
    rank_term = (50 - rank) / 50.0
    form_term = _form_points(team.get("last5", [])) / 15.0
    h2h_term = _h2h_edge(match, side)
    odds_term = _odds_share(match, side)

    if odds_term is not None:
        return 0.45 * odds_term + 0.25 * rank_term + 0.20 * form_term + 0.10 * h2h_term
    return 0.45 * rank_term + 0.35 * form_term + 0.20 * h2h_term


def _form_points(last5: list[str]) -> int:
    pts = {"W": 3, "D": 1, "L": 0}
    return sum(pts.get(r, 0) for r in (last5 or []))


def _h2h_edge(match: dict, side: str) -> float:
    total = (match.get("head_to_head") or {}).get("total") or {}
    hw, aw, d = total.get("home_wins", 0), total.get("away_wins", 0), total.get("draws", 0)
    n = hw + aw + d
    if n == 0:
        return 0.5
    return (hw if side == "home" else aw) / n


def _odds_share(match: dict, side: str) -> float | None:
    odds = match.get("odds") or {}
    h, d, a = odds.get("home_win"), odds.get("draw"), odds.get("away_win")
    if not (h and d and a):
        return None
    ph, pd, pa = 1 / h, 1 / d, 1 / a
    s = ph + pd + pa
    return (ph if side == "home" else pa) / s


# ---------------------------------------------------------------------------
# Outcome model — gap-aware probability bands
# ---------------------------------------------------------------------------
def _choose_outcome(gap: float, rng: random.Random) -> str:
    """Return 'fav' (favourite wins), 'draw', or 'upset' (outsider wins).

    Bands based on |gap|:
        0.00 – 0.08  TIGHT      → 32% draw, 36% fav, 32% upset
        0.08 – 0.18  CLOSE      → 26% draw, 51% fav, 23% upset
        0.18 – 0.32  CLEAR      → 19% draw, 67% fav, 14% upset
        0.32 – 0.50  STRONG     → 13% draw, 79% fav,  8% upset
        > 0.50       DOMINANT   →  8% draw, 88% fav,  4% upset
    """
    g = abs(gap)
    if g < 0.08:    weights = (0.36, 0.32, 0.32)  # fav, draw, upset
    elif g < 0.18:  weights = (0.51, 0.26, 0.23)
    elif g < 0.32:  weights = (0.67, 0.19, 0.14)
    elif g < 0.50:  weights = (0.79, 0.13, 0.08)
    else:           weights = (0.88, 0.08, 0.04)
    return rng.choices(["fav", "draw", "upset"], weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Scoreline distributions per outcome
# ---------------------------------------------------------------------------
# Realistic football scorelines weighted roughly like real WC tournaments.
# Listed as (winner_goals, loser_goals).
_WIN_SCORES_TIGHT  = [(1,0)]*4 + [(2,1)]*4 + [(2,0)]*2 + [(3,1)]*1
_WIN_SCORES_CLEAR  = [(2,1)]*3 + [(2,0)]*4 + [(1,0)]*3 + [(3,1)]*3 + [(3,0)]*2 + [(4,1)]*1
_WIN_SCORES_STRONG = [(2,0)]*4 + [(3,0)]*3 + [(3,1)]*3 + [(4,1)]*2 + [(4,0)]*2 + [(2,1)]*2
_DRAW_SCORES       = [(1,1)]*5 + [(0,0)]*3 + [(2,2)]*2 + [(3,3)]*0  # 3-3 is too rare


def _choose_scoreline(outcome: str, gap: float, fav_side: str, rng: random.Random) -> tuple[int, int]:
    g = abs(gap)
    if outcome == "draw":
        a, b = rng.choice(_DRAW_SCORES)
        return (a, b)

    # Pick a (winner_goals, loser_goals) tuple sized to the gap.
    if g < 0.18:    pool = _WIN_SCORES_TIGHT
    elif g < 0.40:  pool = _WIN_SCORES_CLEAR
    else:           pool = _WIN_SCORES_STRONG

    wg, lg = rng.choice(pool)
    if outcome == "fav":
        winner = fav_side
    else:  # upset
        winner = "away" if fav_side == "home" else "home"
    return (wg, lg) if winner == "home" else (lg, wg)


# ---------------------------------------------------------------------------
# Narrative — pools of sentence templates per scenario
# ---------------------------------------------------------------------------
# No em-dashes anywhere. {home}/{away}/{fav}/{dog} substituted at render time.
_TEMPLATES_FAV_DOMINANT = [
    "{fav} simply have too much quality across the pitch and should win this at a canter.",
    "The gulf in class is hard to ignore, so {fav} are backed to take charge early and stay in control.",
    "On current form and squad depth, {fav} look a class above and ought to win comfortably.",
    "Everything points to {fav}: stronger squad, better ranking, and the bigger-game experience.",
]
_TEMPLATES_FAV_CLEAR = [
    "{fav} carry the greater threat going forward and should have just enough to see it through.",
    "{fav} have the better individuals, and over 90 minutes that edge usually tells.",
    "Expect {fav} to control possession and break {dog} down for a deserved win.",
    "{fav} are the more complete side and should manage the game to a win, even if {dog} stay competitive.",
]
_TEMPLATES_FAV_TIGHT = [
    "{fav} are slight favourites, but {dog} are well organised and will make this a real contest.",
    "Little separates these two, yet {fav}'s extra pedigree should just about decide it.",
    "A close call, with {fav} relying on a single moment of quality to settle a tight night.",
    "{fav} get the nod, though {dog} have the tools to frustrate them for long spells.",
]
_TEMPLATES_DRAW = [
    "These two match up almost evenly, and a share of the spoils looks the likeliest outcome.",
    "Form and ranking point the same way here, so a balanced game ending level makes sense.",
    "Both teams have reasons for caution, and that often produces a tight, even result.",
    "Neither side holds a clear edge, so honours finishing even would be no surprise.",
    "Closely matched in every department, this has the makings of a stalemate.",
]
_TEMPLATES_UPSET = [
    "{dog} have the belief and the weapons to cause a genuine shock against {fav}.",
    "{fav} have looked vulnerable, and {dog} are well placed to take advantage.",
    "Big call, but {dog} are backed to upset the odds and send {fav} home frustrated.",
    "{dog}'s recent form suggests they can punish a {fav} side that may be off the pace.",
]
_TEMPLATES_DEFENSIVE = [
    "Two cautious, well-drilled sides suggest a low-scoring affair settled by the odd goal.",
    "Goals could be at a premium here, with both teams wary of overcommitting.",
    "Expect a disciplined, tight contest where clean sheets are the priority.",
]
_TEMPLATES_OPEN = [
    "Both teams like to attack, so goals at either end look likely in an open game.",
    "Neither defence is watertight, which points to an entertaining, high-scoring night.",
    "This has the feel of an open game decided by who takes their chances.",
]


def _reason(match: dict, outcome: str, gap: float,
            hs: int, as_: int, fav_side: str, rng: random.Random) -> str:
    home_name = match["home"]["name"]
    away_name = match["away"]["name"]
    fav = match["home"] if fav_side == "home" else match["away"]
    dog = match["away"] if fav_side == "home" else match["home"]
    fav_name, dog_name = fav["name"], dog["name"]

    g = abs(gap)
    if outcome == "draw":
        pool = _TEMPLATES_DRAW
        if hs + as_ == 0: pool = pool + _TEMPLATES_DEFENSIVE
        if hs + as_ >= 4: pool = pool + _TEMPLATES_OPEN
    elif outcome == "upset":
        pool = _TEMPLATES_UPSET
    else:
        if g >= 0.40:   pool = _TEMPLATES_FAV_DOMINANT
        elif g >= 0.20: pool = _TEMPLATES_FAV_CLEAR
        else:           pool = _TEMPLATES_FAV_TIGHT

    base = rng.choice(pool).format(home=home_name, away=away_name, fav=fav_name, dog=dog_name)

    # Append ONE concrete, credible supporting argument (no dashes).
    arg = _support_arg(match, fav, dog, outcome, rng)
    if arg:
        base += " " + arg
    return base


def _support_arg(match: dict, fav: dict, dog: dict, outcome: str, rng: random.Random) -> str:
    """A second sentence citing a real, checkable fact behind the call."""
    candidates = []

    # Ranking
    if abs(fav.get("fifa_rank", 25) - dog.get("fifa_rank", 25)) >= 6:
        higher = fav if fav["fifa_rank"] < dog["fifa_rank"] else dog
        candidates.append(f"{higher['name']} sit {abs(fav['fifa_rank']-dog['fifa_rank'])} places higher in the world ranking.")

    # Form
    hf = _form_points(match["home"].get("last5", []))
    af = _form_points(match["away"].get("last5", []))
    home_name, away_name = match["home"]["name"], match["away"]["name"]
    if (match["home"].get("last5") or match["away"].get("last5")):
        if abs(hf - af) >= 4:
            hotter = home_name if hf > af else away_name
            candidates.append(f"{hotter} come in on the stronger recent run.")

    # Head-to-head
    total = (match.get("head_to_head") or {}).get("total") or {}
    hw, aw = total.get("home_wins", 0), total.get("away_wins", 0)
    if hw + aw + total.get("draws", 0) > 0 and hw != aw:
        leader = home_name if hw > aw else away_name
        candidates.append(f"{leader} have historically had their number in this fixture.")

    # Market value
    if dog.get("squad_value_eur_m") and fav.get("squad_value_eur_m"):
        ratio = fav["squad_value_eur_m"] / max(1, dog["squad_value_eur_m"])
        if ratio >= 1.8 and outcome == "fav":
            candidates.append(f"{fav['name']}'s squad is valued well above their opponents.")

    return rng.choice(candidates) if candidates else ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json, pathlib, sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    m = json.loads(pathlib.Path("series/match.example.json").read_text(encoding="utf-8"))
    print(predict(m))
