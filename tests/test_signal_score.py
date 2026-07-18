import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from intelligence import calculate_signal_score


# =========================================================
# Тестовый аналитический паспорт
# =========================================================

test_passport = {
    "country": {
        "value": "Тестовая страна",
        "total": 120,
        "wins": 70,
        "loses": 50,
        "win_rate": 58.33,
        "roi": 12.0,
    },
    "league": {
        "value": "Тестовая лига",
        "total": 80,
        "wins": 47,
        "loses": 33,
        "win_rate": 58.75,
        "roi": 11.0,
    },
    "match_type": {
        "value": "youth",
        "total": 250,
        "wins": 145,
        "loses": 105,
        "win_rate": 58.0,
        "roi": 10.5,
    },
}


result = calculate_signal_score(test_passport)


print("=" * 65)
print("🧠 EvenOddBasketBot — Signal Score")
print("=" * 65)

print(
    "Итог:",
    f'{result["score"]} / {result["max_score"]}',
)

print(
    "Уровень:",
    result["level"]["icon"],
    result["level"]["title"],
)

print("-" * 65)

for component in result["components"]:
    print(
        f'{component["name"]}: '
        f'{component["points"]} / '
        f'{component["max_points"]}'
    )

    print("Причина:", component["reason"])
    print()

print("-" * 65)
print(result["warning"])
print("=" * 65)