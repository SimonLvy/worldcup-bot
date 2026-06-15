"""Telegram delivery bridge.

The bot renders a post and sends it to the configured chat for the user to post
manually: a caption + the slides as a media group, then the paste-ready
editorial pack (TikTok / Instagram blocks). No approval step.

Config (in .env):
  TELEGRAM_BOT_TOKEN=123456:ABC...
  TELEGRAM_CHAT_ID=123456789

No external libraries beyond `requests` — keeps the dependency footprint small
and the install in GitHub Actions instant.
"""
from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.telegram.org/bot{token}/{method}"


# ---------------------------------------------------------------------------
# Public entry point — called by main.py
# ---------------------------------------------------------------------------
def send_post(post: dict, slide_paths: list[Path]) -> None:
    """Send slides + the paste-ready editorial pack to Telegram for the user to
    post manually. No approval buttons. Raises only if Telegram isn't configured.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env")

    status = _caption(post)
    _send_media_group(token, chat_id, slide_paths, status)

    try:
        _send_editorial_pack(token, chat_id, post)
    except Exception as exc:  # noqa: BLE001
        print(f"[telegram] editorial pack skipped: {exc!r}")


def _send_editorial_pack(token: str, chat_id: str, post: dict) -> None:
    """Send ONE paste-ready caption: the TikTok block (text + 5 hashtags).

    The account is TikTok-only, so the old 3-message pack (TikTok / IG / IG
    first comment) was noise. One <pre> block, tap-and-hold to copy whole.
    """
    import captions

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    pack = captions.for_telegram(post)
    body = pack.get("tiktok_text")
    if not body:
        return
    requests.post(
        BASE.format(token=token, method="sendMessage"),
        data={
            "chat_id": chat_id,
            "text": f"<pre>{esc(body)}</pre>",
            "parse_mode": "HTML",
        },
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------
def _caption(post: dict) -> str:
    """Build a human-readable caption per post type."""
    post_type = post.get("post_type", "match")
    if post_type == "countdown":
        return _caption_countdown(post)
    if post_type == "stadium":
        return _caption_stadium(post)
    if post_type == "nation":
        return _caption_nation(post)
    if post_type == "reaction":
        return _caption_reaction(post)
    return _caption_match(post)


def _caption_reaction(post: dict) -> str:
    h, a = post.get("home", {}), post.get("away", {})
    ac, pr = post.get("actual", {}), post.get("predicted", {})
    parts = [
        f"⚽️ FT: {h.get('name','?')} {ac.get('home')}-{ac.get('away')} {a.get('name','?')}",
        f"🤖 Called: {pr.get('home')}-{pr.get('away')} · verdict: {post.get('verdict','?').upper()}",
    ]
    return "\n".join(p for p in parts if p)


def _caption_nation(post: dict) -> str:
    parts = [
        f"🏳 {post.get('name', '?')}",
        f"💬 {post.get('nickname', '')}" if post.get('nickname') else "",
        f"🌍 {post.get('confederation', '')} · Group {post.get('group_letter', '?')}",
        f"📊 FIFA #{post.get('fifa_rank', '?')}",
        f"🎯 Quali {post.get('quali_pct', '?')}% · {post.get('predicted_round', '?')}",
    ]
    return "\n".join(p for p in parts if p)


def _caption_stadium(post: dict) -> str:
    parts = [
        f"🏟 {post.get('stadium', '?')}",
        f"📍 {post.get('city', '?')}, {post.get('country', '?')}",
        f"👥 Capacity: {post.get('capacity', '?'):,}" if post.get('capacity') else "",
        f"⚽️ {len(post.get('matches') or [])} match(es) scheduled",
    ]
    return "\n".join(p for p in parts if p)


def _caption_countdown(post: dict) -> str:
    parts = [
        f"⏳ {post.get('days_label', 'COUNTDOWN')}",
        f"🗓 Kickoff: {post.get('kickoff_date_label', '?')}",
    ]
    return "\n".join(p for p in parts if p)


def _caption_match(match: dict) -> str:
    home, away = match["home"]["name"], match["away"]["name"]
    kickoff_local = match.get("kickoff_local_label", "")
    kickoff_utc = match.get("kickoff_utc_label", "")
    venue = match.get("venue", {}).get("stadium", "")
    if match.get("stage") == "knockout":
        round_name = match.get("knockout", {}).get("round", "Knockout stage")
        line2 = round_name
    else:
        line2 = f"Group {match.get('group','?')} · Matchday {match.get('match_number_in_group','?')}"
    parts = [
        f"⚽️ {home} vs {away}",
        line2,
        f"⏰ {kickoff_local} ({kickoff_utc})" if kickoff_utc else f"⏰ {kickoff_local}",
        f"📍 {venue}" if venue else "",
    ]
    return "\n".join(p for p in parts if p)


def _send_media_group(token: str, chat_id: str, paths: list[Path], caption: str) -> None:
    """Send up to 10 photos to the chat.

    Telegram's sendMediaGroup endpoint requires 2-10 items, so for singletons
    (e.g. countdown posts) we use sendPhoto instead.
    """
    paths = list(paths)[:10]
    if not paths:
        return

    if len(paths) == 1:
        with open(paths[0], "rb") as f:
            r = requests.post(
                BASE.format(token=token, method="sendPhoto"),
                data={"chat_id": chat_id, "caption": caption},
                files={"photo": f},
                timeout=60,
            )
            if not r.ok:
                print(f"[telegram] sendPhoto error {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
        return

    media = []
    files = {}
    for i, p in enumerate(paths):
        attach_name = f"photo{i}"
        item = {"type": "photo", "media": f"attach://{attach_name}"}
        if i == 0:  # caption on the first photo
            item["caption"] = caption
        media.append(item)
        files[attach_name] = open(p, "rb")
    try:
        import json as _json
        r = requests.post(
            BASE.format(token=token, method="sendMediaGroup"),
            data={"chat_id": chat_id, "media": _json.dumps(media)},
            files=files,
            timeout=120,
        )
        if not r.ok:
            print(f"[telegram] sendMediaGroup error {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
    finally:
        for f in files.values():
            f.close()
