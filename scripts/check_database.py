import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from sqlite_database import get_connection


connection = get_connection()
cursor = connection.cursor()

# Сколько всего сигналов находится в локальной базе
cursor.execute("SELECT COUNT(*) FROM signals")
total = cursor.fetchone()[0]

# Сколько сигналов уже имеют категорию
cursor.execute(
    """
    SELECT match_type, COUNT(*)
    FROM signals
    GROUP BY match_type
    """
)

groups = cursor.fetchall()

connection.close()

print("Всего сигналов в локальной базе:", total)
print("Распределение по категориям:")

for match_type, count in groups:
    print(match_type, ":", count)