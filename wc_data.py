"""Static reference data filling the gaps in football-data.org's free tier.

The free tier gives fixtures, standings, head-to-head, form and a (partial)
squad, but NOT: ISO alpha-2 codes (needed for flagcdn), stadium/venue,
player clubs / market value, or FIFA ranking. We supply those here.

Keyed by football-data's 3-letter `tla` code.

`fifa_rank`, `squad_value_eur_m`, `players_top5` are approximations used to
seed the radar ratings and the predictor, they don't need to be exact, just
plausible and consistent. `stars` are the 3 key players per nation; for teams
without an entry, fetch_match falls back to names pulled from the API squad.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Nations: tla -> reference data
#   a2     : ISO 3166-1 alpha-2 for flagcdn (gb-eng / gb-sct for home nations)
#   rank   : approximate FIFA ranking (drives ratings + predictor)
#   value  : approximate squad market value in €M
#   top5   : approximate number of players in the top-5 European leagues
# ---------------------------------------------------------------------------
NATIONS: dict[str, dict] = {
    # Values sourced from Transfermarkt (June 2025). Entries without TM data
    # retain prior estimates (marked # est).
    "ARG": {"a2": "ar", "rank": 1,  "value": 818,  "top5": 14},
    "FRA": {"a2": "fr", "rank": 3,  "value": 1530, "top5": 21},
    "ESP": {"a2": "es", "rank": 2,  "value": 1100, "top5": 20},  # est (TM page 404)
    "ENG": {"a2": "gb-eng", "rank": 4, "value": 1310, "top5": 23},
    "BRA": {"a2": "br", "rank": 6,  "value": 912,  "top5": 19},
    "POR": {"a2": "pt", "rank": 5,  "value": 412,  "top5": 20},
    "NED": {"a2": "nl", "rank": 8,  "value": 601,  "top5": 18},
    "BEL": {"a2": "be", "rank": 9,  "value": 543,  "top5": 16},
    "GER": {"a2": "de", "rank": 10,  "value": 850,  "top5": 19},  # est (TM 182 → wrong page)
    "CRO": {"a2": "hr", "rank": 11, "value": 260,  "top5": 14},  # est (TM 25 → wrong page)
    "ITA": {"a2": "it", "rank": 12, "value": 600,  "top5": 15},
    "URY": {"a2": "uy", "rank": 17, "value": 64,   "top5": 13},
    "COL": {"a2": "co", "rank": 13, "value": 234,  "top5": 11},
    "MAR": {"a2": "ma", "rank": 7, "value": 350,  "top5": 13},  # est (TM 404)
    "USA": {"a2": "us", "rank": 16, "value": 300,  "top5": 12},  # est (TM 13 → wrong page)
    "SUI": {"a2": "ch", "rank": 19, "value": 42,   "top5": 11},
    "JPN": {"a2": "jp", "rank": 18, "value": 153,  "top5": 12},
    "SEN": {"a2": "sn", "rank": 14, "value": 486,  "top5": 13},
    "DEN": {"a2": "dk", "rank": 21, "value": 340,  "top5": 12},  # est
    "KOR": {"a2": "kr", "rank": 25, "value": 242,  "top5": 8},
    "MEX": {"a2": "mx", "rank": 15, "value": 190,  "top5": 4},
    "ECU": {"a2": "ec", "rank": 24, "value": 406,  "top5": 7},
    "AUT": {"a2": "at", "rank": 23, "value": 196,  "top5": 11},
    "SWE": {"a2": "se", "rank": 38, "value": 536,  "top5": 9},
    "TUR": {"a2": "tr", "rank": 22, "value": 100,  "top5": 7},
    "AUS": {"a2": "au", "rank": 27, "value": 90,   "top5": 3},   # est (TM 0 → wrong page)
    "CIV": {"a2": "ci", "rank": 33, "value": 36,   "top5": 9},
    "EGY": {"a2": "eg", "rank": 29, "value": 160,  "top5": 4},   # est (TM 0)
    "NOR": {"a2": "no", "rank": 31, "value": 272,  "top5": 10},
    "SCO": {"a2": "gb-sct", "rank": 43, "value": 200, "top5": 8},  # est (TM 10 → wrong)
    "PAR": {"a2": "py", "rank": 40, "value": 234,  "top5": 4},
    "TUN": {"a2": "tn", "rank": 46, "value": 90,   "top5": 3},   # est (TM 0)
    "CZE": {"a2": "cz", "rank": 41, "value": 180,  "top5": 6},   # est (TM 404)
    "ALG": {"a2": "dz", "rank": 28, "value": 200,  "top5": 7},   # est (TM 0)
    "PAN": {"a2": "pa", "rank": 34, "value": 4,    "top5": 1},
    "GHA": {"a2": "gh", "rank": 73, "value": 22,   "top5": 7},
    "COD": {"a2": "cd", "rank": 45, "value": 150,  "top5": 6},   # est (TM 404)
    "IRN": {"a2": "ir", "rank": 20, "value": 90,   "top5": 3},   # est (TM 0)
    "KSA": {"a2": "sa", "rank": 61, "value": 40,   "top5": 0},   # est (TM 404)
    "QAT": {"a2": "qa", "rank": 55, "value": 30,   "top5": 0},   # est (TM 0)
    "JOR": {"a2": "jo", "rank": 63, "value": 25,   "top5": 0},   # est (TM 0)
    "IRQ": {"a2": "iq", "rank": 56, "value": 25,   "top5": 0},   # est (TM 0)
    "UZB": {"a2": "uz", "rank": 50, "value": 40,   "top5": 1},   # est (TM 0)
    "RSA": {"a2": "za", "rank": 60, "value": 60,   "top5": 1},   # est (TM 0)
    "BIH": {"a2": "ba", "rank": 64, "value": 30,   "top5": 6},
    "CPV": {"a2": "cv", "rank": 68, "value": 56,   "top5": 2},
    "HAI": {"a2": "ht", "rank": 81, "value": 30,   "top5": 1},   # est (TM 0)
    "NZL": {"a2": "nz", "rank": 85, "value": 25,   "top5": 1},   # est (TM 0)
    "CUW": {"a2": "cw", "rank": 83, "value": 30,   "top5": 1},   # est (TM 0)
    "CAN": {"a2": "ca", "rank": 30, "value": 130,  "top5": 5},   # WC 2026 host
}

# ---------------------------------------------------------------------------
# Key players (3 per nation) for the marquee sides. Teams not listed fall back
# to names from the live API squad (club/stat unknown → graceful placeholder).
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Nation editorial profiles, the rich payload behind each nation showcase post.
# Source of truth for the 3-slide nation carousel (identity / squad / outlook).
# Populated progressively, marquee nations first. Missing entries fall back to
# a placeholder profile so the renderer never crashes on unknown tla.
# ---------------------------------------------------------------------------
NATION_PROFILES: dict[str, dict] = {
    # ----- Top 16 marquees (by FIFA rank). Verified from FIFA / Wikipedia
    # records as of late 2025. Double-check coach names + WC histories before
    # publishing, manager swaps happen. -----
    "ARG": {
        "nickname": "La Albiceleste",
        "confederation": "CONMEBOL",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/c/c1/Argentina_football_association.svg",
        "colors": {"primary": "#75AADB", "secondary": "#FFFFFF", "accent": "#6CACE4"},
        "coach": {"name": "Lionel Scaloni", "nationality_code": "ar"},
        "wc_appearances": 19,
        "wc_best_finish": "Champions (1978, 1986, 2022)",
        "wc_titles": 3,
        "honours": [
            {"label": "WC", "count": 3}, {"label": "Copa", "count": 16},
            {"label": "Finalissima", "count": 1}, {"label": "Confed", "count": 1},
        ],
    },
    "FRA": {
        "nickname": "Les Bleus",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9b/France_national_football_team_seal.svg/180px-France_national_football_team_seal.svg.png",
        "colors": {"primary": "#0055A4", "secondary": "#FFFFFF", "accent": "#EF4135"},
        "coach": {"name": "Didier Deschamps", "nationality_code": "fr"},
        "wc_appearances": 17,
        "wc_best_finish": "Champions (1998, 2018)",
        "wc_titles": 2,
        "honours": [
            {"label": "WC", "count": 2}, {"label": "Euro", "count": 2},
            {"label": "Conf. Cup", "count": 2}, {"label": "UNL", "count": 1},
        ],
    },
    "ESP": {
        "nickname": "La Roja",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/9/99/RFEF.svg",
        "colors": {"primary": "#C60B1E", "secondary": "#FFC400", "accent": "#FFFFFF"},
        "coach": {"name": "Luis de la Fuente", "nationality_code": "es"},
        "wc_appearances": 17,
        "wc_best_finish": "Champions 2010",
        "wc_titles": 1,
        "honours": [
            {"label": "WC", "count": 1}, {"label": "Euro", "count": 4},
            {"label": "UNL", "count": 1},
        ],
    },
    "ENG": {
        "nickname": "Three Lions",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/8/8d/England_national_football_team_crest.svg",
        "colors": {"primary": "#FFFFFF", "secondary": "#CE1124", "accent": "#001489"},
        "coach": {"name": "Thomas Tuchel", "nationality_code": "de"},
        "wc_appearances": 17,
        "wc_best_finish": "Champions 1966",
        "wc_titles": 1,
        "honours": [{"label": "WC", "count": 1}],
    },
    "BRA": {
        "nickname": "Seleção",
        "confederation": "CONMEBOL",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/2/27/Brazilian_Football_Confederation_logo.svg",
        "colors": {"primary": "#FEDF00", "secondary": "#009C3B", "accent": "#002776"},
        "coach": {"name": "Carlo Ancelotti", "nationality_code": "it"},
        "wc_appearances": 23,
        "wc_best_finish": "Champions × 5 (1958, 1962, 1970, 1994, 2002)",
        "wc_titles": 5,
        "honours": [
            {"label": "WC", "count": 5}, {"label": "Copa", "count": 9},
            {"label": "Confed", "count": 4},
        ],
    },
    "POR": {
        "nickname": "A Seleção",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/2/2c/FPF_logo.svg",
        "colors": {"primary": "#FF0000", "secondary": "#006600", "accent": "#FFCC00"},
        "coach": {"name": "Roberto Martínez", "nationality_code": "es"},
        "wc_appearances": 9,
        "wc_best_finish": "3rd place 1966",
        "wc_titles": 0,
        "honours": [{"label": "Euro", "count": 1}, {"label": "UNL", "count": 1}],
    },
    "NED": {
        "nickname": "Oranje",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/0/04/Royal_Dutch_Football_Association_logo.svg",
        "colors": {"primary": "#FF6900", "secondary": "#FFFFFF", "accent": "#003DA5"},
        "coach": {"name": "Ronald Koeman", "nationality_code": "nl"},
        "wc_appearances": 12,
        "wc_best_finish": "Final × 3 (1974, 1978, 2010)",
        "wc_titles": 0,
        "honours": [{"label": "Euro", "count": 1}],
    },
    "BEL": {
        "nickname": "Red Devils",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/3/30/Royal_Belgian_Football_Association.svg",
        "colors": {"primary": "#EF3340", "secondary": "#FAE042", "accent": "#000000"},
        "coach": {"name": "Rudi Garcia", "nationality_code": "fr"},
        "wc_appearances": 14,
        "wc_best_finish": "3rd place 2018",
        "wc_titles": 0,
        "honours": [],
    },
    "GER": {
        "nickname": "Die Mannschaft",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/a/ac/DFB-Logo.svg",
        "colors": {"primary": "#000000", "secondary": "#DD0000", "accent": "#FFCE00"},
        "coach": {"name": "Julian Nagelsmann", "nationality_code": "de"},
        "wc_appearances": 21,
        "wc_best_finish": "Champions × 4 (1954, 1974, 1990, 2014)",
        "wc_titles": 4,
        "honours": [
            {"label": "WC", "count": 4}, {"label": "Euro", "count": 3},
            {"label": "Confed", "count": 1},
        ],
    },
    "CRO": {
        "nickname": "Vatreni",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/2/29/Croatia_FA_logo.svg",
        "colors": {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#171796"},
        "coach": {"name": "Zlatko Dalić", "nationality_code": "hr"},
        "wc_appearances": 7,
        "wc_best_finish": "Final 2018, 3rd 2022",
        "wc_titles": 0,
        "honours": [],
    },
    "URY": {
        "nickname": "La Celeste",
        "confederation": "CONMEBOL",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/1/15/Uruguay_national_football_team_crest.svg",
        "colors": {"primary": "#75AADB", "secondary": "#FFFFFF", "accent": "#000000"},
        "coach": {"name": "Marcelo Bielsa", "nationality_code": "ar"},
        "wc_appearances": 14,
        "wc_best_finish": "Champions × 2 (1930, 1950)",
        "wc_titles": 2,
        "honours": [{"label": "WC", "count": 2}, {"label": "Copa", "count": 15}],
    },
    "COL": {
        "nickname": "Los Cafeteros",
        "confederation": "CONMEBOL",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/en/3/34/Colombia_national_football_team_logo.svg",
        "colors": {"primary": "#FFCD00", "secondary": "#003893", "accent": "#CE1126"},
        "coach": {"name": "Néstor Lorenzo", "nationality_code": "ar"},
        "wc_appearances": 7,
        "wc_best_finish": "Quarter-final 2014",
        "wc_titles": 0,
        "honours": [{"label": "Copa", "count": 1}],
    },
    "MAR": {
        "nickname": "Atlas Lions",
        "confederation": "CAF",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/c/c7/FRMF_logo.svg",
        "colors": {"primary": "#C1272D", "secondary": "#006233", "accent": "#FFFFFF"},
        "coach": {"name": "Walid Regragui", "nationality_code": "ma"},
        "wc_appearances": 7,
        "wc_best_finish": "4th place 2022",
        "wc_titles": 0,
        "honours": [{"label": "AFCON", "count": 1}],
    },
    "USA": {
        "nickname": "The Stars and Stripes",
        "confederation": "CONCACAF",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/a/a5/United_States_Soccer_Federation_logo_2016.svg",
        "colors": {"primary": "#002868", "secondary": "#BF0A30", "accent": "#FFFFFF"},
        "coach": {"name": "Mauricio Pochettino", "nationality_code": "ar"},
        "wc_appearances": 11,
        "wc_best_finish": "3rd place 1930",
        "wc_titles": 0,
        "honours": [{"label": "Gold Cup", "count": 8}],
    },
    "SUI": {
        "nickname": "Nati",
        "confederation": "UEFA",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Swiss_Football_Association_logo.svg",
        "colors": {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#000000"},
        "coach": {"name": "Murat Yakin", "nationality_code": "ch"},
        "wc_appearances": 12,
        "wc_best_finish": "Quarter-final (1934, 1938, 1954)",
        "wc_titles": 0,
        "honours": [],
    },
    "JPN": {
        "nickname": "Samurai Blue",
        "confederation": "AFC",
        "federation_crest": "https://upload.wikimedia.org/wikipedia/commons/f/f6/Japan_Football_Association.svg",
        "colors": {"primary": "#BC002D", "secondary": "#FFFFFF", "accent": "#07045E"},
        "coach": {"name": "Hajime Moriyasu", "nationality_code": "jp"},
        "wc_appearances": 8,
        "wc_best_finish": "Round of 16 (2002, 2010, 2018, 2022)",
        "wc_titles": 0,
        "honours": [{"label": "Asian Cup", "count": 4}],
    },
    # ----- Tier 2 stubs (rank 18-49). Nickname + colors + confederation so
    # the renderer paints the right palette. Coach / WC history / honours
    # to be curated progressively, empty/null fields are dropped gracefully
    # by the template. -----
    "SEN": {"nickname": "Lions of Teranga", "confederation": "CAF",  "colors": {"primary": "#00853F", "secondary": "#FDEF42", "accent": "#E31B23"}},
    "KOR": {"nickname": "Taeguk Warriors",  "confederation": "AFC",  "colors": {"primary": "#003478", "secondary": "#FFFFFF", "accent": "#C60C30"}},
    "MEX": {"nickname": "El Tri",            "confederation": "CONCACAF", "colors": {"primary": "#006847", "secondary": "#FFFFFF", "accent": "#CE1126"}},
    "ECU": {"nickname": "La Tri",            "confederation": "CONMEBOL", "colors": {"primary": "#FFD100", "secondary": "#0072CE", "accent": "#EF3340"}},
    "AUT": {"nickname": "Das Team",          "confederation": "UEFA", "colors": {"primary": "#ED2939", "secondary": "#FFFFFF", "accent": "#000000"}},
    "SWE": {"nickname": "Blågult",           "confederation": "UEFA", "colors": {"primary": "#006AA7", "secondary": "#FECC00", "accent": "#FFFFFF"}},
    "TUR": {"nickname": "Crescent-Stars",    "confederation": "UEFA", "colors": {"primary": "#E30A17", "secondary": "#FFFFFF", "accent": "#000000"}},
    "AUS": {"nickname": "Socceroos",         "confederation": "AFC",  "colors": {"primary": "#FFCD00", "secondary": "#00843D", "accent": "#012169"}},
    "CIV": {"nickname": "Les Éléphants",     "confederation": "CAF",  "colors": {"primary": "#F77F00", "secondary": "#FFFFFF", "accent": "#009E60"}},
    "EGY": {"nickname": "Pharaohs",          "confederation": "CAF",  "colors": {"primary": "#CE1126", "secondary": "#FFFFFF", "accent": "#000000"}},
    "NOR": {"nickname": "Drillos",           "confederation": "UEFA", "colors": {"primary": "#EF2B2D", "secondary": "#002868", "accent": "#FFFFFF"}},
    "SCO": {"nickname": "Tartan Army",       "confederation": "UEFA", "colors": {"primary": "#0065BD", "secondary": "#FFFFFF", "accent": "#3B3B3B"}},
    "CAN": {"nickname": "Canucks",           "confederation": "CONCACAF", "colors": {"primary": "#FF0000", "secondary": "#FFFFFF", "accent": "#000000"}},
    "PAR": {"nickname": "La Albirroja",      "confederation": "CONMEBOL", "colors": {"primary": "#D52B1E", "secondary": "#FFFFFF", "accent": "#0038A8"}},
    "TUN": {"nickname": "Eagles of Carthage","confederation": "CAF",  "colors": {"primary": "#E70013", "secondary": "#FFFFFF", "accent": "#000000"}},
    "CZE": {"nickname": "Národní tým",       "confederation": "UEFA", "colors": {"primary": "#11457E", "secondary": "#FFFFFF", "accent": "#D7141A"}},
    "ALG": {"nickname": "Les Fennecs",       "confederation": "CAF",  "colors": {"primary": "#006633", "secondary": "#FFFFFF", "accent": "#C8102E"}},
    "PAN": {"nickname": "Marea Roja",        "confederation": "CONCACAF", "colors": {"primary": "#DA121A", "secondary": "#005AA7", "accent": "#FFFFFF"}},
    "GHA": {"nickname": "Black Stars",       "confederation": "CAF",  "colors": {"primary": "#CE1126", "secondary": "#FCD116", "accent": "#006B3F"}},
    "COD": {"nickname": "Léopards",          "confederation": "CAF",  "colors": {"primary": "#007FFF", "secondary": "#F7D618", "accent": "#CE1021"}},
    "IRN": {"nickname": "Team Melli",        "confederation": "AFC",  "colors": {"primary": "#239F40", "secondary": "#FFFFFF", "accent": "#DA0000"}},
    "KSA": {"nickname": "Green Falcons",     "confederation": "AFC",  "colors": {"primary": "#006C35", "secondary": "#FFFFFF", "accent": "#FFFFFF"}},
    "QAT": {"nickname": "Al-Annabi",         "confederation": "AFC",  "colors": {"primary": "#8A1538", "secondary": "#FFFFFF", "accent": "#000000"}},
    "JOR": {"nickname": "Al-Nashama",        "confederation": "AFC",  "colors": {"primary": "#CE1126", "secondary": "#FFFFFF", "accent": "#007A3D"}},
    "IRQ": {"nickname": "Lions of Mesopotamia", "confederation": "AFC", "colors": {"primary": "#CE1126", "secondary": "#FFFFFF", "accent": "#007A3D"}},
    "UZB": {"nickname": "Oq Bo'rilar",       "confederation": "AFC",  "colors": {"primary": "#1EB53A", "secondary": "#FFFFFF", "accent": "#0099B5"}},
    "RSA": {"nickname": "Bafana Bafana",     "confederation": "CAF",  "colors": {"primary": "#007A4D", "secondary": "#FFB81C", "accent": "#DE3831"}},
    "BIH": {"nickname": "Zmajevi",           "confederation": "UEFA", "colors": {"primary": "#002F6C", "secondary": "#FECB00", "accent": "#FFFFFF"}},
    "CPV": {"nickname": "Tubarões Azuis",    "confederation": "CAF",  "colors": {"primary": "#003893", "secondary": "#FFFFFF", "accent": "#CF2027"}},
    "HAI": {"nickname": "Les Grenadiers",    "confederation": "CONCACAF", "colors": {"primary": "#00209F", "secondary": "#D21034", "accent": "#FFFFFF"}},
    "NZL": {"nickname": "All Whites",         "confederation": "OFC",  "colors": {"primary": "#FFFFFF", "secondary": "#000000", "accent": "#012169"}},
    "CUW": {"nickname": "Bida i Skuadra",    "confederation": "CONCACAF", "colors": {"primary": "#002B7F", "secondary": "#F9E814", "accent": "#FFFFFF"}},
}


# ---------------------------------------------------------------------------
# Head coaches, single reviewable block for all 48. Hand-maintained (no free
# live source). nationality_code is the a2 for the inline flag. Verify before
# the tournament; managers do change. Confidence noted where lower.
# ---------------------------------------------------------------------------
COACHES: dict[str, dict] = {
    # --- top 16 (cross-checked vs the user's examples) ---
    "ARG": {"name": "Lionel Scaloni", "nationality_code": "ar"},
    "FRA": {"name": "Didier Deschamps", "nationality_code": "fr"},
    "ESP": {"name": "Luis de la Fuente", "nationality_code": "es"},
    "ENG": {"name": "Thomas Tuchel", "nationality_code": "de"},
    "BRA": {"name": "Carlo Ancelotti", "nationality_code": "it"},
    "POR": {"name": "Roberto Martínez", "nationality_code": "es"},
    "NED": {"name": "Ronald Koeman", "nationality_code": "nl"},
    "BEL": {"name": "Rudi Garcia", "nationality_code": "fr"},
    "GER": {"name": "Julian Nagelsmann", "nationality_code": "de"},
    "CRO": {"name": "Zlatko Dalić", "nationality_code": "hr"},
    "URY": {"name": "Marcelo Bielsa", "nationality_code": "ar"},
    "COL": {"name": "Néstor Lorenzo", "nationality_code": "ar"},
    "MAR": {"name": "Walid Regragui", "nationality_code": "ma"},
    "USA": {"name": "Mauricio Pochettino", "nationality_code": "ar"},
    "SUI": {"name": "Murat Yakin", "nationality_code": "ch"},
    "JPN": {"name": "Hajime Moriyasu", "nationality_code": "jp"},
    # --- tier 2 ---
    "SEN": {"name": "Pape Thiaw", "nationality_code": "sn"},
    "KOR": {"name": "Hong Myung-bo", "nationality_code": "kr"},
    "MEX": {"name": "Javier Aguirre", "nationality_code": "mx"},
    "ECU": {"name": "Sebastián Beccacece", "nationality_code": "ar"},
    "AUT": {"name": "Ralf Rangnick", "nationality_code": "de"},
    "SWE": {"name": "Jon Dahl Tomasson", "nationality_code": "dk"},
    "TUR": {"name": "Vincenzo Montella", "nationality_code": "it"},
    "AUS": {"name": "Tony Popovic", "nationality_code": "au"},
    "CIV": {"name": "Emerse Faé", "nationality_code": "ci"},
    "EGY": {"name": "Hossam Hassan", "nationality_code": "eg"},
    "NOR": {"name": "Ståle Solbakken", "nationality_code": "no"},
    "CAN": {"name": "Jesse Marsch", "nationality_code": "us"},
    "PAR": {"name": "Gustavo Alfaro", "nationality_code": "ar"},
    "TUN": {"name": "Sabri Lamouchi", "nationality_code": "fr"},
    "CZE": {"name": "Ivan Hašek", "nationality_code": "cz"},
    "ALG": {"name": "Vladimir Petković", "nationality_code": "ch"},
    "PAN": {"name": "Thomas Christiansen", "nationality_code": "dk"},
    "GHA": {"name": "Otto Addo", "nationality_code": "gh"},
    "COD": {"name": "Sébastien Desabre", "nationality_code": "fr"},
    "IRN": {"name": "Amir Ghalenoei", "nationality_code": "ir"},
    "KSA": {"name": "Giorgos Donis", "nationality_code": "gr"},
    "QAT": {"name": "Julen Lopetegui", "nationality_code": "es"},
    "JOR": {"name": "Jamal Sellami", "nationality_code": "ma"},
    "IRQ": {"name": "Graham Arnold", "nationality_code": "au"},
    "UZB": {"name": "Fabio Cannavaro", "nationality_code": "it"},
    "RSA": {"name": "Hugo Broos", "nationality_code": "be"},
    "BIH": {"name": "Sergej Barbarez", "nationality_code": "ba"},
    "CPV": {"name": "Pedro Brito \"Bubista\"", "nationality_code": "cv"},
    "HAI": {"name": "Sébastien Migné", "nationality_code": "fr"},
    "NZL": {"name": "Darren Bazeley", "nationality_code": "gb-eng"},
    "CUW": {"name": "Dick Advocaat", "nationality_code": "nl"},
    "SCO": {"name": "Steve Clarke", "nationality_code": "gb-sct"},
}


# Continental honours for tier-2 nations (marquees carry theirs in
# NATION_PROFILES). WC titles are derived separately, never listed here.
CONTINENTAL_HONOURS: dict[str, list[dict]] = {
    "SEN": [{"label": "AFCON", "count": 1}],
    "EGY": [{"label": "AFCON", "count": 7}],
    "MEX": [{"label": "Gold Cup", "count": 9}],
    "KOR": [{"label": "Asian Cup", "count": 2}],
    "IRN": [{"label": "Asian Cup", "count": 3}],
    "KSA": [{"label": "Asian Cup", "count": 3}],
    "CIV": [{"label": "AFCON", "count": 3}],
    "ALG": [{"label": "AFCON", "count": 2}],
    "GHA": [{"label": "AFCON", "count": 4}],
    "TUN": [{"label": "AFCON", "count": 1}],
    "RSA": [{"label": "AFCON", "count": 1}],
    "COD": [{"label": "AFCON", "count": 2}],
    "CAN": [{"label": "Gold Cup", "count": 1}],
    "PAR": [{"label": "Copa", "count": 2}],
    "JOR": [],
    "QAT": [{"label": "Asian Cup", "count": 2}],
    "AUS": [{"label": "Asian Cup", "count": 1}],
}


# ---------------------------------------------------------------------------
# Federation crests, the real association emblems (FFF cockerel, FA three
# lions, CBF…), NOT flags. Sourced once from TheSportsDB (free, crowd-sourced
# team badges), all 512×512 PNGs on a stable CDN. 48/48. The nation showcase
# slide n1 shows this as a small inset beside the big flag hero.
#   football-data crests were flags, not emblems, that's why they're not used.
#   Refresh by re-running the TheSportsDB searchteams fetch if a logo updates.
# ---------------------------------------------------------------------------
NATION_CREST: dict[str, str] = {
    "ALG": "https://r2.thesportsdb.com/images/media/team/badge/rrwpry1455460218.png",
    "ARG": "https://r2.thesportsdb.com/images/media/team/badge/3zplhu1726167477.png",
    "AUS": "https://r2.thesportsdb.com/images/media/team/badge/lark6k1661780848.png",
    "AUT": "https://r2.thesportsdb.com/images/media/team/badge/874p631628721400.png",
    "BEL": "https://r2.thesportsdb.com/images/media/team/badge/8xlvxv1592062265.png",
    "BIH": "https://r2.thesportsdb.com/images/media/team/badge/hu9lj21739378200.png",
    "BRA": "https://r2.thesportsdb.com/images/media/team/badge/jl6dip1726167280.png",
    "CAN": "https://r2.thesportsdb.com/images/media/team/badge/2t631f1595154867.png",
    "CIV": "https://r2.thesportsdb.com/images/media/team/badge/rwxuuu1455465643.png",
    "COD": "https://r2.thesportsdb.com/images/media/team/badge/s85jjw1728749022.png",
    "COL": "https://r2.thesportsdb.com/images/media/team/badge/4ymyku1691180081.png",
    "CPV": "https://r2.thesportsdb.com/images/media/team/badge/5jn0o71593280376.png",
    "CRO": "https://r2.thesportsdb.com/images/media/team/badge/vvtsyu1455465317.png",
    "CUW": "https://r2.thesportsdb.com/images/media/team/badge/itygvb1600955363.png",
    "CZE": "https://r2.thesportsdb.com/images/media/team/badge/1o0cx31654205806.png",
    "ECU": "https://r2.thesportsdb.com/images/media/team/badge/47wv2y1591989301.png",
    "EGY": "https://r2.thesportsdb.com/images/media/team/badge/uheyzo1742102234.png",
    "ENG": "https://r2.thesportsdb.com/images/media/team/badge/vf5ttc1726166739.png",
    "ESP": "https://r2.thesportsdb.com/images/media/team/badge/ncgqyr1726166942.png",
    "FRA": "https://r2.thesportsdb.com/images/media/team/badge/p3n0z51726166851.png",
    "GER": "https://r2.thesportsdb.com/images/media/team/badge/1xysi51726167152.png",
    "GHA": "https://r2.thesportsdb.com/images/media/team/badge/j589xw1751526124.png",
    "HAI": "https://r2.thesportsdb.com/images/media/team/badge/gml8wx1598135302.png",
    "IRN": "https://r2.thesportsdb.com/images/media/team/badge/uttpvw1455465617.png",
    "IRQ": "https://r2.thesportsdb.com/images/media/team/badge/aqidfn1742100110.png",
    "JOR": "https://r2.thesportsdb.com/images/media/team/badge/59fo2s1742100034.png",
    "JPN": "https://r2.thesportsdb.com/images/media/team/badge/ffsyxz1591989843.png",
    "KOR": "https://r2.thesportsdb.com/images/media/team/badge/a8nqfs1589564916.png",
    "KSA": "https://r2.thesportsdb.com/images/media/team/badge/24xwpq1594125742.png",
    "MAR": "https://r2.thesportsdb.com/images/media/team/badge/hbmwkj1731791275.png",
    "MEX": "https://r2.thesportsdb.com/images/media/team/badge/3rmosi1748525208.png",
    "NED": "https://r2.thesportsdb.com/images/media/team/badge/1p0hr41593787110.png",
    "NOR": "https://r2.thesportsdb.com/images/media/team/badge/gyfn811591973155.png",
    "NZL": "https://r2.thesportsdb.com/images/media/team/badge/91xpk81742982935.png",
    "PAN": "https://r2.thesportsdb.com/images/media/team/badge/asp2ck1715849700.png",
    "PAR": "https://r2.thesportsdb.com/images/media/team/badge/khgav41553419195.png",
    "POR": "https://r2.thesportsdb.com/images/media/team/badge/swqvpy1455466083.png",
    "QAT": "https://r2.thesportsdb.com/images/media/team/badge/rs3ir31642708685.png",
    "RSA": "https://r2.thesportsdb.com/images/media/team/badge/xjz9j91553368824.png",
    "SCO": "https://r2.thesportsdb.com/images/media/team/badge/3691i11552945146.png",
    "SEN": "https://www.thesportsdb.com/images/media/team/badge/slayb01780546342.png",
    "SUI": "https://r2.thesportsdb.com/images/media/team/badge/mb7yqe1717365808.png",
    "SWE": "https://r2.thesportsdb.com/images/media/team/badge/h5adzg1591981772.png",
    "TUN": "https://r2.thesportsdb.com/images/media/team/badge/7r89rg1526727277.png",
    "TUR": "https://r2.thesportsdb.com/images/media/team/badge/70c4oo1591982459.png",
    "URY": "https://r2.thesportsdb.com/images/media/team/badge/6vjbr11726167756.png",
    "USA": "https://r2.thesportsdb.com/images/media/team/badge/86mluc1731001482.png",
    "UZB": "https://r2.thesportsdb.com/images/media/team/badge/u5bgze1597943605.png",
}


# ---------------------------------------------------------------------------
# "Players to watch", the rising / under-the-radar names worth keeping an eye
# on per nation, distinct from the marquee star in STARS. Used in slide 2 of
# the nation showcase, names-only (no photo) to stay compact.
# ---------------------------------------------------------------------------
PLAYERS_TO_WATCH: dict[str, list[str]] = {
    "ARG": ["Julián Álvarez", "Alejandro Garnacho"],
    "FRA": ["Désiré Doué", "William Saliba"],
    "ESP": ["Lamine Yamal", "Pedri"],
    "ENG": ["Bukayo Saka", "Cole Palmer"],
    "BRA": ["Endrick", "Estêvão Willian"],
    "POR": ["João Neves", "Rafael Leão"],
    "NED": ["Xavi Simons", "Cody Gakpo"],
    "BEL": ["Jérémy Doku", "Charles De Ketelaere"],
    "GER": ["Florian Wirtz", "Karim Adeyemi"],
    "CRO": ["Joško Gvardiol", "Petar Sučić"],
    "URY": ["Manuel Ugarte", "Maximiliano Araújo"],
    "COL": ["Jhon Durán", "James Rodríguez"],
    "MAR": ["Bilal El Khannouss", "Brahim Díaz"],
    "USA": ["Yunus Musah", "Folarin Balogun"],
    "SUI": ["Manuel Akanji", "Breel Embolo"],
    "JPN": ["Takefusa Kubo", "Kaoru Mitoma"],
    # --- tier 2 ---
    "SEN": ["Nicolas Jackson", "Pape Matar Sarr"],
    "KOR": ["Lee Kang-in", "Kim Min-jae"],
    "MEX": ["Edson Álvarez", "Gilberto Mora"],
    "ECU": ["Kendry Páez", "Piero Hincapié"],
    "AUT": ["Konrad Laimer", "Marcel Sabitzer"],
    "SWE": ["Viktor Gyökeres", "Dejan Kulusevski"],
    "TUR": ["Kenan Yıldız", "Hakan Çalhanoğlu"],
    "AUS": ["Nestory Irankunda", "Garang Kuol"],
    "CIV": ["Amad Diallo", "Simon Adingra"],
    "EGY": ["Omar Marmoush", "Mostafa Mohamed"],
    "NOR": ["Martin Ødegaard", "Antonio Nusa"],
    "CAN": ["Jonathan David", "Tani Oluwaseyi"],
    "PAR": ["Julio Enciso", "Diego Gómez"],
    "TUN": ["Elyes Skhiri", "Montassar Talbi"],
    "CZE": ["Adam Hložek", "Tomáš Souček"],
    "ALG": ["Houssem Aouar", "Ismaël Bennacer"],
    "PAN": ["Ismael Díaz", "Michael Murillo"],
    "GHA": ["Antoine Semenyo", "Thomas Partey"],
    "COD": ["Silas Katompa", "Chancel Mbemba"],
    "IRN": ["Sardar Azmoun", "Mehdi Ghayedi"],
    "KSA": ["Firas Al-Buraikan", "Saud Abdulhamid"],
    "QAT": ["Almoez Ali", "Hassan Al-Haydos"],
    "JOR": ["Yazan Al-Naimat", "Nizar Al-Rashdan"],
    "UZB": ["Abbosbek Fayzullaev", "Khusayin Norchaev"],
    "RSA": ["Percy Tau", "Relebohile Mofokeng"],
    "BIH": ["Amar Dedić", "Benjamin Šeško"],
    "CPV": ["Jovane Cabral", "Gilson Tavares"],
    "HAI": ["Danley Jean Jacques", "Duckens Nazon"],
    "NZL": ["Marko Stamenić", "Liberato Cacace"],
    "CUW": ["Juninho Bacuna", "Jürgen Locadia"],
    "SCO": ["Billy Gilmour", "Andrew Robertson"],
    "IRQ": ["Zidane Iqbal", "Ali Jasim"],
}


# ---------------------------------------------------------------------------
# Per-nation curated key players ("stars"). The FIRST entry is the marquee
# (used by the nation showcase slide). Selection criteria, in order:
#   1. International recognition (Ballon d'Or, big-club captain, talisman)
#   2. Recent club form (UCL contenders preferred)
#   3. Caps + goals for the national team
# Nations not listed fall back to live API squad order (no club / stat shown).
# ---------------------------------------------------------------------------
STARS: dict[str, list[dict]] = {
    "FRA": [
        {"name": "Kylian Mbappé", "club": "Real Madrid", "stat": "48 goals for France"},
        {"name": "Aurélien Tchouaméni", "club": "Real Madrid", "stat": "Midfield engine"},
        {"name": "Mike Maignan", "club": "AC Milan", "stat": "World-class keeper"},
    ],
    "ARG": [
        {"name": "Lionel Messi", "club": "Inter Miami", "stat": "112 goals for Argentina"},
        {"name": "Lautaro Martínez", "club": "Inter Milan", "stat": "Lethal finisher"},
        {"name": "Enzo Fernández", "club": "Chelsea", "stat": "Best Young Player, WC22"},
    ],
    "ESP": [
        {"name": "Lamine Yamal", "club": "Barcelona", "stat": "Generational winger"},
        {"name": "Rodri", "club": "Man City", "stat": "Ballon d'Or 2024"},
        {"name": "Pedri", "club": "Barcelona", "stat": "Midfield metronome"},
    ],
    "ENG": [
        {"name": "Jude Bellingham", "club": "Real Madrid", "stat": "Talisman No.10"},
        {"name": "Harry Kane", "club": "Bayern Munich", "stat": "England top scorer"},
        {"name": "Bukayo Saka", "club": "Arsenal", "stat": "Relentless winger"},
    ],
    "BRA": [
        {"name": "Vinícius Jr", "club": "Real Madrid", "stat": "Champions League menace"},
        {"name": "Rodrygo", "club": "Real Madrid", "stat": "Big-game scorer"},
        {"name": "Bruno Guimarães", "club": "Newcastle", "stat": "Midfield anchor"},
    ],
    "POR": [
        {"name": "Cristiano Ronaldo", "club": "Al-Nassr", "stat": "All-time top scorer"},
        {"name": "Rúben Dias", "club": "Man City", "stat": "Defensive rock"},
        {"name": "Bruno Fernandes", "club": "Man Utd", "stat": "Creative hub"},
    ],
    "NED": [
        {"name": "Virgil van Dijk", "club": "Liverpool", "stat": "Captain & leader"},
        {"name": "Cody Gakpo", "club": "Liverpool", "stat": "Versatile forward"},
        {"name": "Frenkie de Jong", "club": "Barcelona", "stat": "Press-resistant"},
    ],
    "GER": [
        {"name": "Jamal Musiala", "club": "Bayern Munich", "stat": "Dribble king"},
        {"name": "Florian Wirtz", "club": "Leverkusen", "stat": "Playmaker"},
        {"name": "Kai Havertz", "club": "Arsenal", "stat": "Flexible forward"},
    ],
    "BEL": [
        {"name": "Kevin De Bruyne", "club": "Napoli", "stat": "Elite creator"},
        {"name": "Jérémy Doku", "club": "Man City", "stat": "Explosive winger"},
        {"name": "Romelu Lukaku", "club": "Napoli", "stat": "Belgium top scorer"},
    ],
    "CRO": [
        {"name": "Luka Modrić", "club": "Real Madrid", "stat": "Midfield maestro"},
        {"name": "Joško Gvardiol", "club": "Man City", "stat": "Modern defender"},
        {"name": "Mateo Kovačić", "club": "Man City", "stat": "Tempo-setter"},
    ],
    "URY": [
        {"name": "Federico Valverde", "club": "Real Madrid", "stat": "Box-to-box"},
        {"name": "Darwin Núñez", "club": "Liverpool", "stat": "Relentless runner"},
        {"name": "Ronald Araújo", "club": "Barcelona", "stat": "Defensive leader"},
    ],
    "USA": [
        {"name": "Christian Pulisic", "club": "AC Milan", "stat": "Captain America"},
        {"name": "Weston McKennie", "club": "Juventus", "stat": "Engine room"},
        {"name": "Gio Reyna", "club": "Dortmund", "stat": "Creative spark"},
    ],
    "MAR": [
        {"name": "Achraf Hakimi", "club": "PSG", "stat": "Marauding full-back"},
        {"name": "Brahim Díaz", "club": "Real Madrid", "stat": "Silky playmaker"},
        {"name": "Sofyan Amrabat", "club": "Fiorentina", "stat": "Midfield shield"},
    ],
    "COL": [
        {"name": "Luis Díaz", "club": "Liverpool", "stat": "Direct, fearless winger"},
        {"name": "James Rodríguez", "club": "Rayo Vallecano", "stat": "Creative captain"},
        {"name": "Daniel Muñoz", "club": "Crystal Palace", "stat": "Marauding full-back"},
    ],
    "JPN": [
        {"name": "Wataru Endo", "club": "Liverpool", "stat": "Captain & midfield anchor"},
        {"name": "Kaoru Mitoma", "club": "Brighton", "stat": "Premier League dribbler"},
        {"name": "Takefusa Kubo", "club": "Real Sociedad", "stat": "Mr. Right Foot"},
    ],
    "SUI": [
        {"name": "Granit Xhaka", "club": "Bayer Leverkusen", "stat": "Bundesliga champion & captain"},
        {"name": "Manuel Akanji", "club": "Man City", "stat": "Defensive rock"},
        {"name": "Breel Embolo", "club": "Monaco", "stat": "Focal-point striker"},
    ],
    # --- tier 2 (marquee star only; the slide shows the first) ---
    "SEN": [{"name": "Sadio Mané", "club": "Al-Nassr", "stat": "Talisman & all-time top scorer"}],
    "KOR": [{"name": "Son Heung-min", "club": "LAFC", "stat": "Captain & icon"}],
    "MEX": [{"name": "Santiago Giménez", "club": "AC Milan", "stat": "Lead striker"}],
    "ECU": [{"name": "Moisés Caicedo", "club": "Chelsea", "stat": "Midfield engine"}],
    "AUT": [{"name": "David Alaba", "club": "Real Madrid", "stat": "Veteran leader"}],
    "SWE": [{"name": "Alexander Isak", "club": "Liverpool", "stat": "Elite finisher"}],
    "TUR": [{"name": "Arda Güler", "club": "Real Madrid", "stat": "Generational playmaker"}],
    "AUS": [{"name": "Mathew Ryan", "club": "Roma", "stat": "Captain & keeper"}],
    "CIV": [{"name": "Franck Kessié", "club": "Al-Ahli", "stat": "Midfield powerhouse"}],
    "EGY": [{"name": "Mohamed Salah", "club": "Liverpool", "stat": "Egypt's all-time great"}],
    "NOR": [{"name": "Erling Haaland", "club": "Man City", "stat": "Goal machine"}],
    "CAN": [{"name": "Alphonso Davies", "club": "Bayern Munich", "stat": "Flying full-back"}],
    "PAR": [{"name": "Miguel Almirón", "club": "Atlanta United", "stat": "Pace & energy"}],
    "TUN": [{"name": "Hannibal Mejbri", "club": "Burnley", "stat": "Midfield spark"}],
    "CZE": [{"name": "Patrik Schick", "club": "Bayer Leverkusen", "stat": "Clinical striker"}],
    "ALG": [{"name": "Riyad Mahrez", "club": "Al-Ahli", "stat": "Magic left foot"}],
    "PAN": [{"name": "Adalberto Carrasquilla", "club": "Pumas", "stat": "Midfield metronome"}],
    "GHA": [{"name": "Mohammed Kudus", "club": "Tottenham", "stat": "Explosive attacker"}],
    "COD": [{"name": "Yoane Wissa", "club": "Newcastle", "stat": "Versatile forward"}],
    "IRN": [{"name": "Mehdi Taremi", "club": "Inter", "stat": "Lethal centre-forward"}],
    "KSA": [{"name": "Salem Al-Dawsari", "club": "Al-Hilal", "stat": "Match-winner"}],
    "QAT": [{"name": "Akram Afif", "club": "Al-Sadd", "stat": "Asian Cup star"}],
    "JOR": [{"name": "Mousa Al-Tamari", "club": "Montpellier", "stat": "Dynamic winger"}],
    "UZB": [{"name": "Eldor Shomurodov", "club": "Roma", "stat": "Focal striker"}],
    "RSA": [{"name": "Lyle Foster", "club": "Burnley", "stat": "Lead striker"}],
    "BIH": [{"name": "Edin Džeko", "club": "Fenerbahçe", "stat": "Record goalscorer"}],
    "CPV": [{"name": "Ryan Mendes", "club": "Al-Wakrah", "stat": "Captain & creator"}],
    "HAI": [{"name": "Frantzdy Pierrot", "club": "Gaziantep", "stat": "Target man"}],
    "NZL": [{"name": "Chris Wood", "club": "Nottingham Forest", "stat": "Premier League striker"}],
    "CUW": [{"name": "Leandro Bacuna", "club": "free agent", "stat": "Experienced leader"}],
    "SCO": [{"name": "Scott McTominay", "club": "Napoli", "stat": "Serie A champion"}],
    "IRQ": [{"name": "Aymen Hussein", "club": "Al-Qadsiah", "stat": "Lead striker"}],
}

# ---------------------------------------------------------------------------
# Host venues (16 stadiums) with coordinates for the Open-Meteo forecast.
# ---------------------------------------------------------------------------
VENUES: dict[str, dict] = {
    "Estadio Azteca":      {"city": "Mexico City", "country": "Mexico", "capacity": 87523, "lat": 19.3029, "lon": -99.1505,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Vista_a%C3%A9rea_del_Estadio_Azteca_-_2026_-_02.jpg/1920px-Vista_a%C3%A9rea_del_Estadio_Azteca_-_2026_-_02.jpg"},
    "Estadio Akron":       {"city": "Guadalajara", "country": "Mexico", "capacity": 49850, "lat": 20.6819, "lon": -103.4625,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Estadio_Akron_02-07-2022_cabecera_sur_lado_derecho_%283%29.jpg/1920px-Estadio_Akron_02-07-2022_cabecera_sur_lado_derecho_%283%29.jpg"},
    "Estadio BBVA":        {"city": "Monterrey",   "country": "Mexico", "capacity": 53500, "lat": 25.6692, "lon": -100.2444,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/5/57/Mexico_Guadalupe_Monterrey_Estadio_BBVA_Bancomer_fifa_world_cup_2026_6.JPG"},
    "MetLife Stadium":     {"city": "New York/NJ", "country": "USA",    "capacity": 82500, "lat": 40.8135, "lon": -74.0745,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/0/04/Metlife_stadium_%28Aerial_view%29.jpg"},
    "SoFi Stadium":        {"city": "Los Angeles", "country": "USA",    "capacity": 70240, "lat": 33.9535, "lon": -118.3392,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/SoFi_Stadium_2023.jpg/1920px-SoFi_Stadium_2023.jpg"},
    "AT&T Stadium":        {"city": "Dallas",      "country": "USA",    "capacity": 80000, "lat": 32.7473, "lon": -97.0945,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Arlington_June_2020_4_%28AT%26T_Stadium%29.jpg/1920px-Arlington_June_2020_4_%28AT%26T_Stadium%29.jpg"},
    "Mercedes-Benz Stadium": {"city": "Atlanta",   "country": "USA",    "capacity": 71000, "lat": 33.7554, "lon": -84.4008,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/1/10/Mercedes_Benz_Stadium_time_lapse_capture_2017-08-13.jpg"},
    "NRG Stadium":         {"city": "Houston",     "country": "USA",    "capacity": 72220, "lat": 29.6847, "lon": -95.4107,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Nrg_stadium.jpg"},
    "Arrowhead Stadium":   {"city": "Kansas City", "country": "USA",    "capacity": 76416, "lat": 39.0489, "lon": -94.4839,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Aerial_view_of_Arrowhead_Stadium_08-31-2013.jpg/1920px-Aerial_view_of_Arrowhead_Stadium_08-31-2013.jpg"},
    "Lincoln Financial Field": {"city": "Philadelphia", "country": "USA", "capacity": 69596, "lat": 39.9008, "lon": -75.1675,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/a/a1/Lincoln_Financial_Field_%28Aerial_view%29.jpg"},
    "Levi's Stadium":      {"city": "San Francisco Bay", "country": "USA", "capacity": 68500, "lat": 37.4030, "lon": -121.9698,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Levi%27s_Stadium_in_February_2016_prior_to_Super_Bowl_50_%2824398261729%29.jpg/1920px-Levi%27s_Stadium_in_February_2016_prior_to_Super_Bowl_50_%2824398261729%29.jpg"},
    "Lumen Field":         {"city": "Seattle",     "country": "USA",    "capacity": 68740, "lat": 47.5952, "lon": -122.3316,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/2025_FIFA_Club_World_Cup_-_Seattle_Sounders_FC_vs._Atl%C3%A9tico_Madrid_-_05.jpg/1920px-2025_FIFA_Club_World_Cup_-_Seattle_Sounders_FC_vs._Atl%C3%A9tico_Madrid_-_05.jpg"},
    "Gillette Stadium":    {"city": "Boston",      "country": "USA",    "capacity": 65878, "lat": 42.0909, "lon": -71.2643,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/d/db/Gillette_Stadium_%28Top_View%29.jpg"},
    "Hard Rock Stadium":   {"city": "Miami",       "country": "USA",    "capacity": 65326, "lat": 25.9580, "lon": -80.2389,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Hard_Rock_Stadium_for_Super_Bowl_LIV_%2849606710103%29.jpg/1920px-Hard_Rock_Stadium_for_Super_Bowl_LIV_%2849606710103%29.jpg"},
    "BC Place":            {"city": "Vancouver",   "country": "Canada", "capacity": 54500, "lat": 49.2768, "lon": -123.1119,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/BC_Place_2015_Women%27s_FIFA_World_Cup.jpg/1920px-BC_Place_2015_Women%27s_FIFA_World_Cup.jpg"},
    "BMO Field":           {"city": "Toronto",     "country": "Canada", "capacity": 45736, "lat": 43.6332, "lon": -79.4185,
                            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Toronto_BMO_Field_in_2024.jpg/1920px-Toronto_BMO_Field_in_2024.jpg"},
}


# ---------------------------------------------------------------------------
# Host-city brand emblems (16 official FIFA host city logos for WC 2026).
# Keyed by stadium name (the same key used in VENUES) so a stadium post can
# look both up in one shot.
#
# To fill: copy the logo image from https://www.fifa.com/en/tournaments/mens/
# worldcup/canadamexicousa2026/host-cities into series/assets/city_logos/
# (PNG with transparent background). Then paste the official FIFA motif
# description into `motif` below. Empty entries render a graceful placeholder.
# ---------------------------------------------------------------------------
CITY_BRANDS: dict[str, dict] = {
    "Estadio Azteca":          {
        "logo_path": "assets/city_logos/mexico_city.svg",
        "logo_scale": 1.4,
        "motif": "Estadio Azteca becomes the first venue ever to host three World Cup opening matches. CDMX brings 150+ museums and world-renowned cuisine to the world stage.",
        "caption_hook": "The only stadium in history to host THREE World Cups, 1970, 1986, and now 2026. Maradona's Hand of God, Pelé's third trophy, and on June 11 the opener of WC26. Hyped? 👇",
    },
    "Estadio Akron":           {
        "logo_path": "assets/city_logos/guadalajara.webp",
        "motif": "Capital of tequila and mariachi. Four matches in a city where Pelé once shined, and where the famous stadium 'Wave' was born in 1986.",
        "caption_hook": "Home of Chivas Guadalajara, the only Liga MX club that fields Mexican-only players. Mariachi country welcomes the world. ¿Listos? 👇",
    },
    "Estadio BBVA":            {
        "logo_path": "assets/city_logos/monterrey.webp",
        "motif": "Mexico's industrial capital where mountains meet skyscrapers. Four matches at one of Latin America's most modern venues, continuing the 1986 World Cup tradition.",
        "caption_hook": "Nicknamed \"El Gigante de Acero\", The Steel Giant, with the iconic Cerro de la Silla mountain framing every match. Most scenic venue of WC26? 👇",
    },
    "MetLife Stadium":         {
        "logo_path": "assets/city_logos/new_york_nj.svg",
        "motif": "Eight matches including the Final. From the Manhattan skyline to the Jersey Shore, the soccer-passionate region with 120 miles of coastline welcomes the world.",
        "caption_hook": "The road ends here on July 19. The trophy lifts here. Who lifts it? 👇",
    },
    "SoFi Stadium":            {
        "logo_path": "assets/city_logos/los_angeles.svg",
        "motif": "Eight matches including the USMNT opener. A global capital for sport and culture, returning to the legacy of the FIFA World Cup USA 1994 Final.",
        "caption_hook": "Around $5 billion to build, one of the most expensive stadiums ever made. Stage for the USMNT opener vs Paraguay. Tuning in? 👇",
    },
    "AT&T Stadium":            {
        "logo_path": "assets/city_logos/dallas.svg",
        "motif": "Nine matches including five group stage games and the July 14 semi-final. Fun fact: the entire Statue of Liberty fits inside Dallas Stadium with the roof closed.",
        "caption_hook": "Home of one of the largest center-hung HD video boards in sport, and stage for the July 14 semi-final. Texas does it bigger. 👇",
    },
    "Mercedes-Benz Stadium":   {
        "logo_path": "assets/city_logos/atlanta.webp",
        "motif": "Eight matches including a semi-final in the 'City in the Forest', where green neighborhoods meet a fast-growing skyline.",
        "caption_hook": "The eight-petal \"camera-aperture\" roof opens in 8 minutes flat, engineering theatre before kickoff. Hosts a semi-final on July 15. 👇",
    },
    "NRG Stadium":             {
        "logo_path": "assets/city_logos/houston.svg",
        "motif": "A city built for the world stage. Houston brings its global spirit and unmatched hospitality to the world's game.",
        "caption_hook": "The first NFL venue ever built with a retractable roof. Houston's hospitality goes global this summer. Ready? 👇",
    },
    "Arrowhead Stadium":       {
        "logo_path": "assets/city_logos/kansas_city.svg",
        "motif": "The Soccer Capital of America®. Two states united by an unmatched passion for the game, where progress meets promise.",
        "caption_hook": "Guinness World Record holder for the loudest crowd roar, 142.2 decibels. Bring earplugs. Hyped? 👇",
    },
    "Lincoln Financial Field": {
        "logo_path": "assets/city_logos/philadelphia.svg",
        "motif": "Birthplace of American democracy. Six matches including a historic July 4 showdown, coinciding with the United States' 250th anniversary.",
        "caption_hook": "A historic July 4 R16 fixture at the birthplace of American independence, on the country's 250th anniversary. Goosebump matchup? 👇",
    },
    "Levi's Stadium":          {
        "logo_path": "assets/city_logos/bay_area.svg",
        "motif": "Six matches in a region defined by coastlines, culture and innovation. The Bay Area returns to the 1994 World Cup stage.",
        "caption_hook": "Silicon Valley meets the world's game. The Bay Area returns to the WC stage for the first time since 1994. Excited? 👇",
    },
    "Lumen Field":             {
        "logo_path": "assets/city_logos/seattle.svg",
        "motif": "Where the Salish Sea meets the Cascades. Seattle Stadium is famous for record-breaking noise and the raucous Sounders atmosphere.",
        "caption_hook": "Famous for the Sounders crowd, among the loudest open-air venues in North America. Hyped for the noise? 👇",
    },
    "Gillette Stadium":        {
        "logo_path": "assets/city_logos/boston.svg",
        "motif": "Birthplace of the American Revolution, founded in 1630. Seven matches building on Boston's FIFA World Cup USA 1994 legacy.",
        "caption_hook": "Boston's WC return since 1994, seven matches in a region that lives and breathes soccer. Heading there? 👇",
    },
    "Hard Rock Stadium":       {
        "logo_path": "assets/city_logos/miami.svg",
        "motif": "Where Latin America, the Caribbean and Europe meet between the Atlantic Ocean and Biscayne Bay. Diverse, dynamic, ready for the world.",
        "caption_hook": "Hosts BOTH a quarter-final AND the third-place playoff, Miami's full WC arc, from the QF run to the bronze medal match. Which fixture grabs you? 👇",
    },
    "BC Place":                {
        "logo_path": "assets/city_logos/vancouver.webp",
        "motif": "Seven matches at one of the few World Cup stadiums in a downtown core. A 10,000-seat open-air FIFA Fan Festival amphitheatre awaits at Hastings Park.",
        "caption_hook": "One of the only WC venues you can walk to from downtown. A 10,000-seat open-air Fan Festival awaits at Hastings Park. Worth the trip? 👇",
    },
    "BMO Field":               {
        "logo_path": "assets/city_logos/toronto.svg",
        "motif": "Canada's largest city and home of its first soccer-specific stadium. Six matches across 150+ vibrant neighborhoods.",
        "caption_hook": "Canada's first soccer-specific stadium, host of Canada's WC return vs Bosnia on June 12. Watching the Maple Leaf rise? 👇",
    },
}


def city_brand(stadium: str) -> dict | None:
    return CITY_BRANDS.get(stadium)


# Pre-tournament stadium showcase campaign: 16 posts, one per venue, dripped
# at 8-hour intervals starting CAMPAIGN_START_UTC. Order is "earliest first
# hosted match first" so the next-up venue gets its spotlight next.
STADIUM_PUBLISH_ORDER: list[str] = [
    "Estadio Azteca",          # 11 Jun · opening match (MEX vs RSA)
    "Estadio Akron",           # 12 Jun
    "BMO Field",               # 12 Jun
    "SoFi Stadium",            # 13 Jun
    "Levi's Stadium",          # 13 Jun
    "MetLife Stadium",         # 13 Jun · hosts the FINAL
    "Gillette Stadium",        # 14 Jun
    "BC Place",                # 14 Jun
    "NRG Stadium",             # 14 Jun
    "AT&T Stadium",            # 14 Jun
    "Lincoln Financial Field", # 14 Jun
    "Estadio BBVA",            # 15 Jun
    "Mercedes-Benz Stadium",   # 15 Jun
    "Lumen Field",             # 15 Jun
    "Hard Rock Stadium",       # 15 Jun
    "Arrowhead Stadium",       # 17 Jun
]


# Pre-tournament nation showcase campaign: 48 posts, one per nation, dripped
# 4×/day (every 6h). Order is "earliest first group match first" so each
# nation's profile lands ahead of (or around) its opening fixture.
NATION_PUBLISH_ORDER: list[str] = [
    "MEX", "RSA", "CZE", "KOR", "BIH", "CAN", "PAR", "USA",   # 11–12 Jun openers
    "QAT", "SUI", "BRA", "MAR", "HAI", "SCO", "AUS", "TUR",   # 13–14 Jun
    "CUW", "GER", "JPN", "NED", "CIV", "ECU", "SWE", "TUN",   # 14–15 Jun
    "CPV", "ESP", "BEL", "EGY", "KSA", "URY", "IRN", "NZL",   # 15–16 Jun
    "FRA", "SEN", "IRQ", "NOR", "ALG", "ARG", "AUT", "JOR",   # 16–17 Jun
    "COD", "POR", "CRO", "ENG", "GHA", "PAN", "COL", "UZB",   # 17–18 Jun
]

# Local timezone per venue for summer 2026 (UTC offset hours, short label).
# Mexico abolished DST in 2023 → CST = UTC-6 year-round. US/Canada are on DST
# in June-July: Eastern -4 (EDT), Central -5 (CDT), Pacific -7 (PDT).
VENUE_TZ: dict[str, tuple[int, str]] = {
    "Estadio Azteca":        (-6, "CST"),
    "Estadio Akron":         (-6, "CST"),
    "Estadio BBVA":          (-6, "CST"),
    "MetLife Stadium":       (-4, "ET"),
    "SoFi Stadium":          (-7, "PT"),
    "AT&T Stadium":          (-5, "CT"),
    "Mercedes-Benz Stadium": (-4, "ET"),
    "NRG Stadium":           (-5, "CT"),
    "Arrowhead Stadium":     (-5, "CT"),
    "Lincoln Financial Field": (-4, "ET"),
    "Levi's Stadium":        (-7, "PT"),
    "Lumen Field":           (-7, "PT"),
    "Gillette Stadium":      (-4, "ET"),
    "Hard Rock Stadium":     (-4, "ET"),
    "BC Place":              (-7, "PT"),
    "BMO Field":             (-4, "ET"),
}


def tz_for(stadium: str) -> tuple[int, str]:
    """(utc_offset_hours, label) for a stadium; defaults to ET."""
    return VENUE_TZ.get(stadium, (-4, "ET"))


# ---------------------------------------------------------------------------
# Match → venue maps (from the official FIFA WC 2026 schedule).
#
# GROUP_VENUES uses an unordered pair of TLAs so the order football-data
# returns for home/away doesn't matter. Resolved play-off winners as of the
# published schedule: CZE (group A), BIH (B), TUR (D), SWE (F), IRQ (I),
# COD (K). Both teams of every pair are real nations in NATIONS above.
# ---------------------------------------------------------------------------
def _pair(a: str, b: str) -> frozenset[str]:
    return frozenset({a, b})


GROUP_VENUES: dict[frozenset[str], str] = {
    # Group A
    _pair("MEX", "RSA"): "Estadio Azteca",
    _pair("KOR", "CZE"): "Estadio Akron",
    _pair("CZE", "RSA"): "Mercedes-Benz Stadium",
    _pair("MEX", "KOR"): "Estadio Akron",
    _pair("CZE", "MEX"): "Estadio Azteca",
    _pair("RSA", "KOR"): "Estadio BBVA",
    # Group B
    _pair("CAN", "BIH"): "BMO Field",
    _pair("QAT", "SUI"): "Levi's Stadium",
    _pair("SUI", "BIH"): "SoFi Stadium",
    _pair("CAN", "QAT"): "BC Place",
    _pair("SUI", "CAN"): "BC Place",
    _pair("BIH", "QAT"): "Lumen Field",
    # Group C
    _pair("BRA", "MAR"): "MetLife Stadium",
    _pair("HAI", "SCO"): "Gillette Stadium",
    _pair("SCO", "MAR"): "Gillette Stadium",
    _pair("BRA", "HAI"): "Lincoln Financial Field",
    _pair("SCO", "BRA"): "Hard Rock Stadium",
    _pair("MAR", "HAI"): "Mercedes-Benz Stadium",
    # Group D
    _pair("USA", "PAR"): "SoFi Stadium",
    _pair("AUS", "TUR"): "BC Place",
    _pair("TUR", "PAR"): "Levi's Stadium",
    _pair("USA", "AUS"): "Lumen Field",
    _pair("TUR", "USA"): "SoFi Stadium",
    _pair("PAR", "AUS"): "Levi's Stadium",
    # Group E
    _pair("GER", "CUW"): "NRG Stadium",
    _pair("CIV", "ECU"): "Lincoln Financial Field",
    _pair("GER", "CIV"): "BMO Field",
    _pair("ECU", "CUW"): "Arrowhead Stadium",
    _pair("ECU", "GER"): "MetLife Stadium",
    _pair("CUW", "CIV"): "Lincoln Financial Field",
    # Group F
    _pair("NED", "JPN"): "AT&T Stadium",
    _pair("SWE", "TUN"): "Estadio BBVA",
    _pair("NED", "SWE"): "NRG Stadium",
    _pair("TUN", "JPN"): "Estadio BBVA",
    _pair("TUN", "NED"): "Arrowhead Stadium",
    _pair("JPN", "SWE"): "AT&T Stadium",
    # Group G
    _pair("BEL", "EGY"): "Lumen Field",
    _pair("IRN", "NZL"): "SoFi Stadium",
    _pair("BEL", "IRN"): "SoFi Stadium",
    _pair("NZL", "EGY"): "BC Place",
    _pair("NZL", "BEL"): "BC Place",
    _pair("EGY", "IRN"): "Lumen Field",
    # Group H
    _pair("ESP", "CPV"): "Mercedes-Benz Stadium",
    _pair("KSA", "URY"): "Hard Rock Stadium",
    _pair("ESP", "KSA"): "Mercedes-Benz Stadium",
    _pair("URY", "CPV"): "Hard Rock Stadium",
    _pair("URY", "ESP"): "Estadio Akron",
    _pair("CPV", "KSA"): "NRG Stadium",
    # Group I
    _pair("FRA", "SEN"): "MetLife Stadium",
    _pair("IRQ", "NOR"): "Gillette Stadium",
    _pair("FRA", "IRQ"): "Lincoln Financial Field",
    _pair("NOR", "SEN"): "MetLife Stadium",
    _pair("NOR", "FRA"): "Gillette Stadium",
    _pair("SEN", "IRQ"): "BMO Field",
    # Group J
    _pair("AUT", "JOR"): "Levi's Stadium",
    _pair("ARG", "ALG"): "Arrowhead Stadium",
    _pair("ARG", "AUT"): "AT&T Stadium",
    _pair("JOR", "ALG"): "Levi's Stadium",
    _pair("JOR", "ARG"): "AT&T Stadium",
    _pair("ALG", "AUT"): "Arrowhead Stadium",
    # Group K
    _pair("POR", "COD"): "NRG Stadium",
    _pair("UZB", "COL"): "Estadio Azteca",
    _pair("POR", "UZB"): "NRG Stadium",
    _pair("COL", "COD"): "Estadio Akron",
    _pair("COL", "POR"): "Hard Rock Stadium",
    _pair("COD", "UZB"): "Mercedes-Benz Stadium",
    # Group L
    _pair("ENG", "CRO"): "AT&T Stadium",
    _pair("GHA", "PAN"): "BMO Field",
    _pair("ENG", "GHA"): "Gillette Stadium",
    _pair("PAN", "CRO"): "BMO Field",
    _pair("PAN", "ENG"): "MetLife Stadium",
    _pair("CRO", "GHA"): "Lincoln Financial Field",
}


# Knockout venues by (kickoff_date_iso, host_city_keyword). Both Round of 16
# and later rounds are tied to a fixed venue regardless of which teams advance,
# so we look them up by date + city rather than by team pair.
KO_VENUES: dict[tuple[str, str], str] = {
    # Round of 16
    ("2026-06-28", "Los Angeles"):   "SoFi Stadium",
    ("2026-06-29", "Houston"):       "NRG Stadium",
    ("2026-06-29", "Boston"):        "Gillette Stadium",
    ("2026-06-29", "Monterrey"):     "Estadio BBVA",
    ("2026-06-30", "Mexico"):        "Estadio Azteca",
    ("2026-06-30", "New York"):      "MetLife Stadium",
    ("2026-06-30", "Dallas"):        "AT&T Stadium",
    ("2026-07-01", "Atlanta"):       "Mercedes-Benz Stadium",
    ("2026-07-01", "San Francisco"): "Levi's Stadium",
    ("2026-07-01", "Seattle"):       "Lumen Field",
    ("2026-07-02", "Los Angeles"):   "SoFi Stadium",
    ("2026-07-02", "Vancouver"):     "BC Place",
    ("2026-07-02", "Toronto"):       "BMO Field",
    ("2026-07-03", "Miami"):         "Hard Rock Stadium",
    ("2026-07-03", "Dallas"):        "AT&T Stadium",
    ("2026-07-03", "Kansas City"):   "Arrowhead Stadium",
    # Round of 8 (Last 16 / Eighth-finals)
    ("2026-07-04", "Philadelphia"):  "Lincoln Financial Field",
    ("2026-07-04", "Houston"):       "NRG Stadium",
    ("2026-07-05", "New York"):      "MetLife Stadium",
    ("2026-07-05", "Mexico"):        "Estadio Azteca",
    ("2026-07-06", "Dallas"):        "AT&T Stadium",
    ("2026-07-06", "Seattle"):       "Lumen Field",
    ("2026-07-07", "Atlanta"):       "Mercedes-Benz Stadium",
    ("2026-07-07", "Vancouver"):     "BC Place",
    # Quarter-finals
    ("2026-07-09", "Boston"):        "Gillette Stadium",
    ("2026-07-10", "Los Angeles"):   "SoFi Stadium",
    ("2026-07-11", "Miami"):         "Hard Rock Stadium",
    ("2026-07-11", "Kansas City"):   "Arrowhead Stadium",
    # Semi-finals
    ("2026-07-14", "Dallas"):        "AT&T Stadium",
    ("2026-07-15", "Atlanta"):       "Mercedes-Benz Stadium",
    # Third place & final
    ("2026-07-18", "Miami"):         "Hard Rock Stadium",
    ("2026-07-19", "New York"):      "MetLife Stadium",
}


def venue_for(home_tla: str, away_tla: str) -> str | None:
    return GROUP_VENUES.get(_pair(home_tla.upper(), away_tla.upper()))


def ko_venue_for(date_iso: str, host_city: str) -> str | None:
    return KO_VENUES.get((date_iso, host_city))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def nation(tla: str) -> dict:
    """Return the reference dict for a tla, or a safe default."""
    return NATIONS.get((tla or "").upper(), {"a2": "un", "rank": 50, "value": 100, "top5": 2})


def alpha2(tla: str) -> str:
    return nation(tla)["a2"]


def stars_for(tla: str) -> list[dict]:
    return STARS.get((tla or "").upper(), [])


def profile_for(tla: str) -> dict | None:
    """Editorial profile for a nation showcase post. None if not yet curated."""
    return NATION_PROFILES.get((tla or "").upper())


def crest_for(tla: str) -> str | None:
    """Federation crest URL (TheSportsDB). None if unknown."""
    return NATION_CREST.get((tla or "").upper())


def coach_for(tla: str) -> dict | None:
    """Head coach {name, nationality_code}. None if not on file."""
    return COACHES.get((tla or "").upper())


def continental_honours_for(tla: str) -> list[dict]:
    """Curated continental honours (Euro/Copa/AFCON…) for tier-2 nations.
    Marquees carry theirs in NATION_PROFILES; this fills the rest."""
    return CONTINENTAL_HONOURS.get((tla or "").upper(), [])


def players_to_watch_for(tla: str) -> list[str]:
    """Rising/under-the-radar players to keep an eye on (excludes the star)."""
    return PLAYERS_TO_WATCH.get((tla or "").upper(), [])


def group_for(tla: str) -> tuple[str | None, list[str]]:
    """Return (group_letter, [4 tlas in that group]) for the given nation.

    Derives the group composition by reverse-walking GROUP_VENUES, each tla
    appears in 3 pairs, the union is the group. The letter mapping mirrors the
    GROUP_LETTERS order used in fetch_match's schedule generator (A → L).
    """
    tla = (tla or "").upper()
    members = set()
    for pair in GROUP_VENUES:
        if tla in pair:
            members.update(pair)
    if not members:
        return None, []
    # Group letter: find a representative pair in the canonical group order.
    GROUP_ORDER = [
        ("A", {"MEX", "RSA", "KOR", "CZE"}),
        ("B", {"CAN", "BIH", "QAT", "SUI"}),
        ("C", {"BRA", "MAR", "HAI", "SCO"}),
        ("D", {"USA", "PAR", "AUS", "TUR"}),
        ("E", {"GER", "CUW", "CIV", "ECU"}),
        ("F", {"NED", "JPN", "SWE", "TUN"}),
        ("G", {"BEL", "EGY", "IRN", "NZL"}),
        ("H", {"ESP", "CPV", "KSA", "URY"}),
        ("I", {"FRA", "SEN", "IRQ", "NOR"}),
        ("J", {"AUT", "JOR", "ARG", "ALG"}),
        ("K", {"POR", "COD", "UZB", "COL"}),
        ("L", {"ENG", "CRO", "GHA", "PAN"}),
    ]
    for letter, teams in GROUP_ORDER:
        if tla in teams:
            return letter, sorted(teams)
    return None, sorted(members)


def venue(name: str) -> dict | None:
    return VENUES.get(name)


# Typical late-June / July afternoon temperature (°C) per host venue. Used as a
# fallback when Open-Meteo has no forecast — its API only reaches ~16 days out,
# so knockout-stage fixtures (and any preview built early, or any transient API
# failure) fall back to these so the slide never shows a blank "-".
SUMMER_AVG_C: dict[str, int] = {
    "Estadio Azteca": 23, "Estadio Akron": 25, "Estadio BBVA": 31,
    "MetLife Stadium": 27, "SoFi Stadium": 24, "AT&T Stadium": 34,
    "Mercedes-Benz Stadium": 30, "NRG Stadium": 33, "Arrowhead Stadium": 30,
    "Lincoln Financial Field": 29, "Levi's Stadium": 23, "Lumen Field": 23,
    "Gillette Stadium": 26, "Hard Rock Stadium": 31, "BC Place": 21,
    "BMO Field": 26,
}


def summer_temp(name: str) -> int | None:
    """Fallback afternoon temperature (°C) for a venue when no forecast exists."""
    return SUMMER_AVG_C.get(name)

# ===== AUTO-GENERATED SCHEDULE, DO NOT EDIT BY HAND =====
# Source: football-data.org /competitions/WC/matches (104 fixtures).
# Regenerate via `python _gen_schedule.py` whenever the official schedule changes.

MATCH_KICKOFF_UTC: dict[int, str] = {
    # ----- GROUP_STAGE (72) -----
    537327: "2026-06-11T19:00:00Z",  # A · MEX vs RSA
    537328: "2026-06-12T02:00:00Z",  # A · KOR vs CZE
    537333: "2026-06-12T19:00:00Z",  # B · CAN vs BIH
    537345: "2026-06-13T01:00:00Z",  # D · USA vs PAR
    537334: "2026-06-13T19:00:00Z",  # B · QAT vs SUI
    537339: "2026-06-13T22:00:00Z",  # C · BRA vs MAR
    537340: "2026-06-14T01:00:00Z",  # C · HAI vs SCO
    537346: "2026-06-14T04:00:00Z",  # D · AUS vs TUR
    537351: "2026-06-14T17:00:00Z",  # E · GER vs CUW
    537357: "2026-06-14T20:00:00Z",  # F · NED vs JPN
    537352: "2026-06-14T23:00:00Z",  # E · CIV vs ECU
    537358: "2026-06-15T02:00:00Z",  # F · SWE vs TUN
    537369: "2026-06-15T16:00:00Z",  # H · ESP vs CPV
    537363: "2026-06-15T19:00:00Z",  # G · BEL vs EGY
    537370: "2026-06-15T22:00:00Z",  # H · KSA vs URY
    537364: "2026-06-16T01:00:00Z",  # G · IRN vs NZL
    537391: "2026-06-16T19:00:00Z",  # I · FRA vs SEN
    537392: "2026-06-16T22:00:00Z",  # I · IRQ vs NOR
    537397: "2026-06-17T01:00:00Z",  # J · ARG vs ALG
    537398: "2026-06-17T04:00:00Z",  # J · AUT vs JOR
    537403: "2026-06-17T17:00:00Z",  # K · POR vs COD
    537409: "2026-06-17T20:00:00Z",  # L · ENG vs CRO
    537410: "2026-06-17T23:00:00Z",  # L · GHA vs PAN
    537404: "2026-06-18T02:00:00Z",  # K · UZB vs COL
    537329: "2026-06-18T16:00:00Z",  # A · CZE vs RSA
    537335: "2026-06-18T19:00:00Z",  # B · SUI vs BIH
    537336: "2026-06-18T22:00:00Z",  # B · CAN vs QAT
    537330: "2026-06-19T01:00:00Z",  # A · MEX vs KOR
    537348: "2026-06-19T19:00:00Z",  # D · USA vs AUS
    537342: "2026-06-19T22:00:00Z",  # C · SCO vs MAR
    537341: "2026-06-20T00:30:00Z",  # C · BRA vs HAI
    537347: "2026-06-20T03:00:00Z",  # D · TUR vs PAR
    537359: "2026-06-20T17:00:00Z",  # F · NED vs SWE
    537353: "2026-06-20T20:00:00Z",  # E · GER vs CIV
    537354: "2026-06-21T00:00:00Z",  # E · ECU vs CUW
    537360: "2026-06-21T04:00:00Z",  # F · TUN vs JPN
    537371: "2026-06-21T16:00:00Z",  # H · ESP vs KSA
    537365: "2026-06-21T19:00:00Z",  # G · BEL vs IRN
    537372: "2026-06-21T22:00:00Z",  # H · URY vs CPV
    537366: "2026-06-22T01:00:00Z",  # G · NZL vs EGY
    537399: "2026-06-22T17:00:00Z",  # J · ARG vs AUT
    537393: "2026-06-22T21:00:00Z",  # I · FRA vs IRQ
    537394: "2026-06-23T00:00:00Z",  # I · NOR vs SEN
    537400: "2026-06-23T03:00:00Z",  # J · JOR vs ALG
    537405: "2026-06-23T17:00:00Z",  # K · POR vs UZB
    537411: "2026-06-23T20:00:00Z",  # L · ENG vs GHA
    537412: "2026-06-23T23:00:00Z",  # L · PAN vs CRO
    537406: "2026-06-24T02:00:00Z",  # K · COL vs COD
    537337: "2026-06-24T19:00:00Z",  # B · SUI vs CAN
    537338: "2026-06-24T19:00:00Z",  # B · BIH vs QAT
    537344: "2026-06-24T22:00:00Z",  # C · MAR vs HAI
    537343: "2026-06-24T22:00:00Z",  # C · SCO vs BRA
    537331: "2026-06-25T01:00:00Z",  # A · CZE vs MEX
    537332: "2026-06-25T01:00:00Z",  # A · RSA vs KOR
    537355: "2026-06-25T20:00:00Z",  # E · ECU vs GER
    537356: "2026-06-25T20:00:00Z",  # E · CUW vs CIV
    537361: "2026-06-25T23:00:00Z",  # F · TUN vs NED
    537362: "2026-06-25T23:00:00Z",  # F · JPN vs SWE
    537349: "2026-06-26T02:00:00Z",  # D · TUR vs USA
    537350: "2026-06-26T02:00:00Z",  # D · PAR vs AUS
    537395: "2026-06-26T19:00:00Z",  # I · NOR vs FRA
    537396: "2026-06-26T19:00:00Z",  # I · SEN vs IRQ
    537373: "2026-06-27T00:00:00Z",  # H · URY vs ESP
    537374: "2026-06-27T00:00:00Z",  # H · CPV vs KSA
    537367: "2026-06-27T03:00:00Z",  # G · NZL vs BEL
    537368: "2026-06-27T03:00:00Z",  # G · EGY vs IRN
    537413: "2026-06-27T21:00:00Z",  # L · PAN vs ENG
    537414: "2026-06-27T21:00:00Z",  # L · CRO vs GHA
    537407: "2026-06-27T23:30:00Z",  # K · COL vs POR
    537408: "2026-06-27T23:30:00Z",  # K · COD vs UZB
    537401: "2026-06-28T02:00:00Z",  # J · JOR vs ARG
    537402: "2026-06-28T02:00:00Z",  # J · ALG vs AUT
    # ----- LAST_32 (16) -----
    537417: "2026-06-28T19:00:00Z",  # TBD vs TBD
    537423: "2026-06-29T17:00:00Z",  # TBD vs TBD
    537415: "2026-06-29T20:30:00Z",  # TBD vs TBD
    537418: "2026-06-30T01:00:00Z",  # TBD vs TBD
    537424: "2026-06-30T17:00:00Z",  # TBD vs TBD
    537416: "2026-06-30T21:00:00Z",  # TBD vs TBD
    537425: "2026-07-01T01:00:00Z",  # TBD vs TBD
    537426: "2026-07-01T16:00:00Z",  # TBD vs TBD
    537422: "2026-07-01T20:00:00Z",  # TBD vs TBD
    537421: "2026-07-02T00:00:00Z",  # TBD vs TBD
    537420: "2026-07-02T19:00:00Z",  # TBD vs TBD
    537419: "2026-07-02T23:00:00Z",  # TBD vs TBD
    537429: "2026-07-03T03:00:00Z",  # TBD vs TBD
    537428: "2026-07-03T18:00:00Z",  # TBD vs TBD
    537427: "2026-07-03T22:00:00Z",  # TBD vs TBD
    537430: "2026-07-04T01:30:00Z",  # TBD vs TBD
    # ----- LAST_16 (8) -----
    537376: "2026-07-04T17:00:00Z",  # TBD vs TBD
    537375: "2026-07-04T21:00:00Z",  # TBD vs TBD
    537377: "2026-07-05T20:00:00Z",  # TBD vs TBD
    537378: "2026-07-06T00:00:00Z",  # TBD vs TBD
    537379: "2026-07-06T19:00:00Z",  # TBD vs TBD
    537380: "2026-07-07T00:00:00Z",  # TBD vs TBD
    537381: "2026-07-07T16:00:00Z",  # TBD vs TBD
    537382: "2026-07-07T20:00:00Z",  # TBD vs TBD
    # ----- QUARTER_FINALS (4) -----
    537383: "2026-07-09T20:00:00Z",  # TBD vs TBD
    537384: "2026-07-10T19:00:00Z",  # TBD vs TBD
    537385: "2026-07-11T21:00:00Z",  # TBD vs TBD
    537386: "2026-07-12T01:00:00Z",  # TBD vs TBD
    # ----- SEMI_FINALS (2) -----
    537387: "2026-07-14T19:00:00Z",  # TBD vs TBD
    537388: "2026-07-15T19:00:00Z",  # TBD vs TBD
    # ----- THIRD_PLACE (1) -----
    537389: "2026-07-18T21:00:00Z",  # TBD vs TBD
    # ----- FINAL (1) -----
    537390: "2026-07-19T19:00:00Z",  # TBD vs TBD
}

GROUP_PAIR_ID: dict[frozenset[str], int] = {
    frozenset({"MEX", "RSA"}): 537327,  # Group A
    frozenset({"KOR", "CZE"}): 537328,  # Group A
    frozenset({"CAN", "BIH"}): 537333,  # Group B
    frozenset({"USA", "PAR"}): 537345,  # Group D
    frozenset({"QAT", "SUI"}): 537334,  # Group B
    frozenset({"BRA", "MAR"}): 537339,  # Group C
    frozenset({"HAI", "SCO"}): 537340,  # Group C
    frozenset({"AUS", "TUR"}): 537346,  # Group D
    frozenset({"GER", "CUW"}): 537351,  # Group E
    frozenset({"NED", "JPN"}): 537357,  # Group F
    frozenset({"CIV", "ECU"}): 537352,  # Group E
    frozenset({"SWE", "TUN"}): 537358,  # Group F
    frozenset({"ESP", "CPV"}): 537369,  # Group H
    frozenset({"BEL", "EGY"}): 537363,  # Group G
    frozenset({"KSA", "URY"}): 537370,  # Group H
    frozenset({"IRN", "NZL"}): 537364,  # Group G
    frozenset({"FRA", "SEN"}): 537391,  # Group I
    frozenset({"IRQ", "NOR"}): 537392,  # Group I
    frozenset({"ARG", "ALG"}): 537397,  # Group J
    frozenset({"AUT", "JOR"}): 537398,  # Group J
    frozenset({"POR", "COD"}): 537403,  # Group K
    frozenset({"ENG", "CRO"}): 537409,  # Group L
    frozenset({"GHA", "PAN"}): 537410,  # Group L
    frozenset({"UZB", "COL"}): 537404,  # Group K
    frozenset({"CZE", "RSA"}): 537329,  # Group A
    frozenset({"SUI", "BIH"}): 537335,  # Group B
    frozenset({"CAN", "QAT"}): 537336,  # Group B
    frozenset({"MEX", "KOR"}): 537330,  # Group A
    frozenset({"USA", "AUS"}): 537348,  # Group D
    frozenset({"SCO", "MAR"}): 537342,  # Group C
    frozenset({"BRA", "HAI"}): 537341,  # Group C
    frozenset({"TUR", "PAR"}): 537347,  # Group D
    frozenset({"NED", "SWE"}): 537359,  # Group F
    frozenset({"GER", "CIV"}): 537353,  # Group E
    frozenset({"ECU", "CUW"}): 537354,  # Group E
    frozenset({"TUN", "JPN"}): 537360,  # Group F
    frozenset({"ESP", "KSA"}): 537371,  # Group H
    frozenset({"BEL", "IRN"}): 537365,  # Group G
    frozenset({"URY", "CPV"}): 537372,  # Group H
    frozenset({"NZL", "EGY"}): 537366,  # Group G
    frozenset({"ARG", "AUT"}): 537399,  # Group J
    frozenset({"FRA", "IRQ"}): 537393,  # Group I
    frozenset({"NOR", "SEN"}): 537394,  # Group I
    frozenset({"JOR", "ALG"}): 537400,  # Group J
    frozenset({"POR", "UZB"}): 537405,  # Group K
    frozenset({"ENG", "GHA"}): 537411,  # Group L
    frozenset({"PAN", "CRO"}): 537412,  # Group L
    frozenset({"COL", "COD"}): 537406,  # Group K
    frozenset({"SUI", "CAN"}): 537337,  # Group B
    frozenset({"BIH", "QAT"}): 537338,  # Group B
    frozenset({"MAR", "HAI"}): 537344,  # Group C
    frozenset({"SCO", "BRA"}): 537343,  # Group C
    frozenset({"CZE", "MEX"}): 537331,  # Group A
    frozenset({"RSA", "KOR"}): 537332,  # Group A
    frozenset({"ECU", "GER"}): 537355,  # Group E
    frozenset({"CUW", "CIV"}): 537356,  # Group E
    frozenset({"TUN", "NED"}): 537361,  # Group F
    frozenset({"JPN", "SWE"}): 537362,  # Group F
    frozenset({"TUR", "USA"}): 537349,  # Group D
    frozenset({"PAR", "AUS"}): 537350,  # Group D
    frozenset({"NOR", "FRA"}): 537395,  # Group I
    frozenset({"SEN", "IRQ"}): 537396,  # Group I
    frozenset({"URY", "ESP"}): 537373,  # Group H
    frozenset({"CPV", "KSA"}): 537374,  # Group H
    frozenset({"NZL", "BEL"}): 537367,  # Group G
    frozenset({"EGY", "IRN"}): 537368,  # Group G
    frozenset({"PAN", "ENG"}): 537413,  # Group L
    frozenset({"CRO", "GHA"}): 537414,  # Group L
    frozenset({"COL", "POR"}): 537407,  # Group K
    frozenset({"COD", "UZB"}): 537408,  # Group K
    frozenset({"JOR", "ARG"}): 537401,  # Group J
    frozenset({"ALG", "AUT"}): 537402,  # Group J
}

MATCH_STAGE: dict[int, str] = {
    537327: "group",
    537328: "group",
    537333: "group",
    537345: "group",
    537334: "group",
    537339: "group",
    537340: "group",
    537346: "group",
    537351: "group",
    537357: "group",
    537352: "group",
    537358: "group",
    537369: "group",
    537363: "group",
    537370: "group",
    537364: "group",
    537391: "group",
    537392: "group",
    537397: "group",
    537398: "group",
    537403: "group",
    537409: "group",
    537410: "group",
    537404: "group",
    537329: "group",
    537335: "group",
    537336: "group",
    537330: "group",
    537348: "group",
    537342: "group",
    537341: "group",
    537347: "group",
    537359: "group",
    537353: "group",
    537354: "group",
    537360: "group",
    537371: "group",
    537365: "group",
    537372: "group",
    537366: "group",
    537399: "group",
    537393: "group",
    537394: "group",
    537400: "group",
    537405: "group",
    537411: "group",
    537412: "group",
    537406: "group",
    537337: "group",
    537338: "group",
    537344: "group",
    537343: "group",
    537331: "group",
    537332: "group",
    537355: "group",
    537356: "group",
    537361: "group",
    537362: "group",
    537349: "group",
    537350: "group",
    537395: "group",
    537396: "group",
    537373: "group",
    537374: "group",
    537367: "group",
    537368: "group",
    537413: "group",
    537414: "group",
    537407: "group",
    537408: "group",
    537401: "group",
    537402: "group",
    537417: "r32",
    537423: "r32",
    537415: "r32",
    537418: "r32",
    537424: "r32",
    537416: "r32",
    537425: "r32",
    537426: "r32",
    537422: "r32",
    537421: "r32",
    537420: "r32",
    537419: "r32",
    537429: "r32",
    537428: "r32",
    537427: "r32",
    537430: "r32",
    537376: "r16",
    537375: "r16",
    537377: "r16",
    537378: "r16",
    537379: "r16",
    537380: "r16",
    537381: "r16",
    537382: "r16",
    537383: "qf",
    537384: "qf",
    537385: "qf",
    537386: "qf",
    537387: "sf",
    537388: "sf",
    537389: "third",
    537390: "final",
}

# ===== END AUTO-GENERATED SCHEDULE =====
