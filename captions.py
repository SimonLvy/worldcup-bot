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

# Punchy display names for the match-title line (football-data name → short
# form). Only the awkwardly long names need an entry; every other nation is
# already short enough and is used verbatim.
_TITLE_SHORT_NAMES = {
    "United States": "USA",
    "Bosnia-Herzegovina": "Bosnia",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
}


def _short_name(name: str) -> str:
    return _TITLE_SHORT_NAMES.get(name, name)


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
    if post_type == "reaction":
        return _reaction(post)
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

    # TikTok: builders now roll their own hashtag COUNT (0..5) for variety.
    # `tiktok_hashtags` present (even empty []) → use it verbatim; absent →
    # fall back to 5 from the generic pool.
    tt_tags = pack.get("tiktok_hashtags")
    if tt_tags is None:
        tt_tags = hashtags[:5]
    tiktok_text = caption + (("\n\n" + " ".join(tt_tags)) if tt_tags else "")

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


# ---------------------------------------------------------------------------
# Diversity helpers — make every post vary in length AND hashtag count so the
# feed never reads as a template. All seeded by post_id (deterministic).
# ---------------------------------------------------------------------------
def _elongate(word: str, rng: random.Random) -> str:
    """BRAZIL -> BRAZILLLLLL. The shout-it caption style."""
    w = (word or "").strip().upper()
    if not w or not w[-1].isalpha():
        return w
    return w + w[-1] * rng.randint(4, 9)


def _roll_tags(rng: random.Random, tags5) -> list[str]:
    """Seeded variety in hashtag count: sometimes 5, sometimes 1, sometimes
    none. Returns a sublist of the curated tags (or [])."""
    tags5 = [t for t in (tags5 or []) if t]
    if not tags5:
        return []
    n = rng.choices([0, 1, 2, 3, 5], weights=[16, 20, 16, 22, 26])[0]
    return tags5[:n]


def _compose(rng: random.Random, oneword, shorts, longs) -> str:
    """Pick a caption length: one-word shout / short hook / long take. Weighted
    toward short, but one-word and long both show up often enough to read human."""
    style = rng.choices(["one", "short", "long"], weights=[22, 46, 32])[0]
    pool = {"one": oneword, "short": shorts, "long": longs}.get(style)
    pool = pool or shorts or oneword or longs or [""]
    return rng.choice(pool)


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

    if days == 0:
        oneword = ["TODAY.", "IT'S HERE.", "GAME ON."]
    elif days <= 1:
        oneword = ["TOMORROW.", "ALMOST.", f"{days}."]
    else:
        oneword = [f"{days}.", "SOON.", "ALMOST."]
    shorts = [
        f"⏳ {days_label} {hook}",
        f"{days_label} {question} 👇",
        f"{hook} {question} 👇",
    ]
    longs = [
        f"⏳ {days_label}\n\n{hook}\n\n{question} 👇",
        f"{days_label} I can't sit still. {hook} The whole planet is about to stop for this. {question} 👇",
    ]
    caption = _compose(rng, oneword, shorts, longs)

    import tiktok_tags
    cd_tags = ["#Countdown", "#WC26Countdown"] + tiktok_tags.rotators(rng)
    hashtags = _TAGS_CORE + ["#Countdown", "#WC26Countdown"] + _pick(_TAGS_REACH, 3, rng)
    first_comment = (
        f"Drop your prediction below 🔥\n\n"
        + " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng))
    )
    return {"caption": caption, "hashtags": hashtags,
            "tiktok_hashtags": _roll_tags(rng, cd_tags), "first_comment": first_comment}


# ===========================================================================
# MATCH (J-1 preview)
# ===========================================================================
def _match(post: dict) -> dict:
    import tiktok_tags
    rng = _rng_for(post)
    h = post["home"]["name"]
    a = post["away"]["name"]
    th, ta = _short_name(h), _short_name(a)
    title = f"{th} VS {ta}"
    pred = post.get("prediction", {})
    ps = f"{pred.get('home_score', '?')}-{pred.get('away_score', '?')}" if pred else ""

    # The matchup now lives in the title line, so the body is hook-only (no
    # repeating "X vs Y"). Prediction phrasing may still name the teams.
    oneword = ["MATCHDAY.", _elongate(th, rng), _elongate(ta, rng), "BIG ONE."]
    shorts = [
        f"👀 My call: {ps}. You? 👇" if ps else "👀 Your call? 👇",
        "I CANNOT wait for this one. 🔥 Who takes it?",
        "Drop your scoreline. 👇",
    ]
    longs = [
        f"I've gone through the form, the history, all of it, and I'm calling {th} {ps} {ta}. Bold? Maybe. Wrong? We'll find out. What's YOUR scoreline? 👇" if ps
        else "I've gone through the form and the history and I think this one's got fireworks. What's your scoreline? 👇",
        "Two teams with everything to play for. My head says one thing, my gut says another. Give me your prediction before kickoff. 👇",
    ]
    body = _compose(rng, oneword, shorts, longs)
    caption = f"{title}\n\n{body}"

    # Tags from both nations (curated) + roll the count.
    ht = tiktok_tags.NATION_TAGS.get(post["home"].get("tla") or "", ())
    at = tiktok_tags.NATION_TAGS.get(post["away"].get("tla") or "", ())
    m_tags = [t for t in (ht[:1] + at[:1]) if t] + tiktok_tags.rotators(rng)

    home_tag = "#" + h.replace(" ", "")
    away_tag = "#" + a.replace(" ", "")
    hashtags = (_TAGS_CORE + [home_tag, away_tag, "#MatchPreview"]
                + _pick(_TAGS_REACH, 3, rng))
    return {
        "caption": caption,
        "hashtags": hashtags,
        "tiktok_hashtags": _roll_tags(rng, m_tags),
        "first_comment": "",
    }


