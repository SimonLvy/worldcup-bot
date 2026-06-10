"""Local all-in-one runner — runs on YOUR PC, on demand, so we don't burn
GitHub Actions minutes. ONE command sends everything new to Telegram:

    python local_runner.py

Each run pushes, with no repeats (it remembers what it already sent in
data/sent_posts.json):
  - REACTIONS : every match that just finished (result vs your call)
  - NATION    : the next nation profile, throttled to ~2/day
  - PREVIEWS  : the 7-slide deep-dive for every match kicking off soon
  - COUNTDOWN : today's J-X teaser, until kickoff

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
REACT_LOOKBACK_H = 30.0     # how far back to scan for finished matches
PREVIEW_HORIZON_H = 30.0    # how far ahead to preview upcoming matches
NATION_MIN_GAP_H = 10.0     # min spacing between nation posts (~2/day)
STATE_FILE = Path(__file__).resolve().parent / "data" / "sent_posts.json"


def _load_state() -> dict:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):  # migrate the old flat-list format
            return {"sent": set(data), "last_nation": None}
        return {"sent": set(data.get("sent", [])), "last_nation": data.get("last_nation")}
    except Exception:
        return {"sent": set(), "last_nation": None}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(
        {"sent": sorted(state["sent"]), "last_nation": state["last_nation"]}),
        encoding="utf-8")


def _send(post: dict, state: dict, key: str, label: str) -> bool:
    if key in state["sent"]:
        return False
    result = render_post(post)
    slides = result.get("upload_paths") or []
    if not slides:
        return False
    notify.send_preview(post, slides)
    state["sent"].add(key)
    _save_state(state)
    print(f"  [{datetime.now():%H:%M}] sent → {label}")
    return True


def _do_reactions(state: dict) -> int:
    now = datetime.now(timezone.utc)
    n = 0
    for mid in companion.finished_match_ids(now - timedelta(hours=REACT_LOOKBACK_H), now):
        try:
            post = companion.build_reaction_post(mid)
            if not post:
                continue
            h, a, ac = post["home"], post["away"], post["actual"]
            label = f"REACTION {h['name']} {ac['home']}-{ac['away']} {a['name']} ({post['verdict']})"
            n += _send(post, state, f"react-{mid}", label)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] reaction {mid} failed: {exc!r}")
    return n


def _do_nation(state: dict) -> int:
    """Send the next unsent nation, but no more than one per NATION_MIN_GAP_H
    so running the command often doesn't blast all 48 in a day."""
    last = state.get("last_nation")
    if last:
        try:
            gap_h = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() / 3600
            if gap_h < NATION_MIN_GAP_H:
                return 0
        except Exception:
            pass
    from wc_data import NATION_PUBLISH_ORDER
    for tla in NATION_PUBLISH_ORDER:
        try:
            post = companion.build_nation_post(tla)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] nation {tla} failed: {exc!r}")
            continue
        if not post or post["post_id"] in state["sent"]:
            continue
        if _send(post, state, post["post_id"], f"NATION {post['name']}"):
            state["last_nation"] = datetime.now(timezone.utc).isoformat()
            _save_state(state)
            return 1
        return 0
    return 0


def _do_previews(state: dict) -> int:
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
        if key in state["sent"]:
            continue
        try:
            post = fm.fetch_match(str(m["id"]))
            if not post:
                continue
            label = f"PREVIEW {post['home']['name']} vs {post['away']['name']}"
            n += _send(post, state, key, label)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] preview {m['id']} failed: {exc!r}")
    return n


def _do_countdown(state: dict) -> int:
    try:
        post = companion.build_countdown_post()
    except Exception as exc:  # noqa: BLE001
        print(f"  [warn] countdown failed: {exc!r}")
        return 0
    if not post:
        return 0
    return int(_send(post, state, post["post_id"], f"COUNTDOWN {post.get('days_label', '')}"))


def _sweep(state: dict, do_previews: bool) -> int:
    total = _do_reactions(state)
    total += _do_nation(state)
    total += _do_countdown(state)
    if do_previews:
        total += _do_previews(state)
    return total


def _seed_nations_through(state: dict, tla: str) -> None:
    """One-time catch-up: mark every nation up to and including `tla` (in the
    publish order) as already sent, so the local runner resumes where the
    GitHub cron left off instead of restarting from Mexico."""
    from wc_data import NATION_PUBLISH_ORDER
    tla = tla.strip().upper()
    if tla not in NATION_PUBLISH_ORDER:
        print(f"[seed] '{tla}' is not a known nation TLA. Order: {', '.join(NATION_PUBLISH_ORDER)}")
        return
    idx = NATION_PUBLISH_ORDER.index(tla)
    done = NATION_PUBLISH_ORDER[:idx + 1]
    for t in done:
        state["sent"].add(f"WC2026-N-{t}")
    state["last_nation"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)
    nxt = NATION_PUBLISH_ORDER[idx + 1] if idx + 1 < len(NATION_PUBLISH_ORDER) else "(none, campaign done)"
    print(f"[seed] marked {len(done)} nations as already sent (through {tla}). Next up: {nxt}.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-previews", action="store_true", help="Skip the heavy match previews.")
    ap.add_argument("--watch", action="store_true", help="Keep polling every 15 min (Ctrl+C to stop).")
    ap.add_argument("--nations-sent-through", metavar="TLA", default=None,
                    help="One-time: mark all nations up to this one as already done "
                         "(e.g. GER for Germany), so it resumes from the next one.")
    args = ap.parse_args()

    state = _load_state()

    if args.nations_sent_through:
        _seed_nations_through(state, args.nations_sent_through)
        return 0

    print("[run] checking for anything new to send…")
    got = _sweep(state, do_previews=not args.no_previews)
    print(f"[done] {got} new post(s) sent to Telegram." if got
          else "[done] nothing new since last run.")

    if not args.watch:
        return 0

    print(f"[watch] polling every {LOOP_MIN} min. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(LOOP_MIN * 60)
            _sweep(state, do_previews=not args.no_previews)
    except KeyboardInterrupt:
        print("\n[stop] watcher stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
