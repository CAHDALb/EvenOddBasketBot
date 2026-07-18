import json
import os
import sqlite3


PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

JSON_PATH = os.path.join(PROJECT_DIR, "signals.json")
SQLITE_PATH = os.path.join(PROJECT_DIR, "evenodd.db")


def check_json():
    print("=" * 60)
    print("signals.json")
    print("=" * 60)

    if not os.path.exists(JSON_PATH):
        print("Файл не найден.")
        return

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as file:
            signals = json.load(file)

        print("Количество записей:", len(signals))

        if signals:
            print("Первая запись:")
            print(signals[0])

    except Exception as error:
        print("Ошибка чтения JSON:", error)


def check_sqlite():
    print("=" * 60)
    print("evenodd.db")
    print("=" * 60)

    if not os.path.exists(SQLITE_PATH):
        print("Файл не найден.")
        return

    try:
        connection = sqlite3.connect(SQLITE_PATH)
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        )

        tables = [row[0] for row in cursor.fetchall()]

        print("Таблицы:", tables)

        if "signals" in tables:
            cursor.execute("SELECT COUNT(*) FROM signals")
            total = cursor.fetchone()[0]

            print("Количество записей в signals:", total)

            cursor.execute(
                """
                SELECT *
                FROM signals
                LIMIT 1
                """
            )

            row = cursor.fetchone()

            cursor.execute("PRAGMA table_info(signals)")
            columns = [column[1] for column in cursor.fetchall()]

            if row:
                print("Первая запись:")
                print(dict(zip(columns, row)))

        connection.close()

    except Exception as error:
        print("Ошибка чтения SQLite:", error)


if __name__ == "__main__":
    check_json()
    check_sqlite()