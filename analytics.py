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