"""Pull /competitions/WC/matches from football-data and append a fresh
MATCH_KICKOFF_UTC + GROUP_PAIR_ID block to wc_data.py.

Run once whenever FIFA tweaks the official schedule. Idempotent: removes
any previously-generated block before appending the new one.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from fetch_match import list_matches


GROUP_LETTERS = {f"GROUP_{c}": c for c in "ABCDEFGHIJKL"}

START_MARKER = "# ===== AUTO-GENERATED SCHEDULE — DO NOT EDIT BY HAND ====="
END_MARKER = "# ===== END AUTO-GENERATED SCHEDULE ====="


def render_block(matches: list[dict]) -> str:
    matches = sorted(matches, key=lambda m: m["utcDate"])
    by_stage = defaultdict(list)
    for m in matches:
        by_stage[m["stage"]].append(m)

    lines = [
        START_MARKER,
        f"# Source: football-data.org /competitions/WC/matches ({len(matches)} fixtures).",
        "# Regenerate via `python _gen_schedule.py` whenever the official schedule changes.",
        "",
        "MATCH_KICKOFF_UTC: dict[int, str] = {",
    ]
    for stage in ("GROUP_STAGE", "LAST_32", "LAST_16", "QUARTER_FINALS",
                  "SEMI_FINALS", "THIRD_PLACE", "FINAL"):
        ms = by_stage.get(stage, [])
        if not ms:
            continue
        lines.append(f"    # ----- {stage} ({len(ms)}) -----")
        for m in ms:
            home = m["homeTeam"].get("tla") or "TBD"
            away = m["awayTeam"].get("tla") or "TBD"
            grp = GROUP_LETTERS.get(m.get("group") or "", "")
            tag = f"{grp} · " if grp else ""
            lines.append(f'    {m["id"]}: "{m["utcDate"]}",  # {tag}{home} vs {away}')
    lines += ["}", "", "GROUP_PAIR_ID: dict[frozenset[str], int] = {"]
    for m in by_stage.get("GROUP_STAGE", []):
        h, a = m["homeTeam"].get("tla"), m["awayTeam"].get("tla")
        if not h or not a:
            continue
        grp = GROUP_LETTERS.get(m.get("group") or "", "?")
        lines.append(f'    frozenset({{"{h}", "{a}"}}): {m["id"]},  # Group {grp}')
    lines += ["}", "", "MATCH_STAGE: dict[int, str] = {"]
    stage_short = {
        "GROUP_STAGE": "group", "LAST_32": "r32", "LAST_16": "r16",
        "QUARTER_FINALS": "qf", "SEMI_FINALS": "sf",
        "THIRD_PLACE": "third", "FINAL": "final",
    }
    for m in matches:
        lines.append(f'    {m["id"]}: "{stage_short[m["stage"]]}",')
    lines += ["}", "", END_MARKER, ""]
    return "\n".join(lines)


def main() -> int:
    block = render_block(list_matches())
    p = Path("wc_data.py")
    src = p.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER) + r"\n?",
                         re.DOTALL)
    if pattern.search(src):
        src = pattern.sub("", src).rstrip() + "\n"
        print("[gen] replaced existing schedule block")
    if not src.endswith("\n"):
        src += "\n"
    p.write_text(src + "\n" + block, encoding="utf-8")
    print(f"[gen] wrote {block.count(chr(10))} lines to {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
