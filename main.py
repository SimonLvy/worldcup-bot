"""Orchestrator: fetch → render → approve → publish.

Modes:
  python main.py                       # mock match (group)
  python main.py knockout              # mock match (knockout)
  python main.py <fixture_id>          # one specific live match
  python main.py --tomorrow            # auto-pick every match of tomorrow
  python main.py --date 2026-06-12     # all matches on that date
  python main.py --countdown           # today's J-X countdown post (companion)

Designed to run daily via GitHub Actions cron. Handles "no matches today"
by exiting cleanly.

Approval flow:
  - If TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID are set → Telegram (mobile).
  - Otherwise falls back to terminal o/n prompt.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta

# Windows console is cp1252; our captions/logs contain emoji + accents.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import companion
import config
import fetch_match as fm
from render import render_post
from publish import build_caption, publish


# ---------------------------------------------------------------------------
# Approval — Telegram if configured, terminal otherwise.
# ---------------------------------------------------------------------------
def _telegram_available() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def ask_approval(match: dict, slide_paths: list) -> bool:
    if _telegram_available():
        try:
            import notify
            return notify.send_slides_with_approval(match, slide_paths)
        except Exception as exc:  # noqa: BLE001 — never block on notif glitch
            print(f"[warn] Telegram approval failed ({exc!r}), falling back to terminal")

    # If there's no interactive TTY (CI / GitHub Actions / cron), default to
    # NO so we never silently publish — slides stay in the artifact.
    if not sys.stdin.isatty():
        print("[info] no interactive terminal — defaulting to 'do not publish'.")
        return False

    answer = input("\nPublish these slides? [o/n] ").strip().lower()
    return answer in ("o", "oui", "y", "yes")


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
# Preview branch — shared by match + countdown
# ---------------------------------------------------------------------------
def _send_preview_to_telegram(post: dict, slide_paths: list) -> None:
    """Send post slides as a preview (no buttons). Silent failure on Telegram."""
    if not _telegram_available():
        print("[preview] no Telegram configured — slides remain in output/.")
        return
    try:
        import notify
        notify.send_preview(post, slide_paths)
        print("[preview] sent to Telegram.")
    except Exception as exc:  # noqa: BLE001
        print(f"[preview] Telegram send failed: {exc!r}")


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

    # Preview mode: send slides to Telegram, no approval, no publish.
    if preview:
        _send_preview_to_telegram(match, slides)
        return 0

    print("[3/4] Review")
    for p in slides:
        print(f"      {p}")

    if config.REQUIRE_APPROVAL and not ask_approval(match, slides):
        print("Publishing cancelled. PNGs remain in output/.")
        return 0

    print("[4/4] Publishing…")
    caption = build_caption(match)
    try:
        results = publish(slides, caption, config.PUBLISH_TARGETS)
    except NotImplementedError as exc:
        print(f"[info] Publishing not configured: {exc}")
        print(f"       Slides are ready for manual upload in {result['source_dir']}")
        return 0

    for target, res in results.items():
        print(f"      {target}: {res}")
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

    # Preview mode: send to Telegram, no approval, no publish.
    if preview:
        _send_preview_to_telegram(post, slides)
        return 0

    print("[3/4] Review")
    for p in slides:
        print(f"      {p}")

    if config.REQUIRE_APPROVAL and not ask_approval(post, slides):
        print("Publishing cancelled. PNGs remain in output/.")
        return 0

    print("[4/4] Publishing…")
    # For companion posts the publish layer is not wired yet — they get manually
    # posted from the artifact for now. Exit cleanly.
    print("[info] Companion post publishing not wired yet — PNGs ready for manual upload.")
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

    if preview:
        _send_preview_to_telegram(post, slides)
        return 0

    print("[3/4] Review")
    for p in slides:
        print(f"      {p}")
    if config.REQUIRE_APPROVAL and not ask_approval(post, slides):
        print("Publishing cancelled. PNGs remain in output/.")
        return 0
    print("[4/4] Publishing…")
    print("[info] Companion post publishing not wired yet — PNGs ready for manual upload.")
    return 0


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

    if preview:
        _send_preview_to_telegram(post, slides)
        return 0

    print("[3/4] Review")
    for p in slides:
        print(f"      {p}")

    if config.REQUIRE_APPROVAL and not ask_approval(post, slides):
        print("Publishing cancelled. PNGs remain in output/.")
        return 0

    print("[4/4] Publishing…")
    print("[info] Companion post publishing not wired yet — PNGs ready for manual upload.")
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
        from datetime import datetime, timezone
        from wc_data import NATION_PUBLISH_ORDER
        # 48 nations × 6h slots = 12 days. Starting 2026-06-05 18:00 UTC, the
        # last profile lands ~17 Jun — around the end of matchday 1.
        START = datetime(2026, 6, 5, 18, 0, tzinfo=timezone.utc)
        SLOT_HOURS = 6
        now = datetime.now(timezone.utc)
        delta_h = (now - START).total_seconds() / 3600
        if delta_h < 0:
            print(f"[nation-cron] campaign starts {START.isoformat()} — too early ({delta_h:.1f}h).")
            return 0
        slot = int(delta_h // SLOT_HOURS)
        if slot >= len(NATION_PUBLISH_ORDER):
            print(f"[nation-cron] campaign over (slot {slot} ≥ {len(NATION_PUBLISH_ORDER)}).")
            return 0
        tla = NATION_PUBLISH_ORDER[slot]
        print(f"[nation-cron] slot {slot+1}/{len(NATION_PUBLISH_ORDER)} — {tla}")
        return process_nation(tla, preview=args.preview)

    if args.nation:
        return process_nation(args.nation, preview=args.preview)

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
