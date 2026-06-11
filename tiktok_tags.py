"""TikTok hashtags curated per nation and per stadium.

Strategy after the TikTok throttle analysis: drop the bot-signature of
identical tags everywhere and curate 3 specific tags per post + 2 pillars.

Format always: [SPECIFIC1, SPECIFIC2, SPECIFIC3, #WorldCup2026, #FIFA]

Specific tags target:
  - The team / city itself (the local search route)
  - The locale's native football world (#Selecao for BR, #CopaDoMundo
    for ES/PT-speaking, #LesBleus for FR, etc.)
  - A continental or rivalry hook (#CONMEBOL, #AFCON, #ChampionsLeague)

This drives the algorithm to branch out beyond the generic FYP loop —
hispano, luso, anglo audiences pick up posts that target their tags.
"""
from __future__ import annotations

import random

# Rotating pools so posts don't always end on the same #WorldCup2026 #FIFA.
# Each post draws ONE canonical tournament tag (discoverability) + ONE reach/
# trending tag, both picked by the post's seed so the pair varies every time.
# Trending tags pulled from current WC-2026 TikTok usage (Golazo2026,
# ModoMundial, etc.) + the evergreen football reach tags.
CORE_TAGS = (
    "#WorldCup2026", "#FIFAWorldCup", "#WorldCup", "#Mundial2026",
    "#WC26", "#FIFA", "#WorldCup26", "#Copa2026",
)
REACH_TAGS = (
    "#fyp", "#foryoupage", "#footballtok", "#Golazo2026", "#ModoMundial",
    "#SportsTok", "#GameDay", "#FootballVibes", "#ViralSports", "#football",
    "#soccer", "#futbol", "#footballedit", "#PasionSinFronteras",
)

# Back-compat: a couple of callers still import PILLARS. Keep a stable default.
PILLARS = ("#WorldCup2026", "#FIFA")


def rotators(rng: random.Random) -> list[str]:
    """One canonical tournament tag + one reach/trending tag, seeded so the
    pair is different on each post instead of the fixed #WorldCup2026 #FIFA."""
    return [rng.choice(CORE_TAGS), rng.choice(REACH_TAGS)]


# Per-nation curated tags. 3 specific tags each, pillars added automatically.
# When updating: stay native-language (#Maroc beats #Morocco for the algo),
# and keep one tag that ties to the broader football identity.
NATION_TAGS: dict[str, tuple[str, str, str]] = {
    # ----- CONMEBOL — lean into Spanish/Portuguese search routes -----
    "ARG": ("#Argentina", "#LaScaloneta", "#CopaDelMundo"),
    "BRA": ("#Brasil", "#Selecao", "#CopaDoMundo"),
    "URY": ("#Uruguay", "#LaCeleste", "#CopaDelMundo"),
    "COL": ("#Colombia", "#LosCafeteros", "#CopaDelMundo"),
    "ECU": ("#Ecuador", "#LaTri", "#CopaDelMundo"),
    "PAR": ("#Paraguay", "#LaAlbirroja", "#CopaDelMundo"),

    # ----- UEFA — mix native + global -----
    "ESP": ("#España", "#LaRoja", "#Mundial2026"),
    "FRA": ("#France", "#LesBleus", "#CoupeDuMonde"),
    "ENG": ("#England", "#ThreeLions", "#WC26"),
    "POR": ("#Portugal", "#Selecao", "#CopaDoMundo"),
    "NED": ("#Nederland", "#Oranje", "#WK2026"),
    "BEL": ("#Belgium", "#RedDevils", "#WK2026"),
    "GER": ("#Deutschland", "#DieMannschaft", "#WM2026"),
    "CRO": ("#Hrvatska", "#Vatreni", "#SP2026"),
    "ITA": ("#Italia", "#Azzurri", "#Mondiali"),  # safety, ITA not qualified
    "AUT": ("#Österreich", "#TeamAustria", "#WM2026"),
    "SWE": ("#Sverige", "#Blagult", "#VM2026"),
    "TUR": ("#Türkiye", "#AyYildizlilar", "#DunyaKupasi"),
    "NOR": ("#Norge", "#Drillos", "#VM2026"),
    "SCO": ("#Scotland", "#TartanArmy", "#WC26"),
    "CZE": ("#Cesko", "#NarodniTym", "#MS2026"),
    "BIH": ("#Bosna", "#Zmajevi", "#SP2026"),

    # ----- CONCACAF -----
    "USA": ("#USMNT", "#StarsAndStripes", "#WC26"),
    "MEX": ("#Mexico", "#ElTri", "#CopaDelMundo"),
    "CAN": ("#Canada", "#CanMNT", "#WC26"),
    "PAN": ("#Panama", "#MareaRoja", "#CopaDelMundo"),
    "HAI": ("#Haiti", "#LesGrenadiers", "#CoupeDuMonde"),
    "CUW": ("#Curacao", "#Caribbean", "#WC26"),

    # ----- CAF — both colonial-language tag + native nickname -----
    "MAR": ("#Maroc", "#AtlasLions", "#CAN"),
    "SEN": ("#Senegal", "#LionsDeLaTeranga", "#CAN"),
    "CIV": ("#CoteDIvoire", "#LesElephants", "#CAN"),
    "EGY": ("#Egypt", "#Pharaohs", "#AFCON"),
    "TUN": ("#Tunisie", "#AiglesDeCarthage", "#CAN"),
    "ALG": ("#Algerie", "#LesFennecs", "#CAN"),
    "GHA": ("#Ghana", "#BlackStars", "#AFCON"),
    "COD": ("#RDCongo", "#Leopards", "#CAN"),
    "RSA": ("#SouthAfrica", "#BafanaBafana", "#AFCON"),
    "CPV": ("#CaboVerde", "#TubaroesAzuis", "#AFCON"),

    # ----- AFC -----
    "JPN": ("#日本代表", "#SamuraiBlue", "#AsianCup"),
    "KOR": ("#대한민국", "#TaegukWarriors", "#AsianCup"),
    "IRN": ("#TeamMelli", "#IranFootball", "#AsianCup"),
    "AUS": ("#Socceroos", "#AusFootball", "#AsianCup"),
    "KSA": ("#السعودية", "#GreenFalcons", "#AsianCup"),
    "QAT": ("#Qatar", "#AlAnnabi", "#AsianCup"),
    "JOR": ("#الأردن", "#AlNashama", "#AsianCup"),
    "IRQ": ("#العراق", "#LionsOfMesopotamia", "#AsianCup"),
    "UZB": ("#Uzbekistan", "#OqBoorilar", "#AsianCup"),

    # ----- OFC -----
    "NZL": ("#NewZealand", "#AllWhites", "#OFC"),
}


