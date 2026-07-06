"""
===========================================================
EvenOddBasketBot

Файл:
notifications.py

Назначение:
Создание красивых сообщений Telegram.

Автор:
Александр Данилин

Версия:
0.5
===========================================================
"""

from constants import STATUS_WIN

def create_start_message():
    """
    Создаёт сообщение о запуске бота.
    """

    return (
        "✅ EvenOddBasketBot запущен на сервере\n\n"
        "🏀 Бот начал проверку LIVE-матчей.\n"
        "⏱ Интервал проверки: 180 секунд."
    )

def create_result_message(signal):
    """
    Создаёт красивое сообщение
    после окончания матча.
    """

    # Определяем смайлик результата
    if signal["result"] == STATUS_WIN:
        result_icon = "✅"
    else:
        result_icon = "❌"

    # Формируем сообщение
    message = (
        "🏁 РЕЗУЛЬТАТ СИГНАЛА\n\n"
        f"🏀 {signal['home']} - {signal['away']}\n\n"
        f"📊 Итоговый тотал: {signal['final_total']}\n\n"
        f"🎯 Прогноз: НЕЧЁТ\n\n"
        f"{result_icon} Результат: {signal['result'].upper()}\n\n"
        f"💰 ROI: {signal['roi']:+.2f}"
    )

    return message