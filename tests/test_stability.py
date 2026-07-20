from pprint import pprint

from intelligence.stability import calculate_stability


# ------------------------------------------------------------
# Вспомогательная функция печати
# ------------------------------------------------------------

def print_scenario(
    title: str,
    history: list[str],
) -> None:
    """
    Рассчитывает и красиво печатает Stability.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    print()
    print("История:")
    print(" ".join(history))

    result = calculate_stability(history)

    print()
    print("Результат:")
    pprint(result)

    print()
    print(
        "Stability:",
        result["stability"],
    )

    print(
        "Level:",
        result["level"]["code"],
    )


# ------------------------------------------------------------
# Сценарий 1
# Результаты распределены относительно равномерно
# ------------------------------------------------------------

stable_history = [
    "WIN", "LOSE", "WIN", "WIN", "LOSE",
    "WIN", "LOSE", "WIN", "LOSE", "WIN",
    "WIN", "LOSE", "WIN", "LOSE", "WIN",
    "LOSE", "WIN", "WIN", "LOSE", "WIN",
    "LOSE", "WIN", "LOSE", "WIN", "WIN",
    "LOSE", "WIN", "LOSE", "WIN", "WIN",
]


# ------------------------------------------------------------
# Сценарий 2
# Победы и поражения собраны в длинные серии
# ------------------------------------------------------------

unstable_history = [
    "WIN", "WIN", "WIN", "WIN", "WIN",
    "WIN", "LOSE", "LOSE", "LOSE", "LOSE",
    "LOSE", "LOSE", "LOSE", "WIN", "WIN",
    "WIN", "WIN", "WIN", "LOSE", "LOSE",
    "LOSE", "LOSE", "LOSE", "LOSE", "WIN",
    "WIN", "WIN", "WIN", "WIN", "WIN",
]


# ------------------------------------------------------------
# Сценарий 3
# Слишком мало результатов
# ------------------------------------------------------------

short_history = [
    "WIN",
    "LOSE",
    "WIN",
    "LOSE",
    "WIN",
]


# ------------------------------------------------------------
# Запуск тестов
# ------------------------------------------------------------

print_scenario(
    title="СЦЕНАРИЙ 1 — СТАБИЛЬНАЯ ИСТОРИЯ",
    history=stable_history,
)

print_scenario(
    title="СЦЕНАРИЙ 2 — НЕСТАБИЛЬНАЯ ИСТОРИЯ",
    history=unstable_history,
)

print_scenario(
    title="СЦЕНАРИЙ 3 — НЕДОСТАТОЧНО ДАННЫХ",
    history=short_history,
)


# ------------------------------------------------------------
# Автоматические проверки
# ------------------------------------------------------------

stable_result = calculate_stability(
    stable_history
)

unstable_result = calculate_stability(
    unstable_history
)

short_result = calculate_stability(
    short_history
)

assert stable_result["stability"] > (
    unstable_result["stability"]
)

assert stable_result["level"]["code"] in {
    "good",
    "strong",
}

assert unstable_result["level"]["code"] in {
    "low",
    "medium",
    "good",
}

assert short_result["stability"] == 0

assert (
    short_result["level"]["code"]
    == "insufficient"
)

assert (
    stable_result["is_probability"]
    is False
)

print()
print("=" * 70)
print("✅ ВСЕ ТЕСТЫ STABILITY УСПЕШНО ПРОЙДЕНЫ")
print("=" * 70)