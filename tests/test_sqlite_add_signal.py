from sqlite_database import create_tables, add_signal

create_tables()

test_match = {
    "id": "TEST123",
    "country": "Тестовая страна",
    "league": "Тестовая лига",
    "home_name": "Команда 1",
    "away_name": "Команда 2",
    "q1_total": 30,
    "q2_total": 40,
    "q3_total": 50,
    "match_url": "https://example.com"
}

result = add_signal(test_match)

print("Добавлено:", result)