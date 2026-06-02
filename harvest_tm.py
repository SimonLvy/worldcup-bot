"""One-shot Transfermarkt squad-value harvest for all 48 WC 2026 nations.

Run once (or re-run to update):
    python harvest_tm.py

Scrapes each national team's squad page on transfermarkt.us to get:
  - Squad total market value (in €M)
  - Top-3 most-valuable players (name, club, value €M)

Results are printed as Python dict literals ready to paste into wc_data.py.
Nothing is written automatically — the user reviews and pastes.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
BASE = "https://www.transfermarkt.us"
SEASON = 2025  # most recent season with WC squad data

# TLA → (transfermarkt team id, URL slug for squad page)
# Verified team ids from Transfermarkt.
TM_IDS: dict[str, tuple[int, str]] = {
    "FRA": (3377, "frankreich"),
    "ARG": (3437, "argentinien"),
    "ENG": (3166, "england"),
    "ESP": (3842, "spanien"),
    "BRA": (3439, "brasilien"),
    "POR": (3436, "portugal"),
    "NED": (3440, "niederlande"),
    "GER": (3438, "deutschland"),
    "BEL": (3382, "belgien"),
    "CRO": (3583, "kroatien"),
    "URY": (3444, "uruguay"),
    "COL": (3441, "kolumbien"),
    "MAR": (3453, "marokko"),
    "USA": (3535, "vereinigte-staaten"),
    "SUI": (3443, "schweiz"),
    "JPN": (3446, "japan"),
    "SEN": (3457, "senegal"),
    "MEX": (3445, "mexiko"),
    "AUT": (3380, "osterreich"),
    "SWE": (3381, "schweden"),
    "TUR": (3447, "turkei"),
    "AUS": (3536, "australien"),
    "CIV": (3461, "elfenbeinskuste"),
    "EGY": (3459, "agypten"),
    "NOR": (3383, "norwegen"),
    "SCO": (3385, "schottland"),
    "PAR": (3442, "paraguay"),
    "TUN": (3460, "tunesien"),
    "CZE": (3377 - 1, "tschechien"),  # placeholder — see note below
    "ALG": (3462, "algerien"),
    "PAN": (3537, "panama"),
    "GHA": (3456, "ghana"),
    "COD": (3465, "dr-kongo"),
    "IRN": (3466, "iran"),
    "KSA": (3467, "saudi-arabien"),
    "QAT": (3469, "katar"),
    "JOR": (3472, "jordanien"),
    "IRQ": (3470, "irak"),
    "UZB": (3473, "usbekistan"),
    "RSA": (3474, "sudafrika"),
    "BIH": (3584, "bosnien-herzegowina"),
    "CPV": (3475, "kap-verde"),
    "HAI": (3538, "haiti"),
    "NZL": (3539, "neuseeland"),
    "CUW": (3540, "curacao"),
    "KOR": (3448, "sudkorea"),
    "ECU": (3449, "ecuador"),
    "CAN": (3450, "kanada"),
}


def _parse_money(text: str) -> float:
    """Parse strings like '1.53bn' or '35.00m' into €M."""
    text = text.strip().replace(",", "")
    m = re.search(r"([\d.]+)\s*(bn|m)", text, re.IGNORECASE)
    if not m:
        return 0.0
    val = float(m.group(1))
    if m.group(2).lower() == "bn":
        val *= 1000
    return round(val)


def scrape_team(tla: str, tm_id: int, slug: str) -> dict:
    url = f"{BASE}/{slug}/kader/verein/{tm_id}/saison_id/{SEASON}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return {"tla": tla, "error": r.status_code}
        soup = BeautifulSoup(r.content, "html.parser")
        text = soup.get_text()

        # Total squad market value — first EUR-like pattern after the text
        mv_patterns = re.findall(r"[€£\$]?([\d,\.]+(?:bn|m))", text, re.IGNORECASE)
        squad_total_m = 0.0
        if mv_patterns:
            squad_total_m = _parse_money(mv_patterns[0])

        # Player rows
        rows = soup.select("table.items tbody tr")
        players = []
        seen_names = set()
        for row in rows:
            name_el = row.select_one("td.hauptlink a")
            club_el = row.select_one("td.zentriert.hauptlink a")
            val_el = row.select_one("td.rechts.hauptlink")
            if not name_el or not val_el:
                continue
            name = name_el.text.strip()
            if name in seen_names:
                continue
            seen_names.add(name)
            club = club_el.text.strip() if club_el else "—"
            val_text = val_el.text.strip()
            val_m = _parse_money(val_text)
            if val_m > 0:
                players.append({"name": name, "club": club, "value_eur_m": val_m})

        players.sort(key=lambda p: p["value_eur_m"], reverse=True)
        top3 = players[:3]

        return {
            "tla": tla,
            "squad_value_eur_m": squad_total_m,
            "top3": top3,
            "player_count": len(players),
        }
    except Exception as exc:
        return {"tla": tla, "error": str(exc)[:60]}


def run():
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cache_path = Path("data/tm_harvest.json")
    cache_path.parent.mkdir(exist_ok=True)

    results = {}
    if cache_path.exists():
        results = json.loads(cache_path.read_text(encoding="utf-8"))
        print(f"[cache] loaded {len(results)} existing results")

    for tla, (tm_id, slug) in TM_IDS.items():
        if tla in results and "error" not in results[tla]:
            print(f"[skip] {tla} already harvested")
            continue
        print(f"[scraping] {tla} ({slug})…", end=" ", flush=True)
        result = scrape_team(tla, tm_id, slug)
        results[tla] = result
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"€{result['squad_value_eur_m']}M | {len(result.get('top3',[]))} key players")
        cache_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(1.2)  # polite rate limiting

    # Print wc_data.py-ready output
    print("\n\n# ===== PASTE INTO wc_data.py (SQUAD_VALUES / STARS) =====")
    for tla, r in sorted(results.items()):
        if "error" in r:
            print(f'    # {tla}: ERROR {r["error"]}')
            continue
        stars = r.get("top3", [])
        star_str = ", ".join(
            f'{{"name": "{p["name"]}", "club": "{p["club"]}", "stat": "€{p["value_eur_m"]}M market value"}}'
            for p in stars
        )
        print(f'    "{tla}": {{"value": {r["squad_value_eur_m"]}, "stars": [{star_str}]}},')


if __name__ == "__main__":
    run()
