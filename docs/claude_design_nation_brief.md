# Brief Claude Design — Nation showcase series (3 slides)

**Goal**: a 3-slide carousel per qualified nation (48 total), dripped pre-tournament
and during early matchdays. Mirrors the structural quality of the stadium series
(template_stadium / v1·v2·v3), with one decisive twist: **per-nation color palette**
so each carousel visually echoes the nation it's profiling.

The Python pipeline is already wired. Your job is the visual template only.

---

## File deliverables

```
series/template_nation.html       (new — full HTML, mirror template_stadium.html)
series/slides_nation/n1.js        (new — Identity slide)
series/slides_nation/n2.js        (new — Squad & coach slide)
series/slides_nation/n3.js        (new — Group + outlook slide)
series/slides.css                 (edit — add #n1, #n2, #n3 rules)
```

All shared engine code (`series/render.js`, `series/data.js`, `series/core.css`,
`assets/logo_wc2026.png`, the `.flag`, `.ghost-mark`, `.footer` helpers) is already
in place and you can reuse it freely. Same `window.__post` injection pattern as
the stadium series.

---

## Data contract (window.__post)

You receive this exact shape. Field names are stable; build your slides against
them. Example payload for `tla=FRA, today=2026-06-14`:

```json
{
  "post_id": "WC2026-N-FRA",
  "post_type": "nation",
  "post_date": "2026-06-14",

  "tla": "FRA",
  "code": "fr",
  "name": "France",
  "nickname": "Les Bleus",
  "confederation": "UEFA",
  "federation_crest": "https://upload.wikimedia.org/.../france_seal.svg.png",

  "colors": {
    "primary":   "#0055A4",
    "secondary": "#FFFFFF",
    "accent":    "#EF4135"
  },

  "group_letter": "I",
  "group_members": ["FRA", "IRQ", "NOR", "SEN"],
  "fixtures": [
    {"kickoff_utc": "2026-06-16T19:00:00Z", "opponent_tla": "SEN", "opponent_code": "sn",
     "opponent_name": "Senegal", "venue": "MetLife Stadium", "matchday": 1},
    {"kickoff_utc": "2026-06-22T21:00:00Z", "opponent_tla": "IRQ", "opponent_code": "iq",
     "opponent_name": "Iraq", "venue": "Lincoln Financial Field", "matchday": 2},
    {"kickoff_utc": "2026-06-26T19:00:00Z", "opponent_tla": "NOR", "opponent_code": "no",
     "opponent_name": "Norway", "venue": "Gillette Stadium", "matchday": 3}
  ],

  "fifa_rank": 2,
  "squad_value_eur_m": 1530,
  "avg_age": 27,
  "star_player": {"name": "Kylian Mbappé", "club": "Real Madrid",
                  "stat": "48 goals for France", "photo_url": null},
  "players_to_watch": ["Désiré Doué", "William Saliba"],
  "coach": {"name": "Didier Deschamps", "nationality_code": "fr"},

  "wc_appearances": 17,
  "wc_best_finish": "Champions (1998, 2018)",
  "wc_titles": 2,
  "wc_history": [
    {"year": 2022, "finish": "Final"},
    {"year": 2018, "finish": "Champions"},
    {"year": 2014, "finish": "Quarter-final"},
    {"year": 2010, "finish": "Group stage"},
    {"year": 2006, "finish": "Final"}
  ],
  "is_first_wc": false,
  "honours": [
    {"label": "WC",        "count": 2},
    {"label": "Euro",      "count": 2},
    {"label": "Conf. Cup", "count": 2},
    {"label": "UNL",       "count": 1}
  ],

  "quali_pct": 92,
  "predicted_round": "Final"
}
```

**Resilience contract**: any field can be null or empty. For the 32 tier-2
nations the data layer ships only `colors + nickname` initially — your template
should gracefully omit empty sections (no broken placeholders).

