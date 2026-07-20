"""
test_explanation.py

Отдельная проверка Recommendation Engine.

Проверяем три сценария:

1. Средний сигнал.
2. Слабый сигнал.
3. Сильный сигнал.
"""

from pprint import pprint

from intelligence.explanation import build_recommendation


# ------------------------------------------------------------
# Вспомогательная функция для создания тестового паспорта
# ------------------------------------------------------------

def create_test_passport(
    *,
    signal_score: float,
    confidence: float,
    country_total: int,
    country_roi: float,
    league_total: int,
    league_roi: float,
    match_type_total: int,
    match_type_roi: float,
    confidence_level: str,
) -> dict:
    """
    Создаёт упрощённый Signal Passport
    для отдельной проверки Recommendation Engine.
    """

    return {
        "version": "1.0",

        "country": {
            "name": "Тестовая страна",
            "total": country_total,
            "roi": country_roi,
        },

        "league": {
            "name": "Тестовая лига",
            "total": league_total,
            "roi": league_roi,
        },

        "match_type": {
            "name": "Мужчины",
            "total": match_type_total,
            "roi": match_type_roi,
        },

        "signal_score": signal_score,
        "confidence": confidence,

        "meta": {
            "confidence_analysis": {
                "level": {
                    "code": confidence_level,
                }
            }
        },
    }


# ------------------------------------------------------------
# Красивый вывод результата
# ------------------------------------------------------------

def print_recommendation(
    title: str,
    recommendation: dict,
) -> None:
    """
    Выводит результат проверки в консоль.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    pprint(recommendation)

    print()
    print("-" * 70)
    print(
        f'{recommendation["action"]["icon"]} '
        f'{recommendation["action"]["title"]}'
    )
    print(
        f'Риск: {recommendation["risk"]["title"]}'
    )
    print(
        f'Приоритет: {recommendation["priority"]}'
    )
    print(
        f'Signal Score: {recommendation["signal_score"]}'
    )
    print(
        f'Confidence: {recommendation["confidence"]}'
    )
    print(
        f'Confidence Level: '
        f'{recommendation["confidence_level"]}'
    )

    print()
    print("Итог:")
    print(recommendation["summary"])

    print()
    print("Преимущества:")

    if recommendation["advantages"]:
        for advantage in recommendation["advantages"]:
            print(f"  ✅ {advantage}")
    else:
        print("  — преимущества не обнаружены")

    print()
    print("Предупреждения:")

    if recommendation["warnings"]:
        for warning in recommendation["warnings"]:
            print(f"  ⚠️ {warning}")
    else:
        print("  — предупреждения отсутствуют")


# ------------------------------------------------------------
# Сценарий №1: средняя статистика
# ------------------------------------------------------------

def test_medium_recommendation() -> None:
    """
    Проверяем текущий рабочий пример:

    Signal Score = 58
    Confidence = 63
    """

    passport = create_test_passport(
        signal_score=58,
        confidence=63,
        country_total=60,
        country_roi=12.0,
        league_total=40,
        league_roi=8.0,
        match_type_total=80,
        match_type_roi=7.0,
        confidence_level="silver",
    )

    recommendation = build_recommendation(passport)

    assert recommendation["action"]["code"] == "consider"
    assert recommendation["risk"]["code"] == "moderate"
    assert recommendation["priority"] == 60.0
    assert recommendation["confidence_level"] == "silver"

    print_recommendation(
        "СЦЕНАРИЙ №1 — СРЕДНИЙ СИГНАЛ",
        recommendation,
    )


# ------------------------------------------------------------
# Сценарий №2: слабая статистика
# ------------------------------------------------------------

def test_weak_recommendation() -> None:
    """
    Проверяем сигнал с недостаточной статистикой.
    """

    passport = create_test_passport(
        signal_score=18,
        confidence=22,
        country_total=8,
        country_roi=-4.0,
        league_total=6,
        league_roi=-8.0,
        match_type_total=9,
        match_type_roi=1.0,
        confidence_level="insufficient",
    )

    recommendation = build_recommendation(passport)

    assert recommendation["action"]["code"] == "skip"
    assert recommendation["risk"]["code"] == "very_high"
    assert recommendation["priority"] == 19.6
    assert (
        recommendation["confidence_level"]
        == "insufficient"
    )

    print_recommendation(
        "СЦЕНАРИЙ №2 — СЛАБЫЙ СИГНАЛ",
        recommendation,
    )


# ------------------------------------------------------------
# Сценарий №3: сильная статистика
# ------------------------------------------------------------

def test_strong_recommendation() -> None:
    """
    Проверяем сигнал с высокой исторической оценкой
    и высокой надёжностью статистики.
    """

    passport = create_test_passport(
        signal_score=91,
        confidence=92,
        country_total=500,
        country_roi=18.0,
        league_total=320,
        league_roi=14.0,
        match_type_total=700,
        match_type_roi=11.0,
        confidence_level="gold",
    )

    recommendation = build_recommendation(passport)

    assert recommendation["action"]["code"] == "priority"
    assert recommendation["risk"]["code"] == "reduced"
    assert recommendation["priority"] == 91.4
    assert recommendation["confidence_level"] == "gold"

    print_recommendation(
        "СЦЕНАРИЙ №3 — СИЛЬНЫЙ СИГНАЛ",
        recommendation,
    )


# ------------------------------------------------------------
# Запуск всех тестов
# ------------------------------------------------------------

def main() -> None:
    """
    Последовательно запускает все тестовые сценарии.
    """

    test_medium_recommendation()
    test_weak_recommendation()
    test_strong_recommendation()

    print()
    print("=" * 70)
    print("✅ ВСЕ ПРОВЕРКИ RECOMMENDATION ENGINE ПРОЙДЕНЫ")
    print("=" * 70)


if __name__ == "__main__":
    main()