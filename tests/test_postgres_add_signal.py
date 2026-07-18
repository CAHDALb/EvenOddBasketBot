import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from postgres_database import create_tables, add_signal


create_tables()

test_match = {
    "id": "POSTGRES_TEST_001",
    "country": "Тестовая страна",
    "league": "Тестовая лига U20",
    "home_name": "Команда А U20",
    "away_name": "Команда Б U20",
    "q1_total": 40,
    "q2_total": 42,
    "q3_total": 38,
    "match_url": "https://example.com/test",
}

result = add_signal(test_match)

print("Добавлено в PostgreSQL:", result)