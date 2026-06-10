"""Local reaction runner — runs on YOUR PC, on demand, so we don't burn
GitHub Actions minutes (the tournament would blow the 2,000/month budget).

You do NOT have to leave anything running. Just run it whenever you sit down
at the PC and want results to post:

    python local_runner.py            # react to every NEW finished match, then exit

It remembers what it already reacted to (data/reacted_matches.json), so you
can run it as many times a day as you like and it only ever sends results you
haven't seen. Overnight games? It catches them the next time you run it.

Optional hands-off mode for a big match day (polls until you Ctrl+C):

    python local_runner.py --watch

Slow content stays on-demand too:
    python main.py --countdown --preview
    python main.py --nation-cron --preview
    python main.py --tomorrow --preview
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("DATA_MODE", "live")

import companion
from render import render_post
import notify

LOOP_MIN = 15
STATE_FILE = Path(__file__).resolve().parent / "data" / "reacted_matches.json"
# How far back to look for finished matches. Persistent dedup means a wide
# window is safe — it just makes sure nothing is missed between runs.
LOOKBACK_HOURS = 30.0


def _load_seen() -> set[str]:
    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_seen(seen: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(seen)), encoding="utf-8")


def _react_new(seen: set[str]) -> int:
    """React to every FINISHED match in the lookback window we haven't already
    handled. Persists state after each one. Returns count reacted."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=LOOKBACK_HOURS)
    n = 0
    for mid in companion.finished_match_ids(start, now):
        if mid in seen:
            continue
        try:
            post = companion.build_reaction_post(mid)
            if not post:
                continue
            result = render_post(post)
            notify.send_preview(post, result["upload_paths"])
            seen.add(mid)
            _save_seen(seen)
            h, a, ac = post["home"], post["away"], post["actual"]
            print(f"  [{datetime.now():%H:%M}] reacted → {h['name']} "
                  f"{ac['home']}-{ac['away']} {a['name']}  ({post['verdict']})")
            n += 1
        except Exception as exc:  # noqa: BLE001 — one bad match must not stop the run
            print(f"  [warn] match {mid} failed: {exc!r}")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true",
                    help="Keep polling every 15 min until Ctrl+C (hands-off match day).")
    args = ap.parse_args()

    seen = _load_seen()
    got = _react_new(seen)
    print(f"[done] {got} new reaction(s) sent to Telegram." if got
          else "[done] no new finished matches since last run.")

    if not args.watch:
        return 0

    print(f"[watch] polling every {LOOP_MIN} min. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(LOOP_MIN * 60)
            _react_new(seen)
    except KeyboardInterrupt:
        print("\n[stop] watcher stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
