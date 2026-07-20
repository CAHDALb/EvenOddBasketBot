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
    get_users_page,
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
        return _handle_users(arguments)

    if command == "/premium":
        return _handle_premium(arguments)

    if command == "/free":
        return _handle_free(arguments, admin_user)

    if command == "/block":
        return _handle_block(arguments)

    if command == "/unblock":
        return _handle_unblock(arguments)

    return "Неизвестная административная команда."


def _handle_users(arguments):
    """
    Показывает статистику и список зарегистрированных пользователей.

    Без аргумента открывает первую страницу:
    /users

    Для следующей страницы:
    /users 2
    """

    if len(arguments) > 1:
        return (
            "Использование:\n"
            "/users\n"
            "/users PAGE\n\n"
            "Пример:\n"
            "/users 2"
        )

    page = 1

    if arguments:
        page = _parse_positive_integer(arguments[0])

        if page is None:
            return "❌ Номер страницы должен быть целым числом больше нуля."

    statistics = get_user_statistics()
    users_page = get_users_page(page=page, page_size=10)

    lines = [
        "👥 ПОЛЬЗОВАТЕЛИ",
        "",
        f"Всего: {statistics['total']}",
        f"👑 ADMIN: {statistics['admin']}",
        f"💎 PREMIUM: {statistics['premium']}",
        f"🆓 FREE: {statistics['free']}",
        f"🚫 Заблокировано: {statistics['blocked']}",
        "",
        (
            "📋 СПИСОК "
            f"— страница {users_page['page']}/{users_page['pages']}"
        ),
        "",
    ]

    if not users_page["users"]:
        lines.append("Пользователей пока нет.")
    else:
        start_number = (
            (users_page["page"] - 1) * users_page["page_size"] + 1
        )

        for number, user in enumerate(
            users_page["users"],
            start=start_number,
        ):
            lines.extend(_format_user_for_list(number, user))

    if users_page["pages"] > 1:
        lines.extend(
            [
                "",
                "Следующая страница:",
                f"/users {min(users_page['page'] + 1, users_page['pages'])}",
            ]
        )

    return "\n".join(lines)


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


def _handle_free(arguments, admin_user):
    """Переводит пользователя на бесплатный тариф."""

    telegram_id, error = _single_user_argument(arguments, "/free")

    if error:
        return error

    user = get_user(telegram_id)

    if user is None:
        return "❌ Пользователь с таким Telegram ID не найден."

    if (
        user.get("tariff") == "admin"
        and int(telegram_id) == int(admin_user["telegram_id"])
    ):
        return "⛔ Нельзя снять права ADMIN у самого себя."

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



def _format_user_for_list(number, user):
    """Формирует карточку одного пользователя внутри команды /users."""

    tariff = user.get("tariff", "free")
    is_active = bool(user.get("is_active"))

    if not is_active:
        icon = "🚫"
        tariff_title = f"{tariff.upper()} · заблокирован"
    elif tariff == "admin":
        icon = "👑"
        tariff_title = "ADMIN"
    elif tariff == "premium":
        icon = "💎"
        tariff_title = "PREMIUM"
    else:
        icon = "🆓"
        tariff_title = "FREE"

    lines = [
        f"{number}. {icon} {_user_title(user)}",
        f"ID: {user['telegram_id']}",
        f"Тариф: {tariff_title}",
    ]

    premium_until = user.get("premium_until")

    if tariff == "premium" and premium_until:
        lines.append(
            "Premium до: "
            f"{premium_until.strftime('%d.%m.%Y %H:%M')} UTC"
        )

    lines.append("")
    return lines

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
