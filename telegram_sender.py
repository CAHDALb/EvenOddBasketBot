"""
===========================================================
EvenOddBasketBot

Файл:
telegram_sender.py

Назначение:
- отправляет служебные сообщения администраторам;
- рассылает сигналы пользователям с учётом тарифа;
- копирует административные публикации;
- закрепляет сообщения административной рассылки.
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

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    return _telegram_request(
        "sendMessage",
        payload,
        recipient_chat_id=chat_id,
    )


def copy_message(chat_id, from_chat_id, message_id):
    """Копирует готовое сообщение без ссылки на исходник."""

    return _telegram_request(
        "copyMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
        },
        recipient_chat_id=chat_id,
    )


def pin_chat_message(chat_id, message_id):
    """Закрепляет отправленное ботом сообщение в личном чате."""

    return _telegram_request(
        "pinChatMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": True,
        },
        recipient_chat_id=chat_id,
    )


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


def _telegram_request(method, payload, recipient_chat_id=None):
    """Выполняет безопасный запрос к Telegram Bot API."""

    if not BOT_TOKEN:
        return {
            "ok": False,
            "description": "BOT_TOKEN не найден.",
        }

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()

        if (
            recipient_chat_id is not None
            and not result.get("ok")
            and response.status_code in (400, 403)
            and _looks_like_unavailable_chat(result)
        ):
            try:
                deactivate_user(recipient_chat_id)
            except Exception as error:
                print("Не удалось отключить пользователя:", error)

        return result

    except (requests.RequestException, ValueError) as error:
        return {
            "ok": False,
            "description": str(error),
        }


def _looks_like_unavailable_chat(result):
    """Не блокирует пользователя из-за обычной ошибки формата запроса."""

    description = str(result.get("description") or "").lower()
    markers = (
        "bot was blocked",
        "user is deactivated",
        "chat not found",
        "forbidden",
        "bot can't initiate conversation",
    )
    return any(marker in description for marker in markers)


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
