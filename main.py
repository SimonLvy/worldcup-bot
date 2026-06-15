"""Orchestrator: fetch → render → send to Telegram for manual posting.

Modes:
  python main.py                       # mock match (group)
  python main.py knockout              # mock match (knockout)
  python main.py <fixture_id>          # one specific live match
  python main.py --tomorrow            # every match of tomorrow
  python main.py --date 2026-06-12     # all matches on that date
  python main.py --countdown           # today's J-X countdown post
  python main.py --nation-cron         # next nation in the showcase campaign
  python main.py --reactions           # post-match reactions for finished games

Designed to run via GitHub Actions cron. Every post is rendered and sent to
Telegram (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID); the user posts it manually.
There is no approval or auto-publish step.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

# Windows console is cp1252; our captions/logs contain emoji + accents.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import companion
import fetch_match as fm
from render import render_post


# ---------------------------------------------------------------------------
# Telegram delivery — the bot generates content and sends it for the user to
# post manually. There is no approval or auto-publish step.
# ---------------------------------------------------------------------------
def _telegram_available() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


# ---------------------------------------------------------------------------
# Nation campaign state — committed back to the repo by the workflow so the
# showcase drip never re-sends or drops a nation across cron runs.
# ---------------------------------------------------------------------------
NATION_STATE_FILE = Path(__file__).resolve().parent / "data" / "nation_campaign.json"


def _load_nation_state() -> set[str]:
    """TLAs of nations already sent in the showcase campaign."""
    try:
        data = json.loads(NATION_STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("sent", []))
    except Exception:
        return set()


def _save_nation_state(sent: set[str]) -> None:
    NATION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    NATION_STATE_FILE.write_text(
        json.dumps({"sent": sorted(sent)}, ensure_ascii=False, indent=2),
        encoding="utf-8")


# ---------------------------------------------------------------------------
# Match selection
# ---------------------------------------------------------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tomorrow", action="store_true")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--countdown", action="store_true",
                        help="Generate today's J-X countdown companion post.")
    parser.add_argument("--stadium", type=str, default=None,
                        help="Generate a stadium showcase post for the given venue name "
                             "(e.g. \"Estadio Azteca\").")
    parser.add_argument("--stadium-all", action="store_true",
                        help="Generate stadium showcase posts for all 16 venues.")
    parser.add_argument("--stadium-cron", action="store_true",
                        help="Pick the next stadium based on the publish schedule "
                             "(8h slots starting STADIUM_CAMPAIGN_START_UTC). "
                             "Designed for the GitHub Actions cron.")
    parser.add_argument("--nation", type=str, default=None,
                        help="Generate a nation showcase post for the given TLA "
                             "(e.g. \"FRA\", \"BRA\"). Renders 3 slides with the "
                             "per-nation palette.")
    parser.add_argument("--nation-cron", action="store_true",
                        help="Pick the next nation by the publish schedule "
                             "(6h slots, 4/day, starting the nation campaign). "
                             "Designed for the GitHub Actions cron.")
    parser.add_argument("--reaction", type=str, default=None,
                        help="Build a post-match reaction for one finished fixture id "
                             "(manual / testing).")
    parser.add_argument("--reactions", action="store_true",
                        help="Cron mode: react to every match that just finished in "
                             "the last polling window. Designed for the reaction cron.")
    parser.add_argument("--preview", action="store_true",
                        help="Preview mode: send slides to Telegram without "
                             "approval buttons, never publish.")
    parser.add_argument("positional", nargs="?", default=None)
    return parser.parse_args(argv)


def select_match_refs(args: argparse.Namespace) -> list[str | None]:
    """Return a list of match references to process (one per match).

    Empty list → exit 0 with "nothing to do".
    [None] → mock mode (handled by fetch_match).
    [str, ...] → live mode, one or more fixture ids.
    """
    target_date: date | None = None
    if args.tomorrow:
        target_date = date.today() + timedelta(days=1)
    elif args.date:
        target_date = date.fromisoformat(args.date)

    if target_date:
        os.environ["DATA_MODE"] = "live"
        raws = fm.find_matches_on(target_date)
        print(f"[info] {len(raws)} match(es) on {target_date.isoformat()}")
        return [str(r["id"]) for r in raws]

    return [args.positional]


# ---------------------------------------------------------------------------
# Telegram delivery — shared by every post type
# ---------------------------------------------------------------------------
def _send_to_telegram(post: dict, slide_paths: list) -> None:
    """Send slides + paste-ready caption to Telegram for manual posting.
    Silent failure so a Telegram glitch never crashes the run."""
    if not _telegram_available():
        print("[telegram] not configured — slides remain in output/.")
        return
    try:
        import notify
        notify.send_post(post, slide_paths)
        print("[telegram] sent.")
    except Exception as exc:  # noqa: BLE001
        print(f"[telegram] send failed: {exc!r}")


# ---------------------------------------------------------------------------
# Pipeline for one match
# ---------------------------------------------------------------------------
def process_match(match_ref: str | None, *, preview: bool = False) -> int:
    print(f"\n{'='*60}")
    print(f"[1/4] Fetching match data… (ref={match_ref!r})")
    match = fm.fetch_match(match_ref)
    if match is None:
        print("No match found for this reference.")
        return 0
    print(f"      → {match['home']['name']} vs {match['away']['name']} "
          f"({match.get('kickoff_local_label', '?')}, {match['stage']})")

    print("[2/4] Rendering slides…")
    result = render_post(match)
    slides = result["upload_paths"]
    if not slides:
        print("No slides rendered.")
        return 1
    print(f"      → {len(slides)} slides in {result['source_dir']}")

    match_json = result["source_dir"] / "match.json"
    match_json.write_text(json.dumps(match, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[3/3] Sending to Telegram…")
    _send_to_telegram(match, slides)
    return 0


# ---------------------------------------------------------------------------
# Pipeline for one companion post (countdown, nation, stadium, group)
# ---------------------------------------------------------------------------
def process_countdown(*, preview: bool = False) -> int:
    print(f"\n{'='*60}")
    print("[1/4] Building today's countdown post…")
    post = companion.build_countdown_post()
    if post is None:
        print("Outside the countdown window (J-10 to J-0). Nothing to do.")
        return 0
    print(f"      → {post['post_id']} — {post['days_label']}")

    print("[2/4] Rendering slide…")
    result = render_post(post)
    slides = result["upload_paths"]
    if not slides:
        print("No slides rendered.")
        return 1
    print(f"      → {len(slides)} slide(s) in {result['source_dir']}")

    post_json = result["source_dir"] / "post.json"
    post_json.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[3/3] Sending to Telegram…")
    _send_to_telegram(post, slides)
    return 0


def process_nation(tla: str, *, preview: bool = False) -> int:
    print(f"\n{'='*60}")
    print(f"[1/4] Building nation post for {tla!r}…")
    post = companion.build_nation_post(tla)
    if post is None:
        print(f"Unknown nation TLA {tla!r}. Nothing to do.")
        return 1
    print(f"      → {post['post_id']} — {post.get('name', '')}")

    print("[2/4] Rendering slides…")
    result = render_post(post)
    slides = result["upload_paths"]
    if not slides:
        print("No slides rendered.")
        return 1
    print(f"      → {len(slides)} slide(s) in {result['source_dir']}")

    post_json = result["source_dir"] / "post.json"
    post_json.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[3/3] Sending to Telegram…")
    _send_to_telegram(post, slides)
    return 0


def process_reaction(match_id: str, *, preview: bool = True) -> int:
    print(f"\n{'='*60}")
    print(f"[1/3] Building reaction for finished match {match_id!r}…")
    post = companion.build_reaction_post(match_id)
    if post is None:
        print("Match not finished yet (no score). Nothing to do.")
        return 0
    h, a = post["home"], post["away"]
    ac = post["actual"]
    print(f"      → {h['name']} {ac['home']}-{ac['away']} {a['name']} · verdict={post['verdict']}")

    print("[2/3] Rendering slides…")
    result = render_post(post)
    slides = result["upload_paths"]
    if not slides:
        print("No slides rendered.")
        return 1
    post_json = result["source_dir"] / "post.json"
    post_json.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[3/3] Sending to Telegram…")
    _send_to_telegram(post, slides)
    return 0


def process_reactions_cron(*, lookback_min: int = 35) -> int:
    """Poll for matches that finished in the last `lookback_min` minutes and
    react to each. Stateless: a match is only inside the window for ~one cron
    cycle, and the FINISHED check means we never react before the score exists.
    Manual posting tolerates the rare boundary double-send."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=lookback_min)
    ids = companion.finished_match_ids(start, now)
    if not ids:
        print(f"[reactions] no match settled in the last {lookback_min} min.")
        return 0
    print(f"[reactions] {len(ids)} freshly-finished match(es): {ids}")
    rc = 0
    for mid in ids:
        try:
            rc |= process_reaction(mid, preview=True)
        except Exception as exc:  # noqa: BLE001 — one bad match must not kill the batch
            print(f"[error] reaction {mid} failed: {exc!r}")
    return rc


