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
import os
from match_classifier import detect_match_type
# ============================================================
# Путь к единственной базе данных проекта
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "evenodd.db")


def get_connection():
    """
    Создаёт подключение к базе данных.

    Если файла evenodd.db ещё нет,
    SQLite создаст его автоматически.
    """

    connection = sqlite3.connect(DB_NAME)
    return connection

def add_column_if_missing(cursor, table_name, column_name, column_type):
    """
    Добавляет новый столбец в существующую таблицу,
    только если такого столбца ещё нет.
    """

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN {column_name} {column_type}"
        )

def create_tables():
    """
    Создаёт таблицу signals, если её ещё нет.
    """

    # Подключаемся к базе данных
    connection = get_connection()
    cursor = connection.cursor()

    # Создаём таблицу signals
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

            signal_datetime TEXT,
            finished_datetime TEXT,
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
        """
    )

    # Если таблица была создана раньше,
    # добавляем новые столбцы без удаления старых данных.
    add_column_if_missing(
        cursor=cursor,
        table_name="signals",
        column_name="finished_datetime",
        column_type="TEXT"
    )

    # Добавляем тип матча для старых баз.
    add_column_if_missing(
        cursor=cursor,
        table_name="signals",
        column_name="match_type",
        column_type="TEXT"
    )

    # Сохраняем изменения
    connection.commit()

    # Закрываем соединение
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
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            match.get("match_url")
        )
    )


    # Сохраняем изменения
    connection.commit()

    # Закрываем базу
    connection.close()

    return True

# ============================================================
# Возвращает все сигналы со статусом waiting
# ============================================================

def get_waiting_signals():
    """
    Возвращает список сигналов,
    которые ещё не проверены.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            home,
            away,
            match_url,
            status
        FROM signals
        WHERE status = 'waiting'
    """)

    rows = cursor.fetchall()

    connection.close()

    signals = []

    for row in rows:

        signals.append({
            "id": row[0],
            "home_name": row[1],
            "away_name": row[2],
            "match_url": row[3],
            "status": row[4]
        })

    return signals

# ============================================================
# Обновляет результат сигнала
# ============================================================

def update_signal_result(match_id, final_total, result, roi):
    """
    Записывает результат проверки сигнала.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE signals
        SET
            final_total = ?,
            result = ?,
            roi = ?,
            status = 'finished',
            finished_datetime = COALESCE(finished_datetime, datetime('now'))
        WHERE id = ?
    """, (
        final_total,
        result,
        roi,
        match_id
    ))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("База данных создана.")