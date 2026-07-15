import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from analytics import build_signal_passport


test_match = {
    "country": "Мир",
    "league": "МИР: World Championship U17 Women",
    "home_name": "Латвия U17 (Ж)",
    "away_name": "США U17 (Ж)",
}

passport = build_signal_passport(test_match)

print("СТРАНА:")
print(passport["country"])

print("\nЛИГА:")
print(passport["league"])

print("\nТИП МАТЧА:")
print(passport["match_type"])