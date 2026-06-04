"""Heuristic predictor for nation showcase posts.

Produces two editorial signals per nation:
  - quali_pct(tla)      : % chance to advance from the group stage (0..100)
  - predicted_round(tla): best round the bot expects this team to reach
                          ("Group stage", "Round of 32", "Round of 16",
                           "Quarter-final", "Semi-final", "Final", "Champions")

Same spirit as predict.py: deterministic, free, varied. We rank each team by a
strength score (FIFA rank + recent form) within their group for the quali %,
and across all 48 for the round verdict. No external API call needed.

The form input is intentionally caller-provided (h2h.form_before at render
time), so "last 5" stays fresh as the tournament progresses — a post for
France generated on June 14 picks up any J1 match France played by then.
"""
from __future__ import annotations

import wc_data
import h2h


# Mapping the team-name as football-data emits it (used by h2h.form_before).
# Some entries diverge from TLA_DISPLAY (e.g. football-data uses "USA" not
# "United States"); the fallback below covers everything via NATIONS.
FORM_DATASET_NAME: dict[str, str] = {
    "USA": "United States",
    "KOR": "South Korea",
    "BIH": "Bosnia-Herzegovina",
    "RSA": "South Africa",
    "CIV": "Ivory Coast",
    "CPV": "Cape Verde",
    "CUW": "Curaçao",
    "COD": "DR Congo",
    "URY": "Uruguay",
    "KSA": "Saudi Arabia",
}


def _form_team_name(tla: str) -> str:
    """Best-effort country name lookup for the international results dataset."""
    return FORM_DATASET_NAME.get(tla) or _tla_to_name(tla)


def _tla_to_name(tla: str) -> str:
    # Avoid the circular import of companion.TLA_DISPLAY by reading it locally.
    import companion
    return companion.TLA_DISPLAY.get(tla, tla.title())


def _form_points(last5: list[str]) -> float:
    pts = {"W": 3, "D": 1, "L": 0}
    return sum(pts.get(r, 0) for r in (last5 or []))


def strength(tla: str, before_date: str) -> float:
    """Composite team strength: FIFA rank + last-5 form. Higher = stronger.

    `before_date` (ISO YYYY-MM-DD) bounds the form window — call with today's
    date at render time so the L5 stays fresh as the tournament progresses.
    """
    info = wc_data.NATIONS.get(tla.upper())
    if not info:
        return 0.0
    rank = info.get("rank", 200)
    # Lower rank = better. Map rank 1 → 1.0, rank 100 → 0.0 (clamped).
    rank_term = max(0.0, min(1.0, (100 - rank) / 99.0))
    last5 = h2h.form_before(_form_team_name(tla), before_date, last_n=5)
    form_term = _form_points(last5) / 15.0  # 0..1
    return 0.7 * rank_term + 0.3 * form_term


def quali_pct(tla: str, before_date: str) -> int:
    """Rough % chance the nation advances from its group (top 2 of 4).

    Approach: rank the 4 group teams by `strength` (same date bound), then
    map within-group rank to a probability band. Round to the nearest %.
    """
    letter, members = wc_data.group_for(tla)
    if not members:
        return 0
    scored = sorted(
        [(t, strength(t, before_date)) for t in members],
        key=lambda x: x[1],
        reverse=True,
    )
    # Rank 1..4 within the group.
    rank = next(i for i, (t, _) in enumerate(scored) if t == tla.upper())
    # Band table — top 2 advance, so rank 1-2 are favored.
    BANDS = {0: 88, 1: 68, 2: 32, 3: 14}
    base = BANDS[rank]
    # Adjust by relative gap to the median (sharpens for dominant favorites,
    # softens for tight groups). Half a strength point ≈ ±8% nudge.
    median_s = sorted(s for _, s in scored)[1:3]
    avg_mid = sum(median_s) / 2 if median_s else 0
    me_s = next(s for t, s in scored if t == tla.upper())
    nudge = round((me_s - avg_mid) * 16)
    return max(3, min(97, base + nudge))


def _qualified_48() -> list[str]:
    """The actual 48 qualified nations (derived from the group draw), not the
    first 48 keys of NATIONS — that used to leak non-qualified sides (ITA, DEN)
    into the strength ranking and skew the round predictions."""
    return sorted({t for pair in wc_data.GROUP_VENUES for t in pair})


def predicted_round(tla: str, before_date: str) -> str:
    """Bucket prediction for how far this team will go. Deterministic and
    grounded in the global strength ranking among the 48 qualified nations.
    """
    ranked = sorted(
        [(t, strength(t, before_date)) for t in _qualified_48()],
        key=lambda x: x[1],
        reverse=True,
    )
    try:
        pos = next(i for i, (t, _) in enumerate(ranked) if t == tla.upper())
    except StopIteration:
        return "Group stage"
    if pos == 0:
        return "Champions"
    if pos == 1:
        return "Final"
    if pos <= 3:
        return "Semi-final"
    if pos <= 7:
        return "Quarter-final"
    if pos <= 15:
        return "Round of 16"
    if pos <= 31:
        return "Round of 32"
    return "Group stage"
