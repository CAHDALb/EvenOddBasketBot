"""
===========================================================
EvenOddBasketBot

Файл:
sqlite_database.py

Назначение:
Работа с базой данных SQLite.

Этот файл будет хранить сигналы не в JSON,
а в настоящей базе данных evenodd.db.

Версия:
0.5
===========================================================
"""

import sqlite3

# Название файла базы данных
DB_NAME = "evenodd.db"


def get_connection():
    """
    Создаёт подключение к базе данных.

    Если файла evenodd.db ещё нет,
    SQLite создаст его автоматически.
    """

    connection = sqlite3.connect(DB_NAME)
    return connection


def create_tables():
    """
    Создаёт таблицу signals, если её ещё нет.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id TEXT PRIMARY KEY,

            strategy TEXT,

            country TEXT,
            league TEXT,

            home TEXT,
            away TEXT,

            signal_datetime TEXT,
            weekday TEXT,
            hour INTEGER,

            q1 INTEGER,
            q2 INTEGER,
            q3 INTEGER,

            prediction TEXT,

            status TEXT,

            final_total INTEGER,
            result TEXT,
            roi REAL,

            match_url TEXT
        )
    """)

    connection.commit()
    connection.close()

# =========================================================
# Проверяет, есть ли уже такой сигнал в базе
# =========================================================

def signal_exists(match_id):
    """
    Проверяет, есть ли матч с таким ID в базе данных.

    Возвращает:
    True  - если матч уже есть
    False - если матча ещё нет
    """

    # Если ID пустой, сразу считаем, что такого сигнала нет
    if match_id is None:
        return False

    # Подключаемся к базе данных
    connection = get_connection()
    cursor = connection.cursor()

    # Ищем матч с таким ID
    cursor.execute(
        "SELECT id FROM signals WHERE id = ?",
        (match_id,)
    )

    # Забираем одну найденную строку
    row = cursor.fetchone()

    # Закрываем соединение с базой
    connection.close()

    # Если row не None — матч найден
    return row is not None

# =========================================================
# Добавляет новый сигнал в SQLite
# =========================================================

def add_signal(match):
    """
    Сохраняет новый сигнал в базу SQLite.
    Если такой матч уже есть — второй раз не добавляет.
    """

    # Берём ID матча
    match_id = match["id"]

    # Если такой сигнал уже есть — выходим
    if signal_exists(match_id):
        return False

    # Подключаемся к базе
    connection = get_connection()
    cursor = connection.cursor()

    # Добавляем сигнал в таблицу
    cursor.execute(
        """
        INSERT INTO signals (
            id,
            strategy,
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
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            match_id,
            "odd_total",
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
            match.get("match_url")
        )
    )

    # Сохраняем изменения
    connection.commit()

    # Закрываем базу
    connection.close()

    return True

if __name__ == "__main__":
    create_tables()
    print("База данных создана.")