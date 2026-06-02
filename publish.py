"""Publishing layer: Instagram carousel via the Meta Graph API.

Instagram carousel flow (requires an IG Business/Creator account linked to
a Facebook Page, plus a long-lived access token):
  1. Upload each image as a carousel ITEM container (is_carousel_item=true).
     Each image must be a PUBLIC https URL — IG fetches it server-side.
  2. Create a CAROUSEL container referencing the item ids.
  3. Publish the carousel container.

Because IG needs public URLs (not local files), you must host the PNGs
somewhere reachable first (S3, Cloudinary, a static bucket, ngrok in dev).
`_host_images` is the single seam to implement for your hosting choice.

TikTok is intentionally not wired yet — its Content Posting API is
restrictive. Fallback: the PNGs sit in output/<id>/upload/ ready for a
manual post.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

import config

load_dotenv()

GRAPH = "https://graph.facebook.com/v21.0"


# ===========================================================================
# Caption
# ===========================================================================
def build_caption(match: dict) -> str:
    home = match["home"]["name"]
    away = match["away"]["name"]
    kickoff = match.get("kickoff_local_label", "")
    venue = match.get("venue", {})
    stadium = venue.get("stadium", "")
    city = venue.get("city", "")

    if match.get("stage") == "knockout":
        round_name = match.get("knockout", {}).get("round", "Knockout stage")
        line2 = f"🏆 {round_name}"
    else:
        line2 = f"Group {match.get('group', '')} · Matchday {match.get('match_number_in_group', '')}"

    tags = (
        "#WorldCup2026 #FIFAWorldCup #WC26 "
        f"#{home.replace(' ', '')} #{away.replace(' ', '')} #football #soccer"
    )
    return (
        f"{home} 🆚 {away}\n"
        f"{line2}\n"
        f"📍 {stadium}, {city} · ⏰ {kickoff}\n\n"
        f"Your call? Drop your score 1 / X / 2 in the comments 👇\n\n"
        f"{tags}"
    )


# ===========================================================================
# Instagram
# ===========================================================================
def publish_instagram(slide_paths: list[Path], caption: str) -> str:
    token = os.getenv("META_ACCESS_TOKEN")
    ig_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")
    if not token or not ig_id:
        raise RuntimeError(
            "META_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID missing in .env. "
            "Cannot publish to Instagram."
        )

    public_urls = _host_images(slide_paths)

    # 1) item containers
    item_ids = []
    for url in public_urls:
        r = requests.post(
            f"{GRAPH}/{ig_id}/media",
            data={"image_url": url, "is_carousel_item": "true", "access_token": token},
            timeout=30,
        )
        r.raise_for_status()
        item_ids.append(r.json()["id"])

    # 2) carousel container
    r = requests.post(
        f"{GRAPH}/{ig_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    r.raise_for_status()
    creation_id = r.json()["id"]

    _wait_until_ready(creation_id, token)

    # 3) publish
    r = requests.post(
        f"{GRAPH}/{ig_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("id", "published")


def _wait_until_ready(creation_id: str, token: str, attempts: int = 10) -> None:
    """Carousel containers need a moment to finish processing before publish."""
    for _ in range(attempts):
        r = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        r.raise_for_status()
        if r.json().get("status_code") == "FINISHED":
            return
        time.sleep(3)
    # Proceed anyway; media_publish will error clearly if it's truly not ready.


def _host_images(slide_paths: list[Path]) -> list[str]:
    """Return public https URLs for the given local PNGs.

    IMPLEMENT FOR YOUR HOSTING: upload each file to S3/Cloudinary/etc. and
    return the resulting URLs in the same order. Until then this raises so
    nobody silently ships broken posts.
    """
    raise NotImplementedError(
        "Image hosting not configured. Implement _host_images() to upload the "
        "PNGs and return their public https URLs (S3, Cloudinary, static bucket…)."
    )


# ===========================================================================
# TikTok (manual fallback for now)
# ===========================================================================
def publish_tiktok(slide_paths: list[Path], caption: str) -> str:
    return (
        "TikTok auto-post not enabled. PNGs are ready for manual upload at: "
        f"{slide_paths[0].parent if slide_paths else config.OUTPUT_DIR}"
    )


# ===========================================================================
# Dispatcher + deferred notification (Phase 2 hook)
# ===========================================================================
def publish(slide_paths: list[Path], caption: str, targets: list[str]) -> dict:
    results: dict[str, str] = {}
    for target in targets:
        if target == "instagram":
            results["instagram"] = publish_instagram(slide_paths, caption)
        elif target == "tiktok":
            results["tiktok"] = publish_tiktok(slide_paths, caption)
        else:
            results[target] = f"unknown target: {target}"

    if config.NOTIFY_AFTER_PUBLISH:
        _notify(results, caption)
    return results


def _notify(results: dict, caption: str) -> None:
    """Phase-2 post-publish notification (email/Telegram/Slack).

    Wire your channel of choice here. Left as a no-op stub so flipping
    REQUIRE_APPROVAL=False + NOTIFY_AFTER_PUBLISH=True is a config change,
    not a code change.
    """
    print(f"[notify] published: {results}")
