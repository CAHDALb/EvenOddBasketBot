"""
===========================================================
EvenOddBasketBot

Файл:
tests/test_real_signal_score.py

Назначение:
Проверяет Signal Score на реальной статистике
из PostgreSQL Neon.

Тест ничего не изменяет в базе данных.
Он только читает статистику.
===========================================================
"""

import os
import sys


# Добавляем корень проекта в пути Python
PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)


from analytics import build_signal_passport
from intelligence import calculate_signal_score


# =========================================================
# Пример реального типа сигнала
# =========================================================
#
# Здесь мы используем матч, который уже был в нашей базе.
# Сам матч повторно никуда не записывается.
# Он нужен только для определения:
# - страны;
# - лиги;
# - категории матча.
# =========================================================

test_match = {
    "id": "SIGNAL_SCORE_REAL_TEST",

    "country": "Мир",
    "league": "МИР: World Championship U17 Women",

    "home_name": "Латвия U17 (Ж)",
    "away_name": "США U17 (Ж)",

    "q1_total": 43,
    "q2_total": 37,
    "q3_total": 43,
}


# Получаем реальный аналитический паспорт
passport = build_signal_passport(test_match)

# Рассчитываем Signal Score
result = calculate_signal_score(passport)


print("=" * 70)
print("🧠 EvenOddBasketBot — реальный Signal Score")
print("=" * 70)

print()
print("АНАЛИТИЧЕСКИЙ ПАСПОРТ")
print("-" * 70)

print("Страна:")
print(passport["country"])

print()
print("Лига:")
print(passport["league"])

print()
print("Категория:")
print(passport["match_type"])

print()
print("=" * 70)
print("SIGNAL SCORE")
print("=" * 70)

print(
    "Итог:",
    f'{result["score"]} / {result["max_score"]}',
)

print(
    "Уровень:",
    result["level"]["icon"],
    result["level"]["title"],
)

print("-" * 70)

for component in result["components"]:
    print(
        f'{component["name"]}: '
        f'{component["points"]} / '
        f'{component["max_points"]}'
    )

    print("Объяснение:", component["reason"])
    print()

print("-" * 70)
print("Предупреждение:")
print(result["warning"])
print("=" * 70)