# ===========================================================================
# Stubs for upcoming post types (return safe defaults so nothing crashes)
# ===========================================================================
def _nation(post: dict) -> dict:
    import tiktok_tags
    rng = _rng_for(post)
    name = post.get("name", "Team")
    tla = post.get("tla", "")
    nickname = post.get("nickname")
    conf = post.get("confederation", "")
    grp = post.get("group_letter", "?")
    star = (post.get("star_player") or {}).get("name") or "their best"
    verdict = post.get("predicted_round")
    quali = post.get("quali_pct")
    titles = post.get("wc_titles") or 0
    first_wc = post.get("is_first_wc")

    # VOICE: @thefootballbro — hyped fan, first person, no em dashes, no "bot".
    # Three length registers (one-word shout / short hook / long take), bucket
    # aware. _compose picks the register, _roll_tags picks 0..5 hashtags.
    nick_word = (nickname or "").split()[-1] if nickname else ""
    if first_wc:
        bucket_word = "HISTORY."
        shorts = [
            f"{name.upper()}. FIRST WORLD CUP EVER. 🔥 I am not ready for this. Who's riding with them? 👇",
            f"Nobody is talking about {name} and that's criminal. Their FIRST Mondial. 🤯 Dark horse?",
            f"{star} is dragging {name} to their FIRST World Cup. 🌍 Tell me you're not hyped. 👇",
        ]
        longs = [
            f"{name}. First World Cup in their entire history. Sit with that. A whole country that has NEVER been on this stage, and here they are. {star} leading the line. I don't care about the odds, I'm watching every single minute. Tell me you're not a little bit excited. 👇",
            f"Everyone's sleeping on {name} and I get it, it's their debut. But debutants have shocked this tournament before. {star} can cause problems. Write the script for me: how far do these guys go? 👇",
        ]
    elif titles >= 3:
        bucket_word = "ROYALTY."
        deep = verdict in ("Champions", "Final", "Semi-final")
        if deep:
            shorts = [
                f"{titles}x WORLD CHAMPIONS and I've got {name} going ALL the way. 🏆 Too confident? 👇",
                f"{star} leading {titles}-time winners {name}. I'm calling {verdict}. 🤯 With me or against me?",
                f"{name} don't rebuild, they RELOAD. {titles} titles deep. 🐐 Winning it again?",
            ]
            longs = [
                f"{titles} World Cups. {star} in the squad. And people STILL want to bet against {name}? They've done this before and they'll do it again. I've got them in the {verdict} and I'm not moving off it. Come tell me where I'm wrong. 👇",
                f"Let me be clear about {name}. {titles} stars on the shirt is not luck, it's a standard. {star} carries that weight. I'm calling {verdict}, no hedging. Screenshot it. Who's brave enough to disagree? 👇",
            ]
        else:
            shorts = [
                f"{titles}x WORLD CHAMPIONS and I've got {name} OUT by the {verdict}?! 🤯 Tell me I'm wrong. 👇",
                f"Hot take: {titles}-time champs {name} crash in the {verdict}. 🔥 Too disrespectful?",
                f"{titles} stars on the shirt but I've got {name} going home in the {verdict}. 🫣 Wrong?",
            ]
            longs = [
                f"I'm about to upset some people. {name}, {titles}-time world champions, and I've got them OUT by the {verdict}. The badge is heavy but this squad? Not convinced. {star} can't do it alone. Prove me wrong in the comments, I'm ready. 👇",
                f"Respect the history, {name} have {titles} World Cups. But history doesn't play the games. I'm calling the {verdict} and no further. That's a hot take and I'll stand on it. Defend them if you can. 👇",
            ]
    elif quali and quali >= 80:
        bucket_word = "DANGEROUS."
        shorts = [
            f"{name} are CRUISING out of this group. 😤 But how far do they actually go? 👇",
            f"{star} plus this {name} squad equals problems for EVERYONE. 🔥 Semis? Final?",
            f"Sleep on {name} if you want. {star} will make you pay. 👀 How deep do they run?",
        ]
        longs = [
            f"{name} are quietly one of the scariest teams here. {star} is in the form of his life and the group? A formality. The real question is the ceiling. I've got them at least the {verdict}. Where do YOU stop them? 👇",
            f"Everyone's busy talking about the usual names while {name} are sitting there loaded. {star} leads a squad that can hurt anyone on the day. Group {grp} is the warm-up. Tell me how far this team goes. 👇",
        ]
    elif quali and quali >= 40:
        bucket_word = "SLEEPERS."
        shorts = [
            f"Group {grp} is a WAR and {name} are right in the middle of it. ⚔️ Surviving or going home? 👇",
            f"Everybody sleeping on {name}. {star} says otherwise. 👀 Upset loading?",
            f"{name} can SHOCK somebody in Group {grp}. 🔥 Who do they take down?",
        ]
        longs = [
            f"{name} are the team nobody wants to draw. Not flashy, but {star} and a real plan can ruin somebody's tournament. Group {grp} is a coin flip and I kind of love them for it. Are they surviving or going home? 👇",
            f"Toss a coin on {name}. On their day they beat anyone, on a bad day they're gone in three games. {star} is the difference maker. I think they've got one massive night in them. Do you? 👇",
        ]
    else:
        bucket_word = "UNDERDOGS."
        shorts = [
            f"Nobody is backing {name}. 💀 Prove me wrong. One game they SHOCK the world? 👇",
            f"{name} are the underdog of Group {grp}. 🐺 Who do you WANT them to ruin?",
            f"Everyone's writing off {name}. 😤 {star} didn't come to roll over. Watching them?",
        ]
        longs = [
            f"Let's be real, nobody's giving {name} a chance. And that's EXACTLY why I love them. {star} carrying the hopes of a whole nation onto the biggest stage. They don't need to win it, they need ONE magic night. Tell me it's possible. 👇",
            f"{name} are outsiders, sure. But this is the World Cup, the place underdogs become legends. {star} just needs a moment. Give me the one game where they shock the planet. 👇",
        ]

    oneword = [_elongate(name, rng)]
    if nick_word and nick_word.lower() not in ("la", "les", "the", "el", "los"):
        oneword.append(_elongate(nick_word, rng))
    oneword.append(bucket_word)

    caption = _compose(rng, oneword, shorts, longs)

    tiktok_5 = tiktok_tags.for_nation(tla, rng)
    name_tag = "#" + name.replace(" ", "").replace(".", "")
    conf_tag = "#" + conf if conf else None
    ig_extra = [t for t in (name_tag, conf_tag) if t]
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + ig_extra + _pick(_TAGS_REACH, 3, rng),
        "tiktok_hashtags": _roll_tags(rng, tiktok_5),
        "first_comment": " ".join(_pick(_TAGS_NICHE + _TAGS_REACH, 8, rng)),
    }


