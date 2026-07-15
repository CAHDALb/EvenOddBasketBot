"""
===========================================================
EvenOddBasketBot

Файл:
analytics.py

Назначение:
Собирает аналитическую информацию по сигналу.

Пока модуль:
- получает статистику по стране;
- получает статистику по лиге;
- получает статистику по типу матча;
- формирует паспорт сигнала.

В будущем:
- оценка уверенности;
- фильтрация слабых сигналов;
- Decision Engine.
===========================================================
"""

from postgres_database import get_connection
from match_classifier import detect_match_type


def get_group_statistics(field_name, field_value):
    """
    Возвращает статистику по одному значению поля.

    Например:
    get_group_statistics("country", "Мир")
    get_group_statistics("league", "МИР: World Championship U17 Women")
    get_group_statistics("match_type", "youth")
    """

    # Разрешаем использовать только известные поля.
    # Это защищает SQL-запрос от неправильных значений.
    allowed_fields = {
        "country",
        "league",
        "match_type",
    }

    if field_name not in allowed_fields:
        raise ValueError(
            f"Недопустимое поле статистики: {field_name}"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN result = 'lose' THEN 1 ELSE 0 END) AS loses,
            COALESCE(SUM(roi), 0) AS roi
        FROM signals
        WHERE status = 'finished'
          AND {field_name} = %s
        """,
        (field_value,),
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    total = row[0] or 0
    wins = row[1] or 0
    loses = row[2] or 0
    roi = float(row[3] or 0)

    finished = wins + loses

    if finished > 0:
        win_rate = wins / finished * 100
    else:
        win_rate = 0

    return {
        "value": field_value,
        "total": total,
        "wins": wins,
        "loses": loses,
        "finished": finished,
        "win_rate": win_rate,
        "roi": roi,
    }


def get_country_info(country):
    """
    Возвращает статистику по стране.
    """

    return get_group_statistics(
        field_name="country",
        field_value=country,
    )


def get_league_info(league):
    """
    Возвращает статистику по лиге.
    """

    return get_group_statistics(
        field_name="league",
        field_value=league,
    )


def get_match_type_info(match_type):
    """
    Возвращает статистику по типу матча.
    """

    return get_group_statistics(
        field_name="match_type",
        field_value=match_type,
    )


def build_signal_passport(match):
    """
    Формирует аналитический паспорт нового сигнала.
    """

    country = match.get("country") or "Неизвестная страна"
    league = match.get("league") or "Неизвестная лига"
    match_type = detect_match_type(match)

    return {
        "country": get_country_info(country),
        "league": get_league_info(league),
        "match_type": get_match_type_info(match_type),
    }

def get_last_results(limit=10):
    """
    Возвращает последние завершённые результаты стратегии.

    Самый свежий результат находится первым.

    Пример:
    ["win", "lose", "win"]
    """

    if limit <= 0:
        return []

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT result
                FROM signals
                WHERE status = 'finished'
                  AND result IN ('win', 'lose')
                ORDER BY signal_datetime DESC
                LIMIT %s
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    return [row[0] for row in rows]


def get_current_streak(results=None):
    """
    Определяет текущую серию WIN или LOSE.

    Важно:
    список должен начинаться с самого свежего результата.

    Возвращает, например:

    {
        "result": "win",
        "length": 3
    }
    """

    if results is None:
        results = get_last_results(limit=100)

    if not results:
        return {
            "result": None,
            "length": 0,
        }

    current_result = results[0]
    streak_length = 0

    for result in results:
        if result == current_result:
            streak_length += 1
        else:
            break

    return {
        "result": current_result,
        "length": streak_length,
    }


def get_recent_statistics(limit=10):
    """
    Считает статистику последних завершённых сигналов.

    Возвращает:
    - список результатов;
    - количество WIN;
    - количество LOSE;
    - проходимость;
    - текущую серию;
    - строку с цветными значками.
    """

    results = get_last_results(limit=limit)

    wins = results.count("win")
    loses = results.count("lose")
    total = len(results)

    if total > 0:
        win_rate = wins / total * 100
    else:
        win_rate = 0

    streak = get_current_streak(results)

    result_icons = {
        "win": "🟢",
        "lose": "🔴",
    }

    # В базе результаты идут от новых к старым.
    # Для Telegram разворачиваем их:
    # слева старые, справа самый свежий.
    history_line = "".join(
        result_icons.get(result, "⚪")
        for result in reversed(results)
    )

    return {
        "limit": limit,
        "results": results,
        "total": total,
        "wins": wins,
        "loses": loses,
        "win_rate": win_rate,
        "streak": streak,
        "history_line": history_line,
    }


def get_risk_indicator(recent_statistics=None):
    """
    Возвращает информационный индикатор осторожности.

    Индикатор не является рекомендацией по размеру ставки
    и не гарантирует результат следующего сигнала.
    """

    if recent_statistics is None:
        recent_statistics = get_recent_statistics(limit=10)

    total = recent_statistics["total"]
    wins = recent_statistics["wins"]

    # Пока нет даже десяти завершённых сигналов
    if total < 10:
        return {
            "level": "high_uncertainty",
            "icon": "⚪",
            "title": "Недостаточно данных",
            "message": (
                f"Завершённых сигналов: {total} из 10. "
                "История пока слишком короткая для оценки текущей формы."
            ),
        }

    # От 0 до 4 побед из последних 10
    if wins <= 4:
        return {
            "level": "caution",
            "icon": "🔴",
            "title": "Повышенная осторожность",
            "message": (
                f"Последние результаты: {wins} WIN из 10. "
                "Текущая серия стратегии выглядит слабой."
            ),
        }

    # Ровно 5 побед из последних 10
    if wins == 5:
        return {
            "level": "neutral",
            "icon": "🟡",
            "title": "Нейтральная форма",
            "message": (
                "Последние результаты: 5 WIN из 10. "
                "Явного преимущества текущая серия не показывает."
            ),
        }

    # 6 побед из последних 10
    if wins == 6:
        return {
            "level": "positive_caution",
            "icon": "🟡",
            "title": "Умеренно положительная форма",
            "message": (
                "Последние результаты: 6 WIN из 10. "
                "Форма положительная, но выборка остаётся небольшой."
            ),
        }

    # 7–10 побед из последних 10
    return {
        "level": "positive",
        "icon": "🟢",
        "title": "Положительная текущая форма",
        "message": (
            f"Последние результаты: {wins} WIN из 10. "
            "Это хорошая короткая серия, но не гарантия следующего WIN."
        ),
    }

def calculate_confidence(passport):
    """
    Пока возвращает None.

    Реальную оценку уверенности добавим,
    когда накопится достаточная статистика.
    """

    return None


def should_send_signal(passport):
    """
    Пока все сигналы разрешены.

    Позже здесь появится фильтрация
    на основе накопленной статистики.
    """

    return True