import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from postgres_database import get_connection


TEST_ID = "POSTGRES_TEST_001"


with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                id,
                country,
                league,
                home,
                away,
                match_type,
                q1,
                q2,
                q3,
                status
            FROM signals
            WHERE id = %s
            """,
            (TEST_ID,)
        )

        signal = cursor.fetchone()


if signal is None:
    print("Тестовый сигнал не найден.")
else:
    print("Сигнал найден в PostgreSQL:")
    print("ID          :", signal[0])
    print("Страна      :", signal[1])
    print("Лига        :", signal[2])
    print("Команды     :", signal[3], "-", signal[4])
    print("Тип матча   :", signal[5])
    print("Q1          :", signal[6])
    print("Q2          :", signal[7])
    print("Q3          :", signal[8])
    print("Статус      :", signal[9])