"""Telegram notification + approval bridge.

Flow:
  1. Send a caption + the 7 slides as a media group to the configured chat.
  2. Send a separate message with two inline buttons: "Publish ✅" / "Cancel ❌".
  3. Poll Telegram's getUpdates for the callback for up to `timeout_minutes`.
  4. Return True if the user pressed Publish, False otherwise (cancel, timeout
     or unexpected error).

Config (in .env):
  TELEGRAM_BOT_TOKEN=123456:ABC...
  TELEGRAM_CHAT_ID=123456789

No external libraries beyond `requests` — keeps the dependency footprint small
and the install in GitHub Actions instant.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://api.telegram.org/bot{token}/{method}"
POLL_INTERVAL_S = 3
# Approval is fully manual — keep the runner alive long enough that the user
# can take their time. GitHub Actions free-tier jobs cap at 6h anyway.
DEFAULT_TIMEOUT_MIN = 240  # 4 hours


# ---------------------------------------------------------------------------
# Public entry point — called by main.py
# ---------------------------------------------------------------------------
def send_preview(post: dict, slide_paths: list[Path]) -> None:
    """Send slides + editorial pack as a PREVIEW (no buttons, no approval).

    Used by /preview command: the user just wants to see tomorrow's content
    early, not validate publication. The normal cron handles publishing.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env")

    # Prefix the status caption with a clear "PREVIEW" tag so it's distinguishable
    # from the real approval notifications.
    base = _caption(post)
    status = "👀 PREVIEW\n" + base
    _send_media_group(token, chat_id, slide_paths, status)

    try:
        _send_editorial_pack(token, chat_id, post)
    except Exception as exc:  # noqa: BLE001
        print(f"[telegram] editorial pack skipped: {exc!r}")


