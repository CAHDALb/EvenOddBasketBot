"""
===========================================================
EvenOddBasketBot

Файл:
scripts/check_postgres_statistics.py

Назначение:
Показывает краткую статистику по базе PostgreSQL Neon.
===========================================================
"""

import os
import sys

# Добавляем корень проекта в пути Python,
# чтобы скрипт видел postgres_database.py
PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from postgres_database import get_connection


def print_postgres_statistics():
    """
    Выводит общую статистику PostgreSQL.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:

            # Всего сигналов
            cursor.execute(
                "SELECT COUNT(*) FROM signals"
            )
            total = cursor.fetchone()[0]

            # Ожидают результата
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM signals
                WHERE status = 'waiting'
                """
            )
            waiting = cursor.fetchone()[0]

            # Завершённые сигналы
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM signals
                WHERE status = 'finished'
                """
            )
            finished = cursor.fetchone()[0]

            # WIN
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM signals
                WHERE result = 'win'
                """
            )
            wins = cursor.fetchone()[0]

            # LOSE
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM signals
                WHERE result = 'lose'
                """
            )
            loses = cursor.fetchone()[0]

            # Суммарный ROI
            cursor.execute(
                """
                SELECT COALESCE(SUM(roi), 0)
                FROM signals
                """
            )
            roi = cursor.fetchone()[0]

    # Проходимость считаем только по завершённым ставкам
    completed_results = wins + loses

    if completed_results > 0:
        win_rate = wins / completed_results * 100
    else:
        win_rate = 0

    print("=" * 50)
    print("PostgreSQL Neon — статистика")
    print("=" * 50)
    print(f"Всего сигналов : {total}")
    print(f"Ожидают        : {waiting}")
    print(f"Завершено      : {finished}")
    print(f"WIN            : {wins}")
    print(f"LOSE           : {loses}")
    print(f"Проходимость   : {win_rate:.2f}%")
    print(f"ROI            : {roi:+.2f}")
    print("=" * 50)


if __name__ == "__main__":
    print_postgres_statistics()