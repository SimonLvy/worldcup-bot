"""Local reaction watcher — runs on YOUR PC so we don't burn GitHub Actions
minutes (the tournament would blow the 2,000/month budget in days).

It polls football-data every LOOP_MIN minutes, reacts to freshly-finished
matches, and sends each reaction to Telegram for you to post on TikTok.

  - In-memory dedup: a match is reacted to once per session (no repeats).
  - Startup catch-up: reacts to anything finished in the last --catchup-hours,
    so when you boot the PC in the morning the overnight results are waiting.
  - Runs only while the PC is on (you're around 8h-00h), which covers your
    active window. Overnight games get picked up by the morning catch-up.

Usage:
    python local_runner.py                  # watch loop (Ctrl+C to stop at night)
    python local_runner.py --catchup-hours 16
    python local_runner.py --once           # one sweep, then exit

You can also still generate the slower content by hand, once a day:
    python main.py --countdown --preview
    python main.py --nation-cron --preview
    python main.py --tomorrow --preview
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("DATA_MODE", "live")

import companion
from render import render_post
import notify

LOOP_MIN = 15          # poll cadence
WINDOW_BUFFER_MIN = 6  # overlap so a match never slips between polls


def _react_settled(start_utc, end_utc, seen: set[str]) -> int:
    """React to every FINISHED match whose settle time is in (start, end] and
    that we haven't already handled this session. Returns count reacted."""
    n = 0
    for mid in companion.finished_match_ids(start_utc, end_utc):
        if mid in seen:
            continue
        try:
            post = companion.build_reaction_post(mid)
            if not post:
                continue
            result = render_post(post)
            notify.send_preview(post, result["upload_paths"])
            seen.add(mid)
            h, a, ac = post["home"], post["away"], post["actual"]
            print(f"  [{datetime.now():%H:%M}] reacted → {h['name']} "
                  f"{ac['home']}-{ac['away']} {a['name']}  ({post['verdict']})")
            n += 1
        except Exception as exc:  # noqa: BLE001 — one bad match must not stop the watch
            print(f"  [warn] match {mid} failed: {exc!r}")
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catchup-hours", type=float, default=16.0,
                    help="On start, react to matches finished in the last N hours.")
    ap.add_argument("--once", action="store_true",
                    help="Do one catch-up sweep and exit (no loop).")
    args = ap.parse_args()

    seen: set[str] = set()
    now = datetime.now(timezone.utc)

    print(f"[start] catch-up sweep: matches finished in the last {args.catchup_hours:g}h…")
    got = _react_settled(now - timedelta(hours=args.catchup_hours), now, seen)
    print(f"[start] {got} reaction(s) sent." if got else "[start] nothing finished recently.")

    if args.once:
        return 0

    print(f"[watch] polling every {LOOP_MIN} min. Leave this open while your PC is on. "
          f"Ctrl+C to stop (e.g. at bedtime).")
    try:
        while True:
            time.sleep(LOOP_MIN * 60)
            now = datetime.now(timezone.utc)
            _react_settled(now - timedelta(minutes=LOOP_MIN + WINDOW_BUFFER_MIN), now, seen)
    except KeyboardInterrupt:
        print("\n[stop] watcher stopped. See you tomorrow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
