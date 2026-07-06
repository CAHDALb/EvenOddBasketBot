"""
===========================================================
EvenOddBasketBot

Файл:
results.py

Назначение:
Проверяет сохранённые сигналы после окончания матча.
Определяет WIN / LOSE и обновляет signals.json.

Версия:
0.4
===========================================================
"""

from database import load_signals, save_signals
from parser import get_match_by_id
from constants import STATUS_WAITING, STATUS_WIN, STATUS_LOSE, PREDICTION_ODD
from notifications import create_result_message
from telegram_sender import send_telegram

def check_signal_result(signal):
    """
    Проверяет один сигнал.
    """

    match_id = signal["id"]

    print("=" * 60)
    print("Проверяем сигнал:", match_id)
    print("Матч:", signal["home"], "-", signal["away"])

    match = get_match_by_id(match_id)

    if match is None:
        print("Матч не найден в текущем feed")
        return signal

    print("Матч найден")
    print("finished:", match["finished"])
    print("home_score:", match["home_score"])
    print("away_score:", match["away_score"])

    if not match["finished"]:
        print("Матч ещё не завершён")
        return signal

    final_total = match["home_score"] + match["away_score"]

    print("Итоговый тотал:", final_total)

    # =========================================================
    # Считаем итоговый тотал матча
    # =========================================================
    final_total = match["home_score"] + match["away_score"]

    # Записываем итоговый тотал в сигнал
    signal["final_total"] = final_total

    # =========================================================
    # Проверяем результат стратегии
    #
    # Правило:
    # если общий тотал матча нечётный — WIN
    # если общий тотал матча чётный — LOSE
    # =========================================================
    if final_total % 2 == 1:
        signal["result"] = STATUS_WIN
        signal["roi"] = 0.9
    else:
        signal["result"] = STATUS_LOSE
        signal["roi"] = -1

    # Матч больше не ждём
    signal["status"] = "finished"

    message = create_result_message(signal)
    send_telegram(message)

    print("Результат отправлен в Telegram")

    return signal


def check_all_waiting_signals():
    """
    Проверяет все сигналы со статусом waiting.
    """

    # Загружаем все сигналы из signals.json
    signals = load_signals()

    # Новый список, куда будем складывать обновлённые сигналы
    updated_signals = []

    # Проверяем каждый сигнал
    for signal in signals:

        # Если сигнал ещё ждёт результата — проверяем
        if signal["status"] == STATUS_WAITING:
            signal = check_signal_result(signal)

        # Добавляем сигнал в обновлённый список
        updated_signals.append(signal)

    # Сохраняем обновлённую базу
    save_signals(updated_signals)