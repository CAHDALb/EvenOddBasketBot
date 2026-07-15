import os
import sys

PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from postgres_database import get_connection


TEST_ID = "POSTGRES_TEST_001"


with get_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM signals
            WHERE id = %s
            """,
            (TEST_ID,)
        )

        deleted_rows = cursor.rowcount


if deleted_rows > 0:
    print("Тестовый сигнал удалён из PostgreSQL.")
else:
    print("Тестовый сигнал в PostgreSQL не найден.")