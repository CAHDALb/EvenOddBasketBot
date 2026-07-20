"""
===========================================================
EvenOddBasketBot

Файл:
telegram_bot.py

Назначение:
Принимает команды Telegram через getUpdates.
На первом этапе поддерживает:
- /start;
- /status;
- /myid.
===========================================================
"""

import time

import requests

from config import BOT_TOKEN, TELEGRAM_POLL_TIMEOUT
from telegram_sender import send_to_chat
from telegram_users import (
    get_remaining_free_signals,
    get_user,
    register_user,
)


def run_telegram_bot():
    """Бесконечно получает новые сообщения от Telegram."""

    if not BOT_TOKEN:
        print("Telegram-команды не запущены: BOT_TOKEN не найден.")
        return

    print("Telegram-команды запущены.")

    offset = None
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    while True:
        try:
            params = {
                "timeout": TELEGRAM_POLL_TIMEOUT,
                "allowed_updates": ["message"],
            }

            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                url,
                params=params,
                timeout=TELEGRAM_POLL_TIMEOUT + 10,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                print("Ошибка Telegram getUpdates:", data)
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                _handle_update(update)

        except requests.RequestException as error:
            print("Ошибка получения Telegram-команд:", error)
            time.sleep(5)

        except Exception as error:
            # Ошибка одной команды не должна остановить основного бота.
            print("Ошибка обработки Telegram-команды:", error)
            time.sleep(3)


def _handle_update(update):
    """Обрабатывает одно обновление Telegram."""

    message = update.get("message") or {}
    text = (message.get("text") or "").strip()

    if not text:
        return

    chat = message.get("chat") or {}
    sender = message.get("from") or {}

    telegram_id = chat.get("id")

    # Групповые чаты пока не регистрируем.
    if telegram_id is None or chat.get("type") != "private":
        return

    command = text.split()[0].split("@")[0].lower()

    if command == "/start":
        user = register_user(
            telegram_id=telegram_id,
            first_name=sender.get("first_name"),
            username=sender.get("username"),
            language_code=sender.get("language_code"),
        )

        send_to_chat(
            telegram_id,
            _create_start_reply(user),
        )
        return

    if command in ("/status", "/myid"):
        user = get_user(telegram_id)

        if user is None:
            user = register_user(
                telegram_id=telegram_id,
                first_name=sender.get("first_name"),
                username=sender.get("username"),
                language_code=sender.get("language_code"),
            )

        send_to_chat(
            telegram_id,
            _create_status_reply(user),
        )


def _create_start_reply(user):
    """Создаёт приветствие после /start."""

    first_name = user.get("first_name") or "друг"

    return (
        f"🏀 Добро пожаловать, {first_name}!\n\n"
        "Вы зарегистрированы в EvenOddBasketBot.\n\n"
        f"🆔 Ваш Telegram ID: {user['telegram_id']}\n"
        f"📦 Тариф: {user['tariff'].upper()}\n"
        f"{_limit_text(user)}\n\n"
        "Команды:\n"
        "/status — тариф и доступные сигналы\n"
        "/myid — ваш Telegram ID"
    )


def _create_status_reply(user):
    """Создаёт ответ для /status и /myid."""

    return (
        "👤 ВАШ ПРОФИЛЬ\n\n"
        f"🆔 Telegram ID: {user['telegram_id']}\n"
        f"📦 Тариф: {user['tariff'].upper()}\n"
        f"{_limit_text(user)}"
    )


def _limit_text(user):
    """Формирует текст о доступном дневном лимите."""

    remaining = get_remaining_free_signals(user)

    if remaining is None:
        return "✅ Доступ: все сигналы без дневного ограничения"

    return f"🎁 Осталось бесплатных сигналов сегодня: {remaining}"