Specifically:
- `federation_crest` null → drop the crest, keep the flag as the hero
- `coach` null → drop the coach block
- `wc_history` empty AND `is_first_wc` true → show a single "FIRST WORLD CUP" badge
- `wc_history` 1-4 entries → show all (no padding)
- `players_to_watch` empty → drop the section, expand the star block
- `most_capped` / `top_scorer` removed from contract (the user dropped legends)

---

## Visual direction — common to all 3 slides

- **Background**: gradient from `colors.primary` (top) to a 35% darker shade
  of `colors.primary` (bottom). HSL trick: `hsl(H, S, max(L-25%, 4%))`.
- **Ghost-mark**: the WC2026 logo centered behind everything at `opacity: 0.05`,
  ~1240px tall. Reuse `<img class="ghost-mark" src="assets/logo_wc2026.png" />`.
- **Accent color**: `colors.accent` (or `colors.secondary` if accent missing) for
  numbers, decorative dots, bottom rules. Replaces the gold (`var(--gold)`) we
  use elsewhere — but **keep the gold for the prediction verdict number** so it
  stays universally readable.
- **Typography**: same display + sans stack as stadium template (Bodoni-like
  display, Inter for sans). No new font files.
- **Footer**: small WC2026 logo, same as stadium series.

---

## Slide 1 — Identity (#n1)

```
            [ ghost mark logo ]

           [ big flag, ~580px wide, centered ]

                    FRANCE                       ← display font, 142px
                   Les Bleus                     ← italic, lighter weight, 38px

          UEFA  ·  Group I  ·  FIFA #2           ← eyebrow line, 26px

         17th World Cup appearance               ← 24px, muted
         Best: Champions 1998 · 2018             ← 24px, muted

  WC × 2  ·  Euro × 2  ·  Conf. Cup × 2  ·  UNL × 1   ← one line, abbreviated
```

**Rules:**
- Flag is THE hero — big, centered, drop shadow.
- Federation crest is optional. If present, place it as a small inset
  (top-right, 130px, drop shadow) — secondary to the flag. If missing, drop it.
- Honours line: render each entry as `{label} × {count}`, separated by ` · `,
  on ONE line. If it overflows 980px width, drop entries from the right until
  it fits (preserve order; WC is always first).
- For `is_first_wc: true`, swap "Nth World Cup appearance" for a centered
  **"FIRST WORLD CUP APPEARANCE"** badge in `colors.accent`, no "Best:" line,
  no honours line.

---

## Slide 2 — Squad & coach (#n2)

No player photos (user dropped them). Two text blocks stacked, then squad meta,
then WC history at the bottom. Clean typography, no emoji icons in the WC history.

```
            [ ghost mark logo ]

           ⭐  STAR PLAYER                       ← eyebrow, accent color
           Kylian Mbappé                        ← display font, 64px
           Real Madrid  ·  48 goals for France  ← 26px, muted

           👀  PLAYERS TO WATCH                 ← eyebrow, accent color
           Désiré Doué  ·  William Saliba       ← 36px, regular

  ─────────────────────────────────────

  🎩  COACH                  📊  SQUAD
  Didier Deschamps           Value: €1.53B
                             Avg age: 27

  ─────────────────────────────────────

           LAST 5 WORLD CUPS                    ← eyebrow

           2022      Final                      ← clean two-column layout:
           2018      Champions                     years left, finishes right
           2014      Quarter-final                 tabular-nums alignment
           2010      Group stage                   28px, line-height 1.5
           2006      Final
```

**Rules:**
- The user explicitly asked for "simple texte mais beau" on the WC history —
  no emoji icons (no 🏆🥈🥉). Just typography. Aligned years (tabular) and
  clean spacing.
- `coach.nationality_code` → render the small flag inline after the coach name
  using `WCF.flag(code, 'mini')`.
- Squad block: skip `top5` (user removed it). Just value + avg age.
- If `wc_history` is empty AND `is_first_wc: true`, replace the section with
  a large centered badge: **"WRITING THEIR FIRST WC STORY"**.

---

## Slide 3 — Group + outlook (#n3)