def _reaction(post: dict) -> dict:
    """Post-match reaction caption — @thefootballbro reacting live to the
    result vs the call we posted before kickoff. Hype, first person, no em
    dashes, ends on a comment-baiting question."""
    import tiktok_tags
    rng = _rng_for(post)
    h, a = post["home"], post["away"]
    hn, an = h["name"], a["name"]
    ph, pa = post["predicted"]["home"], post["predicted"]["away"]
    ah, aa = post["actual"]["home"], post["actual"]["away"]
    verdict = post.get("verdict")
    winner = post.get("winner_name")
    loser = post.get("loser_name")
    pred_str = f"{ph}-{pa}"
    ft_str = f"{ah}-{aa}"

    is_draw = winner is None
    win = winner or "them"
    if verdict == "nailed":
        oneword = ["CALLED IT.", "NAILED IT.", _elongate(win, rng) if winner else "SCENES."]
        shorts = [
            f"I CALLED IT. 🎯 {hn} {ft_str} {an}, EXACTLY what I said. Bow down. 👇",
            f"Wrote {pred_str}. Final? {ft_str}. 🔮 Call me Nostradamus. Who doubted me?",
            f"{ft_str}. EXACT scoreline I predicted. 😤 Screenshot this. You owe me an apology.",
        ]
        longs = [
            f"I want everyone to remember this one. I called {hn} {pred_str} {an} before a ball was kicked. Final score? {ft_str}. EXACT. I'm not saying I'm a genius but the receipts are right there. Who had it spot on like me? 👇",
        ]
    elif verdict == "called" and is_draw:
        oneword = ["CALLED IT.", "HONOURS EVEN.", "TOLD YOU."]
        shorts = [
            f"I said it'd be tight. ✅ {ft_str}, honours even. Called the draw. Who agreed? 👇",
            f"Dead even, just like I said. {ft_str}. 🤝 Points shared. Did you see it coming?",
            f"Told you to expect a tight one. {ft_str}. 🎯 Nobody could split them.",
        ]
        longs = [
            f"Don't say I didn't warn you. I called this one a draw and that's exactly what we got, {ft_str}. Two teams cancelling each other out, points shared. The call was money. Who else had the stalemate? 👇",
        ]
    elif verdict == "called":
        oneword = ["CALLED IT.", _elongate(win, rng), "TOLD YOU."]
        shorts = [
            f"Told you {win} had this. ✅ {ft_str}. Said {pred_str}, close enough. Who listened? 👇",
            f"Called it. {win} get it done, {ft_str}. 🎯 I'm cooking. Agree?",
            f"{win} win, just like I said. {ft_str}. 💪 Score wasn't spot on but the call was. Respect?",
        ]
        longs = [
            f"Don't act surprised. I told you {win} were winning this one and they did, {ft_str}. Scoreline wasn't perfect, I said {pred_str}, but the call was money. This is what I do. Who actually listened to me? 👇",
        ]
    elif verdict == "upset":
        oneword = ["UPSET.", "SCENES.", _elongate(winner, rng) if winner else "CHAOS."]
        shorts = [
            f"NOBODY saw this. 🤯 {ft_str}. I had {pred_str}. The bracket is COOKED. Did YOU call it? 👇",
            f"UPSET ALERT. 🚨 {winner} shocked the world, {ft_str}. I got it SO wrong. Who predicted this??",
            f"{winner}?! {ft_str}?! 😱 I said {pred_str} and I've never been more wrong. Chaos.",
        ]
        longs = [
            f"WHAT did we just watch. {winner} {ft_str}. I had {pred_str}, the whole world had it the other way, and they tore the script up anyway. THIS is why we love the World Cup. Be honest, did a single one of you call this? 👇",
        ]
    else:  # missed
        oneword = ["NOPE.", "WRONG.", "COOKED.", "ROBBED."]
        shorts = [
            f"Yeah I got that WRONG. 😭 {ft_str}. I said {pred_str}. Roast me in the comments. 👇",
            f"Delete my account. {ft_str}, I had {pred_str}. 🤡 You saw it coming and I didn't, right?",
            f"That did NOT go how I called it. {ft_str} vs my {pred_str}. 😬 Tell me you had it.",
        ]
        longs = [
            f"Hands up, that one's on me. I confidently said {hn} {pred_str} {an} and the actual result was {ft_str}. Completely cooked. Go ahead, the comments are open, roast me. But be honest, did YOU see it coming? 👇",
        ]
    caption = _compose(rng, oneword, shorts, longs)

    # Tags: both nations + pillars so it surfaces to both fanbases searching
    # the result right now. Count still rolls 0..5.
    htags = tiktok_tags.NATION_TAGS.get(h.get("tla"), ())
    atags = tiktok_tags.NATION_TAGS.get(a.get("tla"), ())
    specific = [t for t in (htags[:1] + atags[:1]) if t]
    tiktok_5 = specific + tiktok_tags.rotators(rng)
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + _pick(_TAGS_REACH, 3, rng),
        "tiktok_hashtags": _roll_tags(rng, tiktok_5),
        "first_comment": "",
    }


def _stadium(post: dict) -> dict:
    import wc_data, tiktok_tags
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

    # Per-venue editorial hook (curated in CITY_BRANDS). Long register = the
    # full header + curated story; short = punchy; one-word = city shout.
    brand = wc_data.city_brand(name) or {}
    hook = brand.get("caption_hook") or rng.choice([
        "One of 16 venues hosting WC 2026. Visited? 👇",
        "Where memories will be written this summer. Been here? 👇",
        "The road to the trophy runs through here. Which fixture excites you? 👇",
    ])
    oneword = [_elongate(city or name, rng), "ICONIC.", "CATHEDRAL."]
    shorts = [
        f"{name}. 🏟 One of the 16. Catching a game here? 👇",
        f"{(city or name).upper()}. This is where it happens. 🔥 You pulling up?",
        hook,
    ]
    longs = [f"{header}\n\n{hook}"]
    caption = _compose(rng, oneword, shorts, longs)
    return {
        "caption": caption,
        "hashtags": _TAGS_CORE + ["#Stadium", "#WC26Venues"] + _pick(_TAGS_REACH, 3, rng),
        "tiktok_hashtags": _roll_tags(rng, tiktok_tags.for_stadium(name, rng)),
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
