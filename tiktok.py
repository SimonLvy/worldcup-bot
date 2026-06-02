"""TikTok Content Posting API integration.

Three things this module does:

  1. OAuth setup (one-time, local):  run `python tiktok.py setup`
     Opens a browser → user authorises @thefootballbro → we receive an
     authorisation code on http://localhost:8000/callback → we exchange it
     for an access_token + refresh_token and save them to .env.

  2. Token refresh (every call):  access tokens expire after 24h. We use
     the refresh_token (1 year lifespan) to mint a fresh access_token on
     every post. GitHub Actions secret just needs TIKTOK_REFRESH_TOKEN.

  3. Photo post upload:  uses the Direct Post API in MEDIA_UPLOAD mode so
     the post lands in the user's TikTok drafts. The user finishes it (adds
     music, edits caption, etc.) in the app, then taps Publish.

Photo hosting (TikTok requires public URLs via PULL_FROM_URL): we upload
the PNGs to catbox.moe anonymously — no API key, permanent URLs.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

import requests
from dotenv import load_dotenv

load_dotenv()

TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_POST_INIT = "https://open.tiktokapis.com/v2/post/publish/content/init/"
TIKTOK_POST_STATUS = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "user.info.basic,video.publish,video.upload"

CATBOX_URL = "https://catbox.moe/user/api.php"


# ===========================================================================
# OAuth setup — one-time, local
# ===========================================================================
def setup_oauth() -> None:
    """Walk through TikTok OAuth and save tokens to .env."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    if not client_key or not client_secret:
        print("[error] TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET missing in .env")
        sys.exit(1)

    state = secrets.token_urlsafe(16)
    code_holder: dict[str, str] = {}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            if "code" not in params:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter.")
                return
            if params.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State mismatch — possible CSRF.")
                return
            code_holder["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>OK</h1><p>You can close this window and go back to your terminal.</p>"
            )

        def log_message(self, *_args):
            return  # silence

    server = HTTPServer(("localhost", 8000), CallbackHandler)
    Thread(target=server.serve_forever, daemon=True).start()

    authorize_params = {
        "client_key": client_key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    auth_url = TIKTOK_AUTH_URL + "?" + urllib.parse.urlencode(authorize_params)

    print("\n[1] Opening this URL in your browser:")
    print(f"    {auth_url}\n")
    print("    Log in as @thefootballbro and grant the permissions.\n")
    webbrowser.open(auth_url)

    print("[2] Waiting for redirect (max 5 min)…")
    deadline = time.time() + 300
    while time.time() < deadline and "code" not in code_holder:
        time.sleep(1)
    server.shutdown()

    if "code" not in code_holder:
        print("[error] no callback received within 5 minutes — aborting.")
        sys.exit(1)

    print("[3] Exchanging code for tokens…")
    resp = requests.post(
        TIKTOK_TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code_holder["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[error] token exchange failed: {resp.status_code} {resp.text[:300]}")
        sys.exit(1)
    payload = resp.json()
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    if not access_token or not refresh_token:
        print(f"[error] tokens missing in response: {payload}")
        sys.exit(1)

    _save_tokens_to_env(access_token, refresh_token)
    print(f"\n✅ Tokens saved to .env")
    print(f"   access_token  : {access_token[:20]}… (24h)")
    print(f"   refresh_token : {refresh_token[:20]}… (365d)")
    print("\nFor GitHub Actions, also add TIKTOK_REFRESH_TOKEN as a secret.")


def _save_tokens_to_env(access_token: str, refresh_token: str) -> None:
    env_path = Path(".env")
    text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    lines = text.splitlines()

    def upsert(key: str, value: str) -> None:
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                return
        lines.append(f"{key}={value}")

    upsert("TIKTOK_ACCESS_TOKEN", access_token)
    upsert("TIKTOK_REFRESH_TOKEN", refresh_token)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ===========================================================================
# Token refresh
# ===========================================================================
def fresh_access_token() -> str:
    """Return a valid access token, refreshing if we have a refresh_token."""
    refresh = os.getenv("TIKTOK_REFRESH_TOKEN")
    if not refresh:
        # Fall back to the long-lived access token if no refresh available
        tok = os.getenv("TIKTOK_ACCESS_TOKEN")
        if not tok:
            raise RuntimeError("No TIKTOK_ACCESS_TOKEN or TIKTOK_REFRESH_TOKEN — run setup_oauth.")
        return tok

    client_key = os.getenv("TIKTOK_CLIENT_KEY")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
    resp = requests.post(
        TIKTOK_TOKEN_URL,
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ===========================================================================
# Photo hosting via catbox.moe (anonymous, free, permanent)
# ===========================================================================
def host_photos(paths: list[Path]) -> list[str]:
    """Upload PNGs to catbox.moe and return public URLs."""
    urls = []
    for p in paths:
        with open(p, "rb") as f:
            resp = requests.post(
                CATBOX_URL,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (p.name, f, "image/png")},
                timeout=60,
            )
        resp.raise_for_status()
        url = resp.text.strip()
        if not url.startswith("http"):
            raise RuntimeError(f"Unexpected catbox response for {p.name}: {url[:200]}")
        urls.append(url)
        print(f"[catbox] {p.name} → {url}")
    return urls


# ===========================================================================
# Upload to TikTok drafts
# ===========================================================================
def upload_photo_post(slide_paths: list[Path], caption: str) -> str:
    """Upload a photo carousel (or single photo) to the user's TikTok drafts.

    Returns the publish_id. The post lands in drafts; user finishes it in the
    TikTok app (adds music, edits caption, taps Publish).
    """
    if not slide_paths:
        raise ValueError("No slide paths provided.")

    # 1. Host the photos publicly
    photo_urls = host_photos(slide_paths)

    # 2. Init the upload with TikTok
    token = fresh_access_token()
    body = {
        "post_info": {
            "title": caption[:90],  # TikTok caption limit ~150 but keep short
            "privacy_level": "SELF_ONLY",  # sandbox-safe
            "disable_comment": False,
            "auto_add_music": True,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 0,
            "photo_images": photo_urls,
        },
        "post_mode": "MEDIA_UPLOAD",  # → drafts
        "media_type": "PHOTO",
    }
    resp = requests.post(
        TIKTOK_POST_INIT,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        data=json.dumps(body),
        timeout=60,
    )
    if not resp.ok:
        raise RuntimeError(f"TikTok init failed: {resp.status_code} {resp.text[:400]}")
    payload = resp.json()
    publish_id = payload.get("data", {}).get("publish_id")
    if not publish_id:
        raise RuntimeError(f"No publish_id in TikTok response: {payload}")
    print(f"[tiktok] publish_id: {publish_id}")

    # 3. Poll for completion
    deadline = time.time() + 180
    last_status = None
    while time.time() < deadline:
        s = requests.post(
            TIKTOK_POST_STATUS,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=UTF-8"},
            data=json.dumps({"publish_id": publish_id}),
            timeout=30,
        )
        if s.ok:
            data = s.json().get("data", {})
            status = data.get("status")
            if status != last_status:
                print(f"[tiktok] status: {status}")
                last_status = status
            if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
                return publish_id
            if status == "FAILED":
                raise RuntimeError(f"TikTok publish FAILED: {data}")
        time.sleep(5)

    print("[tiktok] still processing after 3min — leaving it in TikTok's queue.")
    return publish_id


# ===========================================================================
# CLI
# ===========================================================================
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "setup":
        setup_oauth()
    elif cmd == "refresh":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(fresh_access_token()[:20] + "…")
    elif cmd == "host":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        # Test: upload output/WC2026-CD-09/upload/slide_01.png
        p = Path("output/WC2026-CD-09/upload/slide_01.png")
        if not p.exists():
            print("Run a countdown render first.")
            sys.exit(1)
        urls = host_photos([p])
        print("URLs:", urls)
    else:
        print("Usage: python tiktok.py {setup|refresh|host}")
