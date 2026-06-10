"""Local all-in-one runner — runs on YOUR PC, on demand, so we don't burn
GitHub Actions minutes. ONE command sends everything new to Telegram:

    python local_runner.py

Each run pushes, with no repeats (it remembers what it already sent):
  - REACTIONS  : every match that just finished (result vs your call)
  - PREVIEWS   : the 7-slide deep-dive for every match kicking off soon
  - COUNTDOWN  : today's J-X teaser, until kickoff

Run it whenever you sit down at the PC. Overnight games are picked up the
next time you run it. Nothing runs in the background, nothing is on 24/7.

Options:
    python local_runner.py --no-previews   # skip the heavy match previews
    python local_runner.py --watch         # keep polling every 15 min (Ctrl+C to stop)
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
import fetch_match as fm
from render import render_post
import notify

LOOP_MIN = 15
REACT_LOOKBACK_H = 30.0    # how far back to scan for finished matches
PREVIEW_HORIZON_H = 30.0   # how far ahead to preview upcoming matches
STATE_FILE = Path(__file__).resolve().parent / "data" / "sent_posts.json"


def _load_sent() -> set[str]:
    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_sent(sent: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(sorted(sent)), encoding="utf-8")


def _send(post: dict, sent: set[str], key: str, label: str) -> bool:
    if key in sent:
        return False
    result = render_post(post)
    slides = result.get("upload_paths") or []
    if not slides:
        return False
    notify.send_preview(post, slides)
    sent.add(key)
    _save_sent(sent)
    print(f"  [{datetime.now():%H:%M}] sent → {label}")
    return True


def _do_reactions(sent: set[str]) -> int:
    now = datetime.now(timezone.utc)
    ids = companion.finished_match_ids(now - timedelta(hours=REACT_LOOKBACK_H), now)
    n = 0
    for mid in ids:
        try:
            post = companion.build_reaction_post(mid)
            if not post:
                continue
            h, a, ac = post["home"], post["away"], post["actual"]
            label = f"REACTION {h['name']} {ac['home']}-{ac['away']} {a['name']} ({post['verdict']})"
            n += _send(post, sent, f"react-{mid}", label)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] reaction {mid} failed: {exc!r}")
    return n


def _do_previews(sent: set[str]) -> int:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=PREVIEW_HORIZON_H)
    n = 0
    for m in sorted(fm.list_matches(), key=lambda x: x["utcDate"]):
        try:
            ko = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        except Exception:
            continue
        if not (now < ko <= horizon):
            continue
        key = f"preview-{m['id']}"
        if key in sent:
            continue
        try:
            post = fm.fetch_match(str(m["id"]))
            if not post:
                continue
            label = f"PREVIEW {post['home']['name']} vs {post['away']['name']}"
            n += _send(post, sent, key, label)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] preview {m['id']} failed: {exc!r}")
    return n


def _do_countdown(sent: set[str]) -> int:
    try:
        post = companion.build_countdown_post()
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] countdown failed: {exc!r}")
        return 0
    if not post:
        return 0
    return int(_send(post, sent, post["post_id"], f"COUNTDOWN {post.get('days_label', '')}"))


def _sweep(sent: set[str], do_previews: bool) -> int:
    total = 0
    total += _do_reactions(sent)
    total += _do_countdown(sent)
    if do_previews:
        total += _do_previews(sent)
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-previews", action="store_true", help="Skip the heavy match previews.")
    ap.add_argument("--watch", action="store_true", help="Keep polling every 15 min (Ctrl+C to stop).")
    args = ap.parse_args()

    sent = _load_sent()
    print("[run] checking for anything new to send…")
    got = _sweep(sent, do_previews=not args.no_previews)
    print(f"[done] {got} new post(s) sent to Telegram." if got
          else "[done] nothing new since last run.")

    if not args.watch:
        return 0

    print(f"[watch] polling every {LOOP_MIN} min. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(LOOP_MIN * 60)
            _sweep(sent, do_previews=not args.no_previews)
    except KeyboardInterrupt:
        print("\n[stop] watcher stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
