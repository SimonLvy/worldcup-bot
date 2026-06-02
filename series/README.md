# World Cup 2026 — Matchday Series (data-driven template)

A polished, 8-slide Instagram series (1080×1350, 4:5) that renders **entirely from one
`match.json`**. Design (charter) and data are fully separated, so you can iterate visuals
without touching pipeline logic — and generate all 104 matches automatically.

## How it works

```
match.json  ──►  template.html (window.__match)  ──►  Playwright screenshots  ──►  output/slide_01..08.png
```

The template reads its data from `window.__match` (injected by Playwright) or, in the
live browser preview, falls back to fetching `match.example.json`.

## Files

| File | Role |
|---|---|
| `template.html` | Entry point. Loads everything, renders the configured slides. |
| `core.css` | Design tokens + viewer shell + shared components (flags, panels, footer). |
| `slides.css` | Per-slide layouts (`#s1`…`#s8`). |
| `data.js` | `window.WCF` — formatting + asset helpers (dates, numbers, **flags**, photos, radar). |
| `slides/s1.js … s8.js` | **One module per slide.** Each registers `{ render(m), mount?(el,m) }` into `window.WCSlides`. |
| `config.js` | `window.WC_CONFIG.slides = [...]` — the only place to **add / remove / reorder** slides. |
| `render.js` | Engine: builds slides, preview nav, capture mode, `window.WC.ready`. |
| `match.example.json` | A validated example matching your `fetch_match.py` contract. |
| `render_slides.py` | Playwright snippet → screenshots all 8 slides for one match. |
| `assets/logo_wc2026.png` | Tournament logo (whitened via CSS for the dark theme). |

## Modularity (your "1 slide = 1 module" requirement)

- **Add** a slide: create `slides/s9.js` (register `window.WCSlides.s9`), add a `<script>`
  tag in `template.html`, and add `'s9'` to `config.js`.
- **Remove / reorder**: just edit the array in `config.js`. Nothing else breaks.
- Each module is pure: `render(m)` returns an HTML string from the match object; optional
  `mount(el, m)` runs after insertion (used by slide 5 to draw the radar canvas).

## Data contract

`match.example.json` mirrors the structure your `fetch_match.py` already emits. Two
**optional, additive** fields make the output richer (safe to omit):

- `home.ratings` / `away.ratings` = `{attack, midfield, value, experience, defense}` (0–100)
  drive the radar (slide 5). If absent, the engine derives plausible values from
  `fifa_rank` / `squad_value_eur_m` / `avg_age`.
- `prediction` = `{home_score, away_score, reasoning}` (slide 8). Fill this **server-side**
  from your Claude call in Python and it renders directly — fully automatable. If absent,
  the live browser preview falls back to an in-page Claude call.

### Real flags
Flags come from **flagcdn.com** by ISO 3166-1 alpha-2 code (`home.code`, `away.code`,
e.g. `"fr"`, `"ar"`). All 48 nations work with no extra assets. (`object-fit: cover`,
swap to `contain` in `core.css` if you prefer un-cropped flags.)

### Photos
`venue.image_url` and `key_players[].photo_url` accept any URL. `null` → a labelled
placeholder so the slide still composes cleanly.

## Rendering (Python)

```bash
pip install playwright && playwright install chromium
python render_slides.py            # renders match.example.json → output/<match_id>/slide_01..08.png
```

In your pipeline, loop your fixtures and call `render_slides.render_match(match_dict)`.
`device_scale_factor=2` yields crisp 2160×2700 PNGs (downscale to 1080×1350 for upload).

## Notes
- Fonts (Archivo + Anton) load from Google Fonts; the engine waits on `document.fonts.ready`
  before signalling `WC.ready`. Self-host them for fully offline rendering.
- Skip-a-day / no-match handling lives in your `main.py` (the template only renders what
  it's given).
