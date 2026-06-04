"""Editorial layer: captions, hashtags, and pinned-comment text per post type.

Goal: vary the prose enough that the feed doesn't feel mechanical, while still
being deterministic per post (so re-rendering the same post yields the same
caption — important for traceability and idempotency).

Per post type:
    match     → 7-slide WC fixture preview
    countdown → 1-slide J-X teaser
    nation    → upcoming
    stadium   → upcoming
    group     → upcoming

Each builder returns three pieces:
    caption        → main post text (Instagram / TikTok description)
    hashtags       → list of tags to append OR drop in the first comment
    first_comment  → the pinned reply (engagement boost, extra hashtags, CTA)
"""
from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# Universal hashtag pools — picked from each pool deterministically by post id
# ---------------------------------------------------------------------------
_TAGS_CORE = [
    "#WorldCup2026", "#WC2026", "#FIFAWorldCup", "#FIFA",
    "#football", "#soccer", "#futbol", "#futebol",
]
_TAGS_REACH = [
    "#fyp", "#foryou", "#foryoupage", "#footballtiktok",
    "#footballcontent", "#sportscontent", "#sportstiktok",
]
_TAGS_NICHE = [
    "#matchpreview", "#footballpredictions", "#footballnews",
    "#matchday", "#kickoff", "#thefootballbro",
]


# ===========================================================================
# Public API
# ===========================================================================
def build_caption(post: dict) -> dict:
    """Return {"caption": str, "hashtags": list[str], "first_comment": str}.

    `hashtags` is the full pool — platform-specific splits live in
    `for_telegram(post)` which is what callers should prefer.
    """
    post_type = post.get("post_type", "match")
    if post_type == "countdown":
        return _countdown(post)
    if post_type == "match":
        return _match(post)
    if post_type == "nation":
        return _nation(post)
    if post_type == "stadium":
        return _stadium(post)
    if post_type == "group":
        return _group(post)
    # Sensible fallback
    return {"caption": "World Cup 2026 update.", "hashtags": _TAGS_CORE, "first_comment": ""}


def for_telegram(post: dict) -> dict:
    """Return ready-to-paste blocks split per platform.

      tiktok_text       : caption + 5 hashtags inline (short, algo-friendly)
      instagram_text    : caption + 12 hashtags inline (rich for IG feed)
      ig_first_comment  : extra 8 hashtags for the pinned reply (IG only)

    Each block is a single string ready to dump into a <pre> Telegram
    code block so the user can tap-to-copy without ever touching labels.
    """
    pack = build_caption(post)
    caption = pack["caption"]
    hashtags = pack["hashtags"]
    first_comment_raw = pack["first_comment"]

    # TikTok: lean on 5 hashtags
    tt_tags = hashtags[:5]
    tiktok_text = f"{caption}\n\n{' '.join(tt_tags)}"

    # Instagram: 12 hashtags inline
    ig_tags = hashtags[:12]
    instagram_text = f"{caption}\n\n{' '.join(ig_tags)}"

    # IG first comment: keep whatever the post-type builder produced
    return {
        "tiktok_text": tiktok_text,
        "instagram_text": instagram_text,
        "ig_first_comment": first_comment_raw,
    }


def _rng_for(post: dict) -> random.Random:
    seed_str = post.get("post_id") or post.get("match_id") or post.get("post_type", "x")
    return random.Random(hash(seed_str) % (2**31))


def _pick(pool: list[str], n: int, rng: random.Random) -> list[str]:
    """Pick n unique tags from pool deterministically."""
    pool = list(pool)
    rng.shuffle(pool)
    return pool[:n]


# ===========================================================================
# COUNTDOWN
# ===========================================================================
_COUNTDOWN_HOOKS_FAR = [
    "The countdown is on.",
    "Less than two weeks. Tick. Tock.",
    "Get your boots and your snacks ready.",
    "The world's biggest football party is loading.",
]
_COUNTDOWN_HOOKS_MID = [
    "Almost there. Almost.",
    "Squad lists are dropping. Vibes are rising.",
    "Final friendlies. Final preparations.",
    "The wait is nearly over.",
]
_COUNTDOWN_HOOKS_NEAR = [
    "Boots tied. Coaches ready. We're so close.",
    "A few sleeps from the biggest tournament on Earth.",
    "Get hyped. It's almost game time.",
    "The opening whistle is around the corner.",
]
_COUNTDOWN_HOOKS_KICKOFF = [
    "Today is the day. World Cup 2026 is HERE.",
    "Game on. The greatest show on Earth starts now.",
    "It's official. Kickoff day. Let's go.",
]

