"""
===========================================================
EvenOddBasketBot

Файл:
database.py

Назначение:
Единая точка работы с базами данных.

Во время миграции:
- SQLite остаётся резервной базой;
- PostgreSQL Neon является постоянной базой.
===========================================================
"""

from sqlite_database import (
    add_signal as sqlite_add_signal,
    get_waiting_signals as sqlite_get_waiting_signals,
    update_signal_result as sqlite_update_signal_result,
)

from postgres_database import (
    add_signal as postgres_add_signal,
    get_waiting_signals as postgres_get_waiting_signals,
    update_signal_result as postgres_update_signal_result,
)


def add_signal(match):
    """
    Сохраняет новый сигнал одновременно
    в SQLite и PostgreSQL.

    Ошибка одной базы не должна остановить бота.
    """

    sqlite_result = False
    postgres_result = False

    # Показывают, удалось ли нормально обратиться к базе.
    # Дубликат сигнала тоже считается успешной операцией:
    # база работает, а запись уже сохранена.
    sqlite_available = False
    postgres_available = False

    # =====================================================
    # Сохраняем резервную копию в SQLite
    # =====================================================
    try:
        sqlite_result = sqlite_add_signal(match)
        sqlite_available = True

        if sqlite_result:
            print("Сигнал сохранён в SQLite.")
        else:
            print("Сигнал уже существует в SQLite.")

    except Exception as error:
        print("Ошибка записи сигнала в SQLite:", error)

    # =====================================================
    # Сохраняем постоянную копию в PostgreSQL
    # =====================================================
    try:
        postgres_result = postgres_add_signal(match)
        postgres_available = True

        if postgres_result:
            print("Сигнал сохранён в PostgreSQL.")
        else:
            print("Сигнал уже существует в PostgreSQL.")

    except Exception as error:
        print("Ошибка записи сигнала в PostgreSQL:", error)

    # True означает, что хотя бы одна база успешно обработала запрос.
    # Это может быть как новая запись, так и уже существующий сигнал.
    return sqlite_available or postgres_available


def get_waiting_signals():
    """
    Получает ожидающие сигналы из PostgreSQL.

    PostgreSQL теперь является основным источником данных.
    SQLite пока остаётся резервной копией.
    """

    try:
        return postgres_get_waiting_signals()

    except Exception as error:
        print(
            "Ошибка чтения waiting-сигналов из PostgreSQL:",
            error
        )

        print("Переходим на резервную SQLite.")

        return sqlite_get_waiting_signals()


def update_signal_result(match_id, final_total, result, roi):
    """
    Обновляет результат сигнала одновременно
    в SQLite и PostgreSQL.
    """

    sqlite_result = False
    postgres_result = False

    # =====================================================
    # Обновляем резервную SQLite
    # =====================================================
    try:
        sqlite_update_signal_result(
            match_id=match_id,
            final_total=final_total,
            result=result,
            roi=roi,
        )

        sqlite_result = True
        print("Результат обновлён в SQLite.")

    except Exception as error:
        print("Ошибка обновления результата в SQLite:", error)

    # =====================================================
    # Обновляем постоянную PostgreSQL
    # =====================================================
    try:
        postgres_result = postgres_update_signal_result(
            match_id=match_id,
            final_total=final_total,
            result=result,
            roi=roi,
        )

        if postgres_result:
            print("Результат обновлён в PostgreSQL.")
        else:
            print(
                "Сигнал не найден в PostgreSQL:",
                match_id,
            )

    except Exception as error:
        print("Ошибка обновления результата в PostgreSQL:", error)

    return sqlite_result or postgres_result