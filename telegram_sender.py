"""
===========================================================
EvenOddBasketBot

Файл:
telegram_sender.py

Назначение:
- отправляет служебные сообщения администраторам;
- рассылает сигналы пользователям с учётом тарифа;
- ограничивает FREE двумя сигналами в сутки.
===========================================================
"""

import requests

from config import BOT_TOKEN
from telegram_users import (
    deactivate_user,
    get_admin_users,
    get_signal_recipients,
    mark_signal_sent,
)


def send_to_chat(chat_id, text, reply_markup=None):
    """Отправляет сообщение и при необходимости кнопочное меню."""

    if not BOT_TOKEN:
        return {
            "ok": False,
            "description": "BOT_TOKEN не найден.",
        }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        result = response.json()

        # Если пользователь заблокировал бота или чат недоступен,
        # временно исключаем его из будущих рассылок.
        if not result.get("ok") and response.status_code in (400, 403):
            try:
                deactivate_user(chat_id)
            except Exception as error:
                print("Не удалось отключить пользователя:", error)

        return result

    except requests.RequestException as error:
        return {
            "ok": False,
            "description": str(error),
        }


def send_telegram(text):
    """
    Отправляет служебное сообщение администраторам.

    Эта функция оставлена совместимой со старым кодом:
    сообщения о запуске, ошибках и результатах пока получают админы.
    """

    try:
        chat_ids = get_admin_users()
    except Exception as error:
        return {
            "ok": False,
            "description": f"Не удалось получить администраторов: {error}",
        }

    return _send_to_many(chat_ids, text)


def send_signal(text):
    """
    Отправляет новый сигнал всем разрешённым пользователям.

    FREE: не более двух сигналов в сутки.
    PREMIUM и ADMIN: все сигналы.
    """

    try:
        recipients = get_signal_recipients()
    except Exception as error:
        return {
            "ok": False,
            "description": f"Не удалось получить получателей: {error}",
            "sent": 0,
            "failed": 0,
        }

    sent = 0
    failed = 0
    last_result = {
        "ok": False,
        "description": "Нет зарегистрированных получателей.",
    }

    for recipient in recipients:
        telegram_id = recipient["telegram_id"]
        result = send_to_chat(telegram_id, text)
        last_result = result

        if result.get("ok"):
            sent += 1

            if recipient["tariff"] == "free":
                mark_signal_sent(telegram_id)
        else:
            failed += 1
            print(
                "Ошибка отправки пользователю",
                telegram_id,
                result,
            )

    return {
        "ok": sent > 0,
        "sent": sent,
        "failed": failed,
        "recipients": len(recipients),
        "last_result": last_result,
    }


def _send_to_many(chat_ids, text):
    """Общая отправка одного текста нескольким получателям."""

    sent = 0
    failed = 0
    last_result = {
        "ok": False,
        "description": "Нет получателей.",
    }

    for chat_id in chat_ids:
        result = send_to_chat(chat_id, text)
        last_result = result

        if result.get("ok"):
            sent += 1
        else:
            failed += 1

    return {
        "ok": sent > 0,
        "sent": sent,
        "failed": failed,
        "recipients": len(chat_ids),
        "last_result": last_result,
    }
