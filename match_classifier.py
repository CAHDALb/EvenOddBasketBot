"""
===========================================================
EvenOddBasketBot

Файл:
match_classifier.py

Назначение:
Определяет тип баскетбольного матча:
- men    — мужчины;
- women  — женщины;
- youth  — молодёжные соревнования.
===========================================================
"""

import re


# Слова и обозначения женских соревнований
WOMEN_KEYWORDS = (
    "(ж)",
    "(w)",
    " women",
    "women ",
    "female",
    "женщины",
    "жен.",
)


# Слова и обозначения молодёжных соревнований
YOUTH_KEYWORDS = (
    "(мол)",
    "(юн)",
    "youth",
    "junior",
    "juniors",
    "cadet",
    "cadets",
    "молодеж",
    "молодёж",
    "юниор",
)


def detect_match_type(match):
    """
    Определяет тип матча по названию лиги и команд.

    Возвращает:
    youth  — молодёжный матч;
    women  — женский матч;
    men    — мужской матч.
    """

    # Собираем все доступные названия в одну строку
    text = " ".join(
        [
            str(match.get("country") or ""),
            str(match.get("league") or ""),
            str(match.get("home_name") or match.get("home") or ""),
            str(match.get("away_name") or match.get("away") or ""),
        ]
    ).lower()

    # =====================================================
    # Молодёжные обозначения вида:
    # U16, U18, U20, U23, (16), (18), (20) и т. д.
    # =====================================================
    youth_patterns = (
        r"\bu\s?1[4-9]\b",
        r"\bu\s?2[0-3]\b",
        r"\((?:1[4-9]|2[0-3])\)",
    )

    # Молодёжные матчи имеют приоритет над женскими
    if any(re.search(pattern, text) for pattern in youth_patterns):
        return "youth"

    if any(keyword in text for keyword in YOUTH_KEYWORDS):
        return "youth"

    # Проверяем женские обозначения
    if any(keyword in text for keyword in WOMEN_KEYWORDS):
        return "women"

    # Если специальных пометок нет — считаем матч мужским
    return "men"