_COUNTDOWN_QUESTIONS = [
    "Who are you backing for the trophy?",
    "Which team will surprise the world?",
    "Group stage favourite? Drop your pick.",
    "Most underrated nation in this World Cup?",
    "Who's lifting the trophy in NYC on July 19?",
]


def _countdown(post: dict) -> dict:
    rng = _rng_for(post)
    days = post.get("days_to_kickoff", 9)

    if days == 0:
        hook_pool = _COUNTDOWN_HOOKS_KICKOFF
        days_label = "Kickoff day."
    elif days <= 3:
        hook_pool = _COUNTDOWN_HOOKS_NEAR
        days_label = f"{days} day{'s' if days > 1 else ''} to go."
    elif days <= 7:
        hook_pool = _COUNTDOWN_HOOKS_MID
        days_label = f"{days} days to go."
    else:
        hook_pool = _COUNTDOWN_HOOKS_FAR
        days_label = f"{days} days to go."

    hook = rng.choice(hook_pool)
    question = rng.choice(_COUNTDOWN_QUESTIONS)

    caption = f"⏳ {days_label}\n\n{hook}\n\n{question} 👇"

    hashtags = _TAGS_CORE + ["#Countdown", "#WC26Countdown"] + _pick(_TAGS_REACH, 3, rng)

    first_comment = (
        f"Drop your prediction below 🔥\n\n"
        + " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng))
    )

    return {"caption": caption, "hashtags": hashtags, "first_comment": first_comment}


# ===========================================================================
# MATCH (J-1 preview)
# ===========================================================================
_MATCH_HOOKS = [
    "It's matchday tomorrow. {h} vs {a}.",
    "Tomorrow night: {h} take on {a}. Here's everything you need to know.",
    "{h} vs {a} — full preview inside ⤵️",
    "All eyes on {h} vs {a}. Here's the breakdown.",
    "Matchday brief: {h} face {a}. Stats, form, prediction — let's go.",
]

_MATCH_QUESTIONS = [
    "Your scoreline? Drop it 👇",
    "1, X or 2? Drop your call.",
    "Who takes it? Comment below.",
    "Pick the winner. Reasoning optional 😏",
]


def _match(post: dict) -> dict:
    rng = _rng_for(post)
    h = post["home"]["name"]
    a = post["away"]["name"]
    hook = rng.choice(_MATCH_HOOKS).format(h=h, a=a)
    question = rng.choice(_MATCH_QUESTIONS)

    if post.get("stage") == "knockout":
        round_name = post.get("knockout", {}).get("round", "Knockout stage")
        context_line = f"🏆 {round_name}"
    else:
        context_line = f"📋 Group {post.get('group', '?')} · MD{post.get('match_number_in_group', '?')}"

    kickoff = post.get("kickoff_utc_label", post.get("kickoff_local_label", ""))
    venue = post.get("venue", {}).get("stadium", "")
    when_where = f"⏰ {kickoff}" + (f"  •  📍 {venue}" if venue else "")

    caption = f"{hook}\n\n{context_line}\n{when_where}\n\n{question}"

    # Country-specific tags + match-specific
    home_tag = "#" + h.replace(" ", "")
    away_tag = "#" + a.replace(" ", "")
    hashtags = (_TAGS_CORE + [home_tag, away_tag, "#MatchPreview"]
                + _pick(_TAGS_REACH, 3, rng))

    # Prediction in first comment — short & engagement-driving
    pred = post.get("prediction", {})
    pred_line = ""
    if pred:
        pred_line = (f"🎯 Our call: {h} {pred.get('home_score', '?')} - "
                     f"{pred.get('away_score', '?')} {a}\n"
                     f"{pred.get('reasoning', '')}\n\n")
    first_comment = (pred_line
                     + "What's YOUR scoreline? 👇\n\n"
                     + " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng)))

    return {"caption": caption, "hashtags": hashtags, "first_comment": first_comment}


# ===========================================================================
# Stubs for upcoming post types (return safe defaults so nothing crashes)
# ===========================================================================
def _nation(post: dict) -> dict:
    rng = _rng_for(post)
    name = post.get("name", "Team")
    nickname = post.get("nickname")
    conf = post.get("confederation", "")
    grp = post.get("group_letter", "?")
    rank = post.get("fifa_rank")
    star = (post.get("star_player") or {}).get("name")
    quali = post.get("quali_pct")
    verdict = post.get("predicted_round")
    titles = post.get("wc_titles") or 0
    first_wc = post.get("is_first_wc")

    # Lead block — mirrors the Telegram preview header so social viewers get
    # the identity at a glance before the editorial hook.
    header = [f"🏳 {name}" + (f" · {nickname}" if nickname else "")]
    header.append(f"🌍 {conf} · Group {grp}" + (f" · FIFA #{rank}" if rank else ""))
    if first_wc:
        header.append("✨ First-ever World Cup")
    elif titles:
        header.append(f"🏆 World Champions ×{titles}")
    if star:
        header.append(f"⭐ {star}")
    header_block = "\n".join(header)

    # Hook leans on the predictor verdict — the bot's hot take drives replies.
    if first_wc:
        hooks = [
            f"{name} land on the biggest stage for the very first time. Dark horse or out early? 👇",
            f"A debut on the world stage for {name}. How far do they go? 👇",
        ]
    else:
        hooks = [
            f"The bot's call: {name} reach the {verdict}. Agree or madness? 👇",
            f"Pre-tournament verdict — {name} to the {verdict}, {quali}% out of the group. Your take? 👇",
            f"{quali}% to escape Group {grp}, predicted {verdict}. Backing {nickname or name}? 👇",
        ]
    caption = f"{header_block}\n\n{rng.choice(hooks)}"

    name_tag = "#" + name.replace(" ", "").replace(".", "")
    conf_tag = "#" + conf if conf else None
    extra = [t for t in (name_tag, conf_tag) if t]
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + extra + _pick(_TAGS_REACH, 3, rng),
        "first_comment": " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng)),
    }


