"""
===========================================================
EvenOddBasketBot

Файл:
statistics.py

Назначение:
Считает общую статистику по сигналам из SQLite.

Версия:
0.8
===========================================================
"""

from postgres_database import get_connection


def get_total_statistics():
    """
    Возвращает общую статистику проекта.

    Считает:
    - всего сигналов;
    - ожидающих результатов;
    - WIN;
    - LOSE;
    - проходимость;
    - суммарный ROI.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # Всего сигналов
    cursor.execute("SELECT COUNT(*) FROM signals")
    total = cursor.fetchone()[0]

    # Ожидают результата
    cursor.execute(
        "SELECT COUNT(*) FROM signals WHERE status = 'waiting'"
    )
    waiting = cursor.fetchone()[0]

    # Победы
    cursor.execute(
        "SELECT COUNT(*) FROM signals WHERE result = 'win'"
    )
    wins = cursor.fetchone()[0]

    # Поражения
    cursor.execute(
        "SELECT COUNT(*) FROM signals WHERE result = 'lose'"
    )
    loses = cursor.fetchone()[0]

    # Суммарный ROI в условных единицах
    cursor.execute(
        "SELECT COALESCE(SUM(roi), 0) FROM signals"
    )
    roi = cursor.fetchone()[0]

    connection.close()

    # Проходимость считаем только по завершённым ставкам
    finished = wins + loses

    if finished > 0:
        win_rate = wins / finished * 100
    else:
        win_rate = 0

    return {
        "total": total,
        "waiting": waiting,
        "wins": wins,
        "loses": loses,
        "finished": finished,
        "win_rate": win_rate,
        "roi": roi,
    }

def get_country_statistics():
    """
    Возвращает статистику по странам.

    Для каждой страны считает:
    - количество завершённых сигналов;
    - WIN;
    - LOSE;
    - процент прохода;
    - суммарный ROI.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            country,
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'lose' THEN 1 ELSE 0 END) AS loses,
            COALESCE(SUM(roi), 0) AS roi
        FROM signals
        WHERE status = 'finished'
        GROUP BY country
        ORDER BY total DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    statistics = []

    for country, total, wins, loses, roi in rows:

        # Защита на случай пустого названия страны
        country_name = country or "Неизвестная страна"

        # Процент прохода
        if total > 0:
            win_rate = wins / total * 100
        else:
            win_rate = 0

        statistics.append({
            "country": country_name,
            "total": total,
            "wins": wins,
            "loses": loses,
            "win_rate": win_rate,
            "roi": roi,
        })

    return statistics

def get_league_statistics():
    """
    Возвращает статистику по лигам.

    Для каждой лиги считает:
    - количество завершённых сигналов;
    - WIN;
    - LOSE;
    - процент прохода;
    - суммарный ROI.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            league,
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'lose' THEN 1 ELSE 0 END) AS loses,
            COALESCE(SUM(roi), 0) AS roi
        FROM signals
        WHERE status = 'finished'
        GROUP BY league
        ORDER BY total DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    statistics = []

    for league, total, wins, loses, roi in rows:

        # Если название лиги отсутствует
        league_name = league or "Неизвестная лига"

        # Проходимость
        if total > 0:
            win_rate = wins / total * 100
        else:
            win_rate = 0

        statistics.append(
            {
                "league": league_name,
                "total": total,
                "wins": wins,
                "loses": loses,
                "win_rate": win_rate,
                "roi": roi,
            }
        )

    return statistics

def print_total_statistics():
    """
    Красиво выводит общую статистику в консоль.
    """

    stats = get_total_statistics()

    print("=" * 50)
    print("🏀 EvenOddBasketBot — статистика")
    print("=" * 50)
    print(f"Всего сигналов : {stats['total']}")
    print(f"Ожидают        : {stats['waiting']}")
    print(f"WIN            : {stats['wins']}")
    print(f"LOSE           : {stats['loses']}")
    print(f"Проходимость   : {stats['win_rate']:.2f}%")
    print(f"ROI            : {stats['roi']:+.2f}")
    print("=" * 50)

def print_country_statistics():
    """
    Красиво выводит статистику по странам в консоль.
    """

    countries = get_country_statistics()

    print("=" * 55)
    print("🌍 EvenOddBasketBot — статистика по странам")
    print("=" * 55)

    if not countries:
        print("Пока нет завершённых сигналов.")
        print("=" * 55)
        return

    for item in countries:
        print(f"Страна         : {item['country']}")
        print(f"Сигналов       : {item['total']}")
        print(f"WIN            : {item['wins']}")
        print(f"LOSE           : {item['loses']}")
        print(f"Проходимость   : {item['win_rate']:.2f}%")
        print(f"ROI            : {item['roi']:+.2f}")
        print("-" * 55)

    print("=" * 55)

def print_league_statistics():
    """
    Красиво выводит статистику по лигам.
    """

    leagues = get_league_statistics()

    print("=" * 55)
    print("🏆 EvenOddBasketBot — статистика по лигам")
    print("=" * 55)

    if not leagues:
        print("Пока нет завершённых сигналов.")
        print("=" * 55)
        return

    for item in leagues:

        print(f"Лига          : {item['league']}")
        print(f"Сигналов      : {item['total']}")
        print(f"WIN           : {item['wins']}")
        print(f"LOSE          : {item['loses']}")
        print(f"Проходимость  : {item['win_rate']:.2f}%")
        print(f"ROI           : {item['roi']:+.2f}")

        print("-" * 55)

    print("=" * 55)

def get_match_type_statistics():
    """
    Возвращает статистику по типам матчей:
    men, women и youth.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            match_type,
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'lose' THEN 1 ELSE 0 END) AS loses,
            COALESCE(SUM(roi), 0) AS roi
        FROM signals
        WHERE status = 'finished'
        GROUP BY match_type
        ORDER BY total DESC
        """
    )

    rows = cursor.fetchall()
    connection.close()

    result = []

    for match_type, total, wins, loses, roi in rows:
        wins = wins or 0
        loses = loses or 0
        finished = wins + loses

        win_rate = (
            wins / finished * 100
            if finished > 0
            else 0
        )

        result.append(
            {
                "match_type": match_type or "unknown",
                "total": total,
                "wins": wins,
                "loses": loses,
                "win_rate": win_rate,
                "roi": roi,
            }
        )

    return result
def print_match_type_statistics():
    """
    Красиво выводит статистику по типам матчей.
    """

    type_names = {
        "men": "👨 Мужские",
        "women": "👩 Женские",
        "youth": "👦 Молодёжные",
        "unknown": "❓ Не определено",
    }

    items = get_match_type_statistics()

    print("=" * 55)
    print("🏀 EvenOddBasketBot — статистика по типам")
    print("=" * 55)

    if not items:
        print("Пока нет завершённых сигналов.")
        print("=" * 55)
        return

    for item in items:
        name = type_names.get(
            item["match_type"],
            item["match_type"]
        )

        print(f"Категория      : {name}")
        print(f"Сигналов       : {item['total']}")
        print(f"WIN            : {item['wins']}")
        print(f"LOSE           : {item['loses']}")
        print(f"Проходимость   : {item['win_rate']:.2f}%")
        print(f"ROI            : {item['roi']:+.2f}")
        print("-" * 55)

    print("=" * 55)