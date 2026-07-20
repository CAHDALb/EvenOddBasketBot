"""
Ручная проверка Signal Passport Builder.

Файл можно запускать непосредственно из PyCharm.
"""

from pprint import pprint

from intelligence.passport_builder import (
    build_signal_passport,
    validate_signal_passport,
)


def main() -> None:
    """
    Создаём тестовый паспорт и проверяем его структуру.
    """

    passport = build_signal_passport(
        country_stats={
            "name": "Израиль",

            # Эти поля нужны Signal Score
            "total": 60,
            "roi": 12.0,

            # Эти поля оставляем для отображения статистики
            "wins": 39,
            "losses": 21,
            "win_rate": 65.0,
        },
        league_stats={
            "name": "Национальная лига",

            # Эти поля нужны Signal Score
            "total": 40,
            "roi": 8.0,

            # Дополнительная статистика
            "wins": 28,
            "losses": 12,
            "win_rate": 70.0,
        },
        match_type_stats={
            "name": "Мужчины",

            # Эти поля нужны Signal Score
            "total": 80,
            "roi": 7.0,

            # Дополнительная статистика
            "wins": 51,
            "losses": 29,
            "win_rate": 63.75,
        },
        # recommendation="Сигнал имеет повышенный исторический приоритет.",
        history={
            "recent_results": [
                "WIN",
                "WIN",
                "LOSE",
                "WIN",
                "WIN",
            ],
            "current_streak": 2,
        },

        history_results=[
            "WIN",
            "WIN",
            "LOSE",
            "WIN",
            "WIN",
        ],

        match_data={
            "match_id": "04ugyK9b",
            "home_team": "Галиль Элион",
            "away_team": "Нетания",
            "q1_total": 48,
            "q2_total": 42,
            "q3_total": 40,
        },
    )

    print("=" * 70)
    print("SIGNAL PASSPORT")
    print("=" * 70)

    pprint(passport, sort_dicts=False)

    print()
    print("=" * 70)
    print("ПРОВЕРКА ПАСПОРТА")
    print("=" * 70)

    is_valid, errors = validate_signal_passport(passport)

    if is_valid:
        print("✅ Signal Passport успешно прошёл проверку.")
    else:
        print("❌ В Signal Passport найдены ошибки:")

        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    main()