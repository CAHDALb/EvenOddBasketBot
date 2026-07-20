"""
===========================================================
EvenOddBasketBot

Файл:
admin_commands.py

Назначение:
Команды управления пользователями, доступные только ADMIN:
- /users;
- /premium TELEGRAM_ID DAYS;
- /free TELEGRAM_ID;
- /block TELEGRAM_ID;
- /unblock TELEGRAM_ID.
===========================================================
"""

from datetime import datetime, timedelta, timezone

from telegram_users import (
    get_user,
    get_user_statistics,
    set_user_active,
    set_user_tariff,
)


ADMIN_COMMANDS = {
    "/users",
    "/premium",
    "/free",
    "/block",
    "/unblock",
}


def is_admin_command(command):
    """Возвращает True, если команда относится к админ-панели."""

    return command in ADMIN_COMMANDS


def handle_admin_command(command, arguments, admin_user):
    """
    Обрабатывает административную команду.

    Возвращает готовый текст ответа для Telegram.
    """

    if not admin_user or admin_user.get("tariff") != "admin":
        return "⛔ Эта команда доступна только администратору."

    if command == "/users":
        return _handle_users()

    if command == "/premium":
        return _handle_premium(arguments)

    if command == "/free":
        return _handle_free(arguments)

    if command == "/block":
        return _handle_block(arguments)

    if command == "/unblock":
        return _handle_unblock(arguments)

    return "Неизвестная административная команда."


def _handle_users():
    """Формирует общую статистику пользователей."""

    statistics = get_user_statistics()

    return (
        "👥 ПОЛЬЗОВАТЕЛИ\n\n"
        f"Всего: {statistics['total']}\n\n"
        f"👑 ADMIN: {statistics['admin']}\n"
        f"💎 PREMIUM: {statistics['premium']}\n"
        f"🆓 FREE: {statistics['free']}\n"
        f"🚫 Заблокировано: {statistics['blocked']}\n\n"
        f"Сегодня зарегистрировалось: {statistics['today']}\n"
        f"За последние 7 дней: {statistics['last_7_days']}\n"
        f"За последние 30 дней: {statistics['last_30_days']}"
    )


def _handle_premium(arguments):
    """Выдаёт пользователю Premium на указанное количество дней."""

    if len(arguments) != 2:
        return (
            "Использование:\n"
            "/premium TELEGRAM_ID DAYS\n\n"
            "Пример:\n"
            "/premium 123456789 30"
        )

    telegram_id = _parse_telegram_id(arguments[0])
    days = _parse_positive_integer(arguments[1])

    if telegram_id is None:
        return "❌ Telegram ID должен состоять только из цифр."

    if days is None:
        return "❌ Количество дней должно быть целым числом больше нуля."

    user = get_user(telegram_id)

    if user is None:
        return (
            "❌ Пользователь не найден.\n\n"
            "Сначала он должен открыть бота и отправить /start."
        )

    premium_until = datetime.now(timezone.utc) + timedelta(days=days)
    set_user_tariff(
        telegram_id=telegram_id,
        tariff="premium",
        premium_until=premium_until,
    )

    return (
        "✅ PREMIUM ВЫДАН\n\n"
        f"Пользователь: {_user_title(user)}\n"
        f"Telegram ID: {telegram_id}\n"
        f"Срок: {days} дн.\n"
        f"До: {premium_until.strftime('%d.%m.%Y %H:%M')} UTC"
    )


def _handle_free(arguments):
    """Переводит пользователя на бесплатный тариф."""

    telegram_id, error = _single_user_argument(arguments, "/free")

    if error:
        return error

    user = get_user(telegram_id)

    if user is None:
        return "❌ Пользователь с таким Telegram ID не найден."

    if user.get("tariff") == "admin":
        return "⛔ Нельзя снять права ADMIN этой командой."

    set_user_tariff(telegram_id, "free")

    return (
        "✅ ТАРИФ ИЗМЕНЁН\n\n"
        f"Пользователь: {_user_title(user)}\n"
        f"Telegram ID: {telegram_id}\n"
        "Новый тариф: FREE"
    )


def _handle_block(arguments):
    """Отключает пользователя от получения сообщений бота."""

    telegram_id, error = _single_user_argument(arguments, "/block")

    if error:
        return error

    user = get_user(telegram_id)

    if user is None:
        return "❌ Пользователь с таким Telegram ID не найден."

    if user.get("tariff") == "admin":
        return "⛔ Нельзя заблокировать администратора."

    set_user_active(telegram_id, False)

    return (
        "🚫 ПОЛЬЗОВАТЕЛЬ ЗАБЛОКИРОВАН\n\n"
        f"Пользователь: {_user_title(user)}\n"
        f"Telegram ID: {telegram_id}"
    )


def _handle_unblock(arguments):
    """Возвращает пользователю доступ к боту и сигналам."""

    telegram_id, error = _single_user_argument(arguments, "/unblock")

    if error:
        return error

    user = get_user(telegram_id)

    if user is None:
        return "❌ Пользователь с таким Telegram ID не найден."

    set_user_active(telegram_id, True)

    return (
        "✅ ПОЛЬЗОВАТЕЛЬ РАЗБЛОКИРОВАН\n\n"
        f"Пользователь: {_user_title(user)}\n"
        f"Telegram ID: {telegram_id}"
    )


def _single_user_argument(arguments, command):
    """Проверяет команду, которой нужен только Telegram ID."""

    if len(arguments) != 1:
        return None, (
            f"Использование:\n{command} TELEGRAM_ID\n\n"
            f"Пример:\n{command} 123456789"
        )

    telegram_id = _parse_telegram_id(arguments[0])

    if telegram_id is None:
        return None, "❌ Telegram ID должен состоять только из цифр."

    return telegram_id, None


def _parse_telegram_id(value):
    """Безопасно переводит Telegram ID в число."""

    try:
        telegram_id = int(value)
    except (TypeError, ValueError):
        return None

    return telegram_id if telegram_id > 0 else None


def _parse_positive_integer(value):
    """Возвращает положительное целое число или None."""

    try:
        number = int(value)
    except (TypeError, ValueError):
        return None

    return number if number > 0 else None


def _user_title(user):
    """Создаёт удобное имя пользователя для ответа администратора."""

    first_name = user.get("first_name") or "Без имени"
    username = user.get("username")

    if username:
        return f"{first_name} (@{username})"

    return first_name