Reuse the **`.v3-match` row layout** from the stadium series (`#v3 .v3-match`
in slides.css) for the 3 fixtures — same date+UTC + flag + VS + flag pattern,
same min-height, same dense mode hooks. This is free reuse; just remap `#n3 .nation-match`
to inherit from those rules or copy them.

```
            [ ghost mark logo ]

                GROUP I FIXTURES                ← title, 48px

  [J1 · 16 JUN · 19:00 UTC]  FRA 🇫🇷 vs 🇸🇳 SEN  ·  MetLife
  [J2 · 22 JUN · 21:00 UTC]  FRA 🇫🇷 vs 🇮🇶 IRQ  ·  Lincoln Financial
  [J3 · 26 JUN · 19:00 UTC]  NOR 🇳🇴 vs 🇫🇷 FRA  ·  Gillette

  ─────────────────────────────────────

                🎯  PREDICTOR VERDICT           ← gold eyebrow (keep gold here)

         Chance to escape Group I:     92%      ← QUALI FIRST (user's order)
         Pre-tournament prediction:   FINAL     ← then ROUND below

         The bot sees Les Bleus going all the way   ← optional flavor line, muted
                   to MetLife on July 19.
                Do you back the call? 👇
```

**Rules:**
- Each fixture row shows: matchday chip + date + UTC time + team flag/TLA +
  VS + opponent flag/TLA + venue (truncated to fit).
- The user's team flag/TLA should be visually emphasized (bolder / brighter)
  so the viewer instantly sees the perspective.
- Predictor verdict block: **quali % FIRST, predicted round SECOND** (user
  explicitly asked for this order).
- Use gold (`var(--gold)`) for the predictor numbers (92%, FINAL) regardless
  of nation palette — keeps the "verdict" feel consistent.
- The flavor line under the verdict comes from a Python-side hook similar to
  stadiums (curated per nation in NATION_PROFILES → `caption_hook` field).
  For now you can hardcode `"The bot sees {nickname} going to {round}."`
  as a template — we'll inject real curated hooks later.

---

## Hard constraints

1. **Field names are FROZEN**. Don't rename anything in the data contract. If
   you need a new field, list it in your PR notes and the Python side will add
   it. This minimizes round-trips.
2. **No external font files**. Use the same display/sans stack as stadium.
3. **No JS dependencies**. Pure vanilla, same pattern as v1/v2/v3.
4. **Resilient to nulls**. The 32 tier-2 nations land with sparse data
   initially — render gracefully (skip blocks, never show "undefined").
5. **Per-nation backgrounds are MANDATORY**. The whole point of this series is
   that France's slide *feels* French (blue) and Brazil's slide *feels*
   Brazilian (yellow-green). Generate the gradient inline in JS from
   `m.colors.primary`. Don't hardcode any one palette.

---

## Test data

The Python pipeline already serves you. To preview locally:

```bash
python main.py --nation FRA --preview
```

This generates the 3 slides into `output/WC2026-N-FRA/` and sends them to
Telegram for visual review. You can also open the static preview:

```bash
# Open in browser with FRA pre-injected:
open "series/template_nation.html?nation=FRA"
```

(That URL hook is your job to wire in template_nation.html — pull from a
`?nation=` query param and inject a hardcoded FRA payload, mirroring how
template_stadium.html previews stadium posts.)

The 16 marquee nations are fully populated in wc_data.NATION_PROFILES with
realistic data so you can browse different palettes during design. Try FRA
(blue), BRA (yellow/green), ARG (light blue), MAR (red/green), USA (navy/red)
for representative range.

---

## What I (Claude main) will handle after you ship

Once `template_nation.html` + the three n*.js modules land, I'll wire:
- `render_nation()` in `series/render_slides.py`
- The `--nation-cron` flag + `nation.yml` workflow
- `_caption_nation()` in captions.py with per-nation editorial hooks
- The remaining 32 tier-2 nation profiles (data only — your template is done)

So a single, complete pass from you closes this series for good. No iterations
needed unless visual feedback requires it. Thanks 🙏
