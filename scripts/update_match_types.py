"""
===========================================================
EvenOddBasketBot

Файл:
scripts/update_match_types.py

Назначение:
Заполняет поле match_type у старых сигналов в SQLite.

Категории:
- men   — мужские матчи;
- women — женские матчи;
- youth — молодёжные матчи.
===========================================================
"""

import os
import sys

# Добавляем корневую папку проекта в пути Python,
# чтобы скрипт видел sqlite_database.py и match_classifier.py
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from match_classifier import detect_match_type
from sqlite_database import create_tables, get_connection


def update_old_match_types():
    """
    Находит записи с пустым match_type,
    определяет категорию матча и обновляет базу.
    """

    # Гарантируем, что таблица и колонка match_type существуют
    create_tables()

    connection = get_connection()
    cursor = connection.cursor()

    # Получаем только старые записи без категории
    cursor.execute(
        """
        SELECT
            id,
            country,
            league,
            home,
            away
        FROM signals
        WHERE match_type IS NULL
           OR TRIM(match_type) = ''
        """
    )

    rows = cursor.fetchall()

    print(f"Найдено записей без категории: {len(rows)}")

    updated = 0
    men_count = 0
    women_count = 0
    youth_count = 0

    for match_id, country, league, home, away in rows:

        # Формируем словарь в формате,
        # который понимает наш классификатор
        match = {
            "country": country,
            "league": league,
            "home_name": home,
            "away_name": away,
        }

        match_type = detect_match_type(match)

        cursor.execute(
            """
            UPDATE signals
            SET match_type = ?
            WHERE id = ?
            """,
            (match_type, match_id),
        )

        updated += 1

        if match_type == "men":
            men_count += 1
        elif match_type == "women":
            women_count += 1
        elif match_type == "youth":
            youth_count += 1

    connection.commit()
    connection.close()

    print("=" * 50)
    print("Миграция завершена.")
    print(f"Обновлено записей : {updated}")
    print(f"Мужские           : {men_count}")
    print(f"Женские           : {women_count}")
    print(f"Молодёжные        : {youth_count}")
    print("=" * 50)


if __name__ == "__main__":
    update_old_match_types()