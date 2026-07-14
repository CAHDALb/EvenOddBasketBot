"""
===========================================================
EvenOddBasketBot

Файл:
postgres_database.py

Назначение:
Подключение к постоянной PostgreSQL-базе Neon.
Пока используется отдельно от рабочего SQLite.
===========================================================
"""

import os

import psycopg
from dotenv import load_dotenv
from match_classifier import detect_match_type

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """
    Создаёт подключение к PostgreSQL.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "Переменная DATABASE_URL не найдена в .env"
        )

    return psycopg.connect(DATABASE_URL)


def create_tables():
    """
    Создаёт таблицу signals в PostgreSQL,
    если она ещё не существует.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id TEXT PRIMARY KEY,

                    strategy TEXT,
                    match_type TEXT,

                    country TEXT,
                    league TEXT,

                    home TEXT,
                    away TEXT,

                    signal_datetime TIMESTAMPTZ DEFAULT NOW(),
                    weekday TEXT,
                    hour INTEGER,

                    q1 INTEGER,
                    q2 INTEGER,
                    q3 INTEGER,

                    prediction TEXT,
                    status TEXT,

                    final_total INTEGER,
                    result TEXT,
                    roi DOUBLE PRECISION,

                    match_url TEXT
                )
                """
            )

    print("Таблица PostgreSQL создана или уже существует.")

def add_signal(match):
    """
    Сохраняет новый сигнал в PostgreSQL.

    Если матч с таким ID уже существует,
    повторно его не добавляет.

    Возвращает:
    True  — сигнал добавлен;
    False — такой сигнал уже был в базе.
    """

    match_id = match["id"]

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Проверяем, есть ли такой матч в PostgreSQL
            cursor.execute(
                """
                SELECT 1
                FROM signals
                WHERE id = %s
                """,
                (match_id,)
            )

            if cursor.fetchone() is not None:
                return False

            # Сохраняем новый сигнал
            cursor.execute(
                """
                INSERT INTO signals (
                    id,
                    strategy,
                    match_type,
                    country,
                    league,
                    home,
                    away,
                    signal_datetime,
                    weekday,
                    hour,
                    q1,
                    q2,
                    q3,
                    prediction,
                    status,
                    final_total,
                    result,
                    roi,
                    match_url
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, NOW(), %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                """,
                (
                    match_id,
                    "odd_total",
                    detect_match_type(match),
                    match.get("country"),
                    match.get("league"),
                    match.get("home_name"),
                    match.get("away_name"),
                    None,
                    None,
                    match.get("q1_total"),
                    match.get("q2_total"),
                    match.get("q3_total"),
                    "odd",
                    "waiting",
                    None,
                    None,
                    None,
                    match.get("match_url"),
                )
            )

    return True

def test_connection():
    """
    Проверяет подключение к Neon.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]

    print("Подключение к PostgreSQL успешно.")
    print("Версия сервера:", version)


if __name__ == "__main__":
    test_connection()
    create_tables()