def _stadium(post: dict) -> dict:
    import wc_data
    rng = _rng_for(post)
    name = post.get("stadium", "Stadium")
    city = post.get("city", "")
    country = post.get("country", "")
    capacity = post.get("capacity") or 0
    n_matches = len(post.get("matches") or [])

    # Lead block: the same info that lands at the top of the Telegram preview,
    # so social viewers see the venue identity before the editorial hook.
    header_lines = [
        f"🏟 {name}",
        f"📍 {city}, {country}".strip(", "),
    ]
    if capacity:
        header_lines.append(f"👥 Capacity: {capacity:,}")
    if n_matches:
        plural = "match" if n_matches == 1 else "matches"
        header_lines.append(f"⚽️ {n_matches} {plural} scheduled")
    header = "\n".join(header_lines)

    # Per-venue editorial hook (curated in CITY_BRANDS). Generic fallbacks only
    # exist as a safety net for unknown venues.
    brand = wc_data.city_brand(name) or {}
    hook = brand.get("caption_hook") or rng.choice([
        "One of 16 venues hosting WC 2026. Visited? 👇",
        "Where memories will be written this summer. Been here? 👇",
        "Built for the world's game. Catching a match here? 👇",
        "The road to the trophy runs through here. Which fixture excites you? 👇",
    ])
    caption = f"{header}\n\n{hook}"
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + ["#Stadium", "#WC26Venues"] + _pick(_TAGS_REACH, 3, rng),
        "first_comment": " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng)),
    }


def _group(post: dict) -> dict:
    rng = _rng_for(post)
    g = post.get("group", "?")
    caption = f"📋 Group {g} preview.\n\nWho qualifies, who exits.\n\nYour top 2? 👇"
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + [f"#Group{g}", "#GroupStage"] + _pick(_TAGS_REACH, 3, rng),
        "first_comment": " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng)),
    }


# ===========================================================================
# Convenience for legacy callers
# ===========================================================================
def caption_only(post: dict) -> str:
    """Return just the caption + hashtags inline (single-post platforms)."""
    out = build_caption(post)
    tag_line = " ".join(out["hashtags"])
    return out["caption"] + "\n\n" + tag_line


# ===========================================================================
# CLI
# ===========================================================================
if __name__ == "__main__":
    import json, sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from companion import build_countdown_post
    from datetime import date

    print("=== COUNTDOWN J-9 ===")
    c = build_caption(build_countdown_post(date(2026, 6, 2)))
    print("CAPTION:")
    print(c["caption"])
    print("\nHASHTAGS:", " ".join(c["hashtags"]))
    print("\nFIRST COMMENT:")
    print(c["first_comment"])
    print()
    print("=== COUNTDOWN J-0 ===")
    c = build_caption(build_countdown_post(date(2026, 6, 11)))
    print(c["caption"])
    print(" ".join(c["hashtags"]))
    print(c["first_comment"])
    print()
    print("=== MATCH (mock) ===")
    m = json.loads(open("series/match.example.json", encoding="utf-8").read())
    c = build_caption(m)
    print(c["caption"])
    print(" ".join(c["hashtags"]))
    print(c["first_comment"])
