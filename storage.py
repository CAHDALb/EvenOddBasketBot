import json
from pathlib import Path

# Путь к файлу с сохранёнными ID
FILE_PATH = Path("data/sent_matches.json")


def load_sent_matches():
    """
    Загружает список уже отправленных матчей.
    """

    if not FILE_PATH.exists():
        return set()

    with open(FILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return set(data)


def save_sent_matches(matches):
    """
    Сохраняет список отправленных матчей.
    """

    with open(FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(
            list(matches),
            file,
            ensure_ascii=False,
            indent=4
        )