def process_stadium(name: str, *, preview: bool = False) -> int:
    print(f"\n{'='*60}")
    print(f"[1/4] Building stadium post for {name!r}…")
    post = companion.build_stadium_post(name)
    if post is None:
        print(f"Unknown venue {name!r}. Nothing to do.")
        return 1
    print(f"      → {post['post_id']} — {post.get('city', '')}")

    print("[2/4] Rendering slides…")
    result = render_post(post)
    slides = result["upload_paths"]
    if not slides:
        print("No slides rendered.")
        return 1
    print(f"      → {len(slides)} slide(s) in {result['source_dir']}")

    post_json = result["source_dir"] / "post.json"
    post_json.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[3/3] Sending to Telegram…")
    _send_to_telegram(post, slides)
    return 0


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main() -> int:
    args = parse_args(sys.argv[1:])

    if args.countdown:
        return process_countdown(preview=args.preview)

    if args.stadium_all:
        from wc_data import VENUES
        rc = 0
        for name in VENUES.keys():
            try:
                rc |= process_stadium(name, preview=args.preview)
            except Exception as exc:  # noqa: BLE001
                print(f"[error] stadium {name!r} failed: {exc!r}")
        return rc

    if args.stadium_cron:
        from datetime import datetime, timezone
        from wc_data import STADIUM_PUBLISH_ORDER
        # 16 venues × 8h slots = 128h ≈ 5.3 days. Starting today (2026-06-04)
        # at 22:00 UTC, the last post lands ~37h before the opening match.
        START = datetime(2026, 6, 4, 22, 0, tzinfo=timezone.utc)
        SLOT_HOURS = 8
        now = datetime.now(timezone.utc)
        delta_h = (now - START).total_seconds() / 3600
        if delta_h < 0:
            print(f"[stadium-cron] campaign starts {START.isoformat()} — too early ({delta_h:.1f}h).")
            return 0
        slot = int(delta_h // SLOT_HOURS)
        if slot >= len(STADIUM_PUBLISH_ORDER):
            print(f"[stadium-cron] campaign over (slot {slot} ≥ {len(STADIUM_PUBLISH_ORDER)}).")
            return 0
        name = STADIUM_PUBLISH_ORDER[slot]
        print(f"[stadium-cron] slot {slot+1}/{len(STADIUM_PUBLISH_ORDER)} — {name}")
        return process_stadium(name, preview=args.preview)

    if args.stadium:
        return process_stadium(args.stadium, preview=args.preview)

    if args.nation_cron:
        from wc_data import NATION_PUBLISH_ORDER
        # Stateful drip: each fire sends the next nation not yet sent, in order.
        # The sent list is committed back to the repo by the workflow, so a
        # skipped or delayed cron run only delays the campaign — it never drops
        # a nation. (The old elapsed-time slot picker silently lost any slot
        # whose run didn't fire, e.g. Curaçao at the 4/day → 2/day cutover.)
        total = len(NATION_PUBLISH_ORDER)
        sent = _load_nation_state()
        nxt = next((t for t in NATION_PUBLISH_ORDER if t not in sent), None)
        if nxt is None:
            print(f"[nation-cron] campaign over — all {total} nations sent.")
            return 0
        print(f"[nation-cron] next unsent: {nxt} ({len(sent)}/{total} done)")
        rc = process_nation(nxt, preview=args.preview)
        if rc == 0:
            sent.add(nxt)
            _save_nation_state(sent)
            print(f"[nation-cron] state advanced → {len(sent)}/{total} sent.")
        return rc

    if args.nation:
        return process_nation(args.nation, preview=args.preview)

    if args.reactions:
        return process_reactions_cron()

    if args.reaction:
        return process_reaction(args.reaction, preview=True)

    refs = select_match_refs(args)
    if not refs:
        print("Nothing scheduled. See you tomorrow.")
        return 0

    for ref in refs:
        try:
            rc = process_match(ref, preview=args.preview)
            if rc != 0:
                print(f"[warn] match {ref} returned {rc}, continuing…")
        except Exception as exc:  # noqa: BLE001 — one bad match must not kill the batch
            print(f"[error] match {ref} failed: {exc!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
