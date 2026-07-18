import json
import os
from datetime import datetime

DB_FILE = "signals.json"


# Создает файл, если его нет
def init_database():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)


# Загружает все сигналы
def load_signals():
    init_database()

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Сохраняет список сигналов
def save_signals(signals):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(signals, f, ensure_ascii=False, indent=4)


# Проверяет, есть ли уже такой матч
def signal_exists(match_id):
    signals = load_signals()

    for signal in signals:
        if signal["id"] == match_id:
            return True

    return False


# Добавляет новый сигнал
def add_signal(match):
    """
    Добавляет новый сигнал в signals.json.
    Если такой матч уже есть, второй раз его не записывает.
    """

    # Загружаем все сохранённые сигналы
    signals = load_signals()

    # Берём ID матча из нового формата parser.py
    match_id = match["id"]

    # Проверяем дубликат
    if signal_exists(match_id):
        return False

    # Создаём запись сигнала
    signal = {
        "id": match_id,
        "match_url": match["match_url"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "country": match.get("country"),
        "league": match.get("league"),

        "home": match.get("home_name"),
        "away": match.get("away_name"),

        "q1": match.get("q1_total"),
        "q2": match.get("q2_total"),
        "q3": match.get("q3_total"),

        "signal_stage": "Q4",
        "prediction": "odd",

        "status": "waiting",
        "final_total": None,
        "result": None,
        "roi": None
    }

    # Добавляем новый сигнал в список
    signals.append(signal)

    # Сохраняем обновлённый список
    save_signals(signals)

    return True