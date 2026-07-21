"""
===========================================================
EvenOddBasketBot

Файл:
notifications.py

Назначение:
Создание фирменных служебных сообщений Telegram.
===========================================================
"""

from branding import BRAND_NAME, DISCLAIMER_SHORT
from config import CHECK_INTERVAL
from constants import STATUS_WIN


def create_start_message():
    """Создаёт сообщение администратору о запуске сервиса."""

    return (
        f"✅ {BRAND_NAME} запущен на сервере\n\n"
        "🏀 Проверка LIVE-матчей активна.\n"
        f"⏱ Интервал проверки: {CHECK_INTERVAL} секунд.\n"
        "🎨 Фирменный профиль и меню загружены."
    )


def create_error_message(error):
    """Создаёт сообщение администратору об ошибке парсинга."""

    return (
        f"⚠️ {BRAND_NAME} • СИСТЕМНАЯ ОШИБКА\n\n"
        "Не удалось получить матчи с Flashscore.\n\n"
        f"Ошибка:\n{error}"
    )


def create_result_message(signal):
    """Создаёт фирменное сообщение после окончания матча."""

    result_icon = "✅" if signal["result"] == STATUS_WIN else "❌"

    return (
        f"🏀 {BRAND_NAME.upper()} • РЕЗУЛЬТАТ\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏀 {signal['home']} — {signal['away']}\n\n"
        f"📊 Итоговый тотал: {signal['final_total']}\n"
        "🎯 Прогноз: НЕЧЁТ\n\n"
        f"{result_icon} Результат: {signal['result'].upper()}\n"
        f"💰 ROI: {signal['roi']:+.2f}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{DISCLAIMER_SHORT}"
    )
