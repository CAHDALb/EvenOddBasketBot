import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from match_classifier import detect_match_type


test_matches = [
    {
        "league": "NBA",
        "home_name": "Boston Celtics",
        "away_name": "Miami Heat",
    },
    {
        "league": "Евробаскет - Женщины",
        "home_name": "Германия (Ж)",
        "away_name": "Франция (Ж)",
    },
    {
        "league": "Евробаскет U20 - Женщины",
        "home_name": "Турция U20 (Ж)",
        "away_name": "Словения U20 (Ж)",
    },
    {
        "league": "Молодёжная лига",
        "home_name": "Команда А (18)",
        "away_name": "Команда Б (18)",
    },
]

for match in test_matches:
    print(
        match["home_name"],
        "-",
        match["away_name"],
        "=>",
        detect_match_type(match)
    )