def send_slides_with_approval(
    post: dict,
    slide_paths: list[Path],
    timeout_minutes: int = DEFAULT_TIMEOUT_MIN,
) -> bool:
    """Send slides + editorial pack + approval buttons. Returns True if approved.

    Telegram sequence:
      1. Photo album (or single photo) with a short status caption
      2. Editorial pack message: ready-to-copy caption, hashtags, first comment
      3. Inline keyboard message with ✅ Publish / ❌ Cancel
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env")

    status_caption = _caption(post)
    _send_media_group(token, chat_id, slide_paths, status_caption)

    # Editorial pack — separate messages per platform so each block can be
    # tap-copied independently into IG / TikTok.
    try:
        _send_editorial_pack(token, chat_id, post)
    except Exception as exc:  # noqa: BLE001 — never block on editorial glitch
        print(f"[telegram] editorial pack skipped: {exc!r}")

    # Unique callback tag per post → so leftover callbacks from prior runs
    # don't accidentally approve a different post.
    tag = post.get("match_id") or post.get("post_id", "post")
    msg_id = _send_approval_buttons(token, chat_id, tag)
    print(f"[telegram] approval buttons sent (message {msg_id})")

    decision = _wait_for_decision(token, tag, timeout_minutes)
    _acknowledge(token, chat_id, msg_id, decision)
    return decision is True


def _send_editorial_pack(token: str, chat_id: str, post: dict) -> None:
    """Send 3 paste-ready messages: TikTok caption, IG caption, IG first comment.

    No headers, no labels — each message is a single <pre> block ready to
    copy whole. Order is always: TikTok → Instagram → IG first comment.
    """
    import captions

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    pack = captions.for_telegram(post)
    for body in (pack["tiktok_text"], pack["instagram_text"], pack["ig_first_comment"]):
        if not body:
            continue
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
    return _caption_match(post)


def _caption_stadium(post: dict) -> str:
    parts = [
        f"🏟 {post.get('stadium', '?')}",
        f"📍 {post.get('city', '?')}, {post.get('country', '?')}",
        f"👥 Capacity: {post.get('capacity', '?'):,}" if post.get('capacity') else "",
        f"⚽️ {len(post.get('matches') or [])} match(es) scheduled",
        "",
        "Validate to publish, or cancel.",
    ]
    return "\n".join(p for p in parts if p)


def _caption_countdown(post: dict) -> str:
    parts = [
        f"⏳ {post.get('days_label', 'COUNTDOWN')}",
        f"🗓 Kickoff: {post.get('kickoff_date_label', '?')}",
        "",
        "Validate to publish, or cancel.",
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
        "",
        "Validate to publish, or cancel.",
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


def _send_approval_buttons(token: str, chat_id: str, tag: str) -> int:
    """Send a small message with inline Publish/Cancel buttons. Return message_id."""
    import json as _json
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Publish",  "callback_data": f"ok::{tag}"},
            {"text": "❌ Cancel",   "callback_data": f"no::{tag}"},
        ]]
    }
    r = requests.post(
        BASE.format(token=token, method="sendMessage"),
        data={
            "chat_id": chat_id,
            "text": "Your call?",
            "reply_markup": _json.dumps(keyboard),
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["result"]["message_id"]


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------
def _wait_for_decision(token: str, tag: str, timeout_minutes: int) -> bool | None:
    """Poll getUpdates until a callback for this tag arrives or we time out.

    Returns True for Publish, False for Cancel, None on timeout.
    """
    deadline = time.time() + timeout_minutes * 60
    last_update_id = _drain_existing_updates(token)

    while time.time() < deadline:
        try:
            r = requests.get(
                BASE.format(token=token, method="getUpdates"),
                params={"offset": last_update_id + 1, "timeout": POLL_INTERVAL_S},
                timeout=POLL_INTERVAL_S + 10,
            )
            r.raise_for_status()
            for upd in r.json().get("result", []):
                last_update_id = max(last_update_id, upd["update_id"])
                cb = upd.get("callback_query")
                if not cb:
                    continue
                data = cb.get("data", "")
                if not data.endswith(f"::{tag}"):
                    continue
                _answer_callback(token, cb["id"])
                if data.startswith("ok::"):
                    return True
                if data.startswith("no::"):
                    return False
        except requests.RequestException as exc:
            print(f"[telegram] polling glitch: {exc!r} — retrying")
            time.sleep(POLL_INTERVAL_S)
    return None  # timeout


def _drain_existing_updates(token: str) -> int:
    """Return the highest update_id currently pending (so we ignore stale clicks)."""
    try:
        r = requests.get(
            BASE.format(token=token, method="getUpdates"),
            params={"timeout": 0},
            timeout=10,
        )
        r.raise_for_status()
        ups = r.json().get("result", [])
        return max((u["update_id"] for u in ups), default=0)
    except Exception:
        return 0


def _answer_callback(token: str, callback_id: str) -> None:
    """Tell Telegram the button click was received (stops the loading spinner)."""
    try:
        requests.post(
            BASE.format(token=token, method="answerCallbackQuery"),
            data={"callback_query_id": callback_id},
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Acknowledge — edit the buttons message so it's clear what happened.
# ---------------------------------------------------------------------------
def _acknowledge(token: str, chat_id: str, msg_id: int, decision: bool | None) -> None:
    if decision is True:
        text = "✅ Approved — publishing…"
    elif decision is False:
        text = "❌ Cancelled — slides remain in output/."
    else:
        text = "⏱ Timed out — no action taken."
    try:
        requests.post(
            BASE.format(token=token, method="editMessageText"),
            data={"chat_id": chat_id, "message_id": msg_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI smoke test — sends a "ping" with two buttons, polls for 2 minutes.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env")
        sys.exit(1)
    print("[ping] sending test buttons (you have 2 min to click)…")
    msg_id = _send_approval_buttons(token, chat_id, "ping")
    decision = _wait_for_decision(token, "ping", timeout_minutes=2)
    _acknowledge(token, chat_id, msg_id, decision)
    print(f"[ping] decision: {decision}")
