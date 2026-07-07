"""
===========================================================
EvenOddBasketBot

Файл:
results.py

Назначение:
Проверяет сигналы из SQLite после окончания матча.
Определяет WIN / LOSE и обновляет базу.

Версия:
0.7
===========================================================
"""

from parser import get_match_by_id
from constants import STATUS_WIN, STATUS_LOSE
from sqlite_database import get_waiting_signals, update_signal_result
from notifications import create_result_message
from telegram_sender import send_telegram


def check_signal_result(signal):
    """
    Проверяет один сигнал из SQLite.
    """

    match_id = signal["id"]

    print("=" * 60)
    print("Проверяем сигнал:", match_id)
    print("Матч:", signal["home_name"], "-", signal["away_name"])

    # Получаем свежие данные матча
    match = get_match_by_id(match_id)

    if match is None:
        print("Матч не найден в текущем feed")
        return

    if not match["finished"]:
        print("Матч ещё не завершён")
        return

    # =========================================================
    # Считаем итоговый тотал матча
    # =========================================================
    final_total = match["home_score"] + match["away_score"]

    print("Итоговый тотал:", final_total)

    # =========================================================
    # Правило стратегии:
    # нечётный общий тотал = WIN
    # чётный общий тотал = LOSE
    # =========================================================
    if final_total % 2 == 1:
        result = STATUS_WIN
        roi = 0.9
    else:
        result = STATUS_LOSE
        roi = -1

    # Обновляем результат в SQLite
    update_signal_result(
        match_id=match_id,
        final_total=final_total,
        result=result,
        roi=roi
    )

    # Готовим данные для сообщения
    signal_for_message = {
        "id": match_id,
        "home": signal["home_name"],
        "away": signal["away_name"],
        "final_total": final_total,
        "result": result,
        "roi": roi
    }

    # Отправляем результат в Telegram
    message = create_result_message(signal_for_message)
    send_telegram(message)

    print("Результат отправлен в Telegram")


def check_all_waiting_signals():
    """
    Проверяет все сигналы со статусом waiting из SQLite.
    """

    waiting_signals = get_waiting_signals()

    print("Ожидающих сигналов:", len(waiting_signals))

    for signal in waiting_signals:
        check_signal_result(signal)