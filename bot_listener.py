"""Telegram command listener — runs every 15 min in GitHub Actions.

Recognised commands (sent in the bot's chat by the configured user):
    /preview              → generate tomorrow's posts (countdown + matches)
    /preview YYYY-MM-DD   → generate posts for a specific date
    /help                 → list available commands

Most invocations exit fast (no command found, ~15-20s including setup).
When a command is detected, the workflow continues with playwright install +
main.py invocations.

State (last processed update_id) is persisted to bot_state.json, restored
across runs via GitHub Actions cache.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
STATE_PATH = Path("bot_state.json")

# Output the workflow consumes via $GITHUB_OUTPUT
HAS_COMMAND = False
TARGET_DATE = (date.today() + timedelta(days=1)).isoformat()


def _send(text: str) -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=15,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[send] failed: {exc!r}")


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"offset": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"offset": 0}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _emit_output(has_command: bool, target_date: str) -> None:
    """Pass results back to the workflow via GITHUB_OUTPUT."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        print(f"[output] has_command={has_command}, target_date={target_date}")
        return
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"has_command={'true' if has_command else 'false'}\n")
        f.write(f"target_date={target_date}\n")


def main() -> int:
    global HAS_COMMAND, TARGET_DATE

    if not TOKEN or not CHAT_ID:
        print("[error] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")
        _emit_output(False, TARGET_DATE)
        return 1

    state = _load_state()
    print(f"[state] starting offset: {state.get('offset', 0)}")

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={
                "offset": state.get("offset", 0),
                "timeout": 0,
                "allowed_updates": '["message"]',
            },
            timeout=20,
        )
        resp.raise_for_status()
        updates = resp.json().get("result", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[error] getUpdates failed: {exc!r}")
        _emit_output(False, TARGET_DATE)
        return 1

    print(f"[poll] {len(updates)} new update(s)")

    for update in updates:
        state["offset"] = max(state.get("offset", 0), update["update_id"] + 1)
        msg = update.get("message") or {}
        chat_id = str(msg.get("chat", {}).get("id", ""))
        if chat_id != CHAT_ID:
            continue
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        print(f"[msg] {text[:80]}")

        cmd = text.lower().split()
        if not cmd:
            continue

        if cmd[0] in ("/preview", "/tomorrow"):
            if len(cmd) > 1:
                try:
                    parsed = date.fromisoformat(cmd[1])
                    TARGET_DATE = parsed.isoformat()
                except ValueError:
                    _send("⚠️ Date format invalid. Use: /preview YYYY-MM-DD")
                    continue
            else:
                TARGET_DATE = (date.today() + timedelta(days=1)).isoformat()
            HAS_COMMAND = True
            _send(f"✨ Generating preview for {TARGET_DATE}…\nCountdown + matches will arrive in 2-4 min.")

        elif cmd[0] == "/help":
            _send(
                "Available commands:\n\n"
                "/preview\n  Generate tomorrow's posts now.\n\n"
                "/preview YYYY-MM-DD\n  Generate posts for a specific date.\n\n"
                "/help\n  This message."
            )

    _save_state(state)
    _emit_output(HAS_COMMAND, TARGET_DATE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