# Per-stadium curated tags. Targets local audience around the venue.
STADIUM_TAGS: dict[str, tuple[str, str, str]] = {
    # Mexico (3 venues)
    "Estadio Azteca":          ("#Azteca", "#Mexico", "#CopaDelMundo"),
    "Estadio Akron":           ("#Guadalajara", "#Chivas", "#CopaDelMundo"),
    "Estadio BBVA":            ("#Monterrey", "#Rayados", "#CopaDelMundo"),

    # USA (11 venues)
    "MetLife Stadium":         ("#NewYork", "#NJ", "#WC26Final"),
    "SoFi Stadium":            ("#LosAngeles", "#SoFiStadium", "#WC26"),
    "AT&T Stadium":            ("#Dallas", "#JerryWorld", "#WC26"),
    "Mercedes-Benz Stadium":   ("#Atlanta", "#ATL", "#WC26"),
    "NRG Stadium":             ("#Houston", "#HTown", "#WC26"),
    "Arrowhead Stadium":       ("#KansasCity", "#ChiefsKingdom", "#WC26"),
    "Lincoln Financial Field": ("#Philadelphia", "#Philly", "#WC26"),
    "Levi's Stadium":          ("#BayArea", "#SantaClara", "#WC26"),
    "Lumen Field":             ("#Seattle", "#Sounders", "#WC26"),
    "Gillette Stadium":        ("#Boston", "#NewEngland", "#WC26"),
    "Hard Rock Stadium":       ("#Miami", "#305", "#WC26"),

    # Canada (2 venues)
    "BC Place":                ("#Vancouver", "#BCPlace", "#WC26"),
    "BMO Field":               ("#Toronto", "#TFC", "#WC26"),
}


def _interleave(specific: list[str], rng: random.Random) -> list[str]:
    """Order: first specific tag, then a rotating tournament tag (so even a
    short 2-3 tag post keeps discoverability), then the rest of the specifics,
    then a rotating reach/trending tag. The two rotators vary every post."""
    core, reach = rotators(rng)
    return specific[:1] + [core] + specific[1:3] + [reach]


def for_nation(tla: str, rng: random.Random) -> list[str]:
    """Up to 5 hashtags for a nation post: curated specifics + 2 rotating tags."""
    tla = (tla or "").upper()
    specific = list(NATION_TAGS.get(tla, ())) or ["#" + tla]
    return _interleave(specific, rng)


def for_stadium(name: str, rng: random.Random) -> list[str]:
    """Up to 5 hashtags for a stadium post: curated specifics + 2 rotating tags."""
    specific = list(STADIUM_TAGS.get(name, ())) or ["#Stadium", "#WC26Venues"]
    return _interleave(specific, rng)
