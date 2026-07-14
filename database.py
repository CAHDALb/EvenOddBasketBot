"""
===========================================================
EvenOddBasketBot

Файл:
database.py

Назначение:
Единая точка сохранения сигналов.

Во время миграции сигнал записывается:
- в резервную SQLite;
- в постоянную PostgreSQL Neon.
===========================================================
"""

from sqlite_database import add_signal as sqlite_add_signal
from postgres_database import add_signal as postgres_add_signal


def add_signal(match):
    """
    Сохраняет сигнал одновременно в SQLite и PostgreSQL.

    Ошибка одной базы не должна останавливать бота.
    Возвращает True, если запись добавлена хотя бы в одну базу.
    """

    sqlite_result = False
    postgres_result = False

    # =====================================================
    # Резервная запись в SQLite
    # =====================================================
    try:
        sqlite_result = sqlite_add_signal(match)

        if sqlite_result:
            print("Сигнал сохранён в SQLite.")
        else:
            print("Сигнал уже существует в SQLite.")

    except Exception as error:
        print("Ошибка записи сигнала в SQLite:", error)

    # =====================================================
    # Постоянная запись в PostgreSQL Neon
    # =====================================================
    try:
        postgres_result = postgres_add_signal(match)

        if postgres_result:
            print("Сигнал сохранён в PostgreSQL.")
        else:
            print("Сигнал уже существует в PostgreSQL.")

    except Exception as error:
        print("Ошибка записи сигнала в PostgreSQL:", error)

    return sqlite_result or postgres_result