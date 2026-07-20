"""
===========================================================
EvenOddBasketBot

Файл:
telegram_bot.py

Назначение:
Принимает команды и нажатия кнопок Telegram через getUpdates.
Поддерживает:
- регистрацию пользователя;
- профиль и дневной лимит;
- главное кнопочное меню;
- административное кнопочное меню;
- текстовые административные команды.
===========================================================
"""

import time

import requests

from admin_commands import handle_admin_command, is_admin_command
from config import BOT_TOKEN, FREE_DAILY_SIGNAL_LIMIT, TELEGRAM_POLL_TIMEOUT
from telegram_keyboards import (
    BUTTON_ADMIN_PANEL,
    BUTTON_BACK,
    BUTTON_BLOCK,
    BUTTON_BUY_PREMIUM,
    BUTTON_GRANT_PREMIUM,
    BUTTON_HELP,
    BUTTON_PROFILE,
    BUTTON_SET_FREE,
    BUTTON_STATISTICS,
    BUTTON_UNBLOCK,
    BUTTON_USERS,
    create_admin_keyboard,
    create_main_keyboard,
)
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

    parts = text.split()
    command = parts[0].split("@")[0].lower()
    arguments = parts[1:]

    if command == "/start":
        user = register_user(
            telegram_id=telegram_id,
            first_name=sender.get("first_name"),
            username=sender.get("username"),
            language_code=sender.get("language_code"),
        )

        _send_main_menu(
            telegram_id,
            user,
            _create_start_reply(user),
        )
        return

    # Для остальных команд пользователь также должен быть в базе.
    user = get_user(telegram_id)

    if user is None:
        user = register_user(
            telegram_id=telegram_id,
            first_name=sender.get("first_name"),
            username=sender.get("username"),
            language_code=sender.get("language_code"),
        )

    # -------------------------------------------------------
    # Главное меню и профиль
    # -------------------------------------------------------
    if command == "/menu" or text == BUTTON_BACK:
        _send_main_menu(
            telegram_id,
            user,
            "🏠 ГЛАВНОЕ МЕНЮ\n\nВыберите нужный раздел кнопкой ниже.",
        )
        return

    if command in ("/status", "/myid", "/profile") or text == BUTTON_PROFILE:
        _send_main_menu(
            telegram_id,
            user,
            _create_profile_reply(user),
        )
        return

    if text == BUTTON_STATISTICS:
        _send_main_menu(
            telegram_id,
            user,
            _create_personal_statistics_reply(user),
        )
        return

    if text == BUTTON_BUY_PREMIUM:
        _send_main_menu(
            telegram_id,
            user,
            _create_premium_reply(user),
        )
        return

    if command == "/help" or text == BUTTON_HELP:
        _send_main_menu(
            telegram_id,
            user,
            _create_help_reply(user),
        )
        return

    # -------------------------------------------------------
    # Административное кнопочное меню
    # -------------------------------------------------------
    if text == BUTTON_ADMIN_PANEL:
        if not _is_admin(user):
            _send_main_menu(
                telegram_id,
                user,
                "⛔ Админ-панель доступна только администратору.",
            )
            return

        send_to_chat(
            telegram_id,
            _create_admin_panel_reply(),
            reply_markup=create_admin_keyboard(),
        )
        return

    if text == BUTTON_USERS:
        _send_admin_result(
            telegram_id,
            user,
            handle_admin_command("/users", [], user),
        )
        return

    if text == BUTTON_GRANT_PREMIUM:
        _send_admin_instruction(
            telegram_id,
            user,
            "💎 ВЫДАТЬ PREMIUM\n\n"
            "Отправьте команду:\n"
            "/premium TELEGRAM_ID DAYS\n\n"
            "Пример:\n"
            "/premium 123456789 30",
        )
        return

    if text == BUTTON_SET_FREE:
        _send_admin_instruction(
            telegram_id,
            user,
            "🆓 ПЕРЕВЕСТИ В FREE\n\n"
            "Отправьте команду:\n"
            "/free TELEGRAM_ID\n\n"
            "Пример:\n"
            "/free 123456789",
        )
        return

    if text == BUTTON_BLOCK:
        _send_admin_instruction(
            telegram_id,
            user,
            "🚫 ЗАБЛОКИРОВАТЬ\n\n"
            "Отправьте команду:\n"
            "/block TELEGRAM_ID\n\n"
            "Пример:\n"
            "/block 123456789",
        )
        return

    if text == BUTTON_UNBLOCK:
        _send_admin_instruction(
            telegram_id,
            user,
            "✅ РАЗБЛОКИРОВАТЬ\n\n"
            "Отправьте команду:\n"
            "/unblock TELEGRAM_ID\n\n"
            "Пример:\n"
            "/unblock 123456789",
        )
        return

    # Старые текстовые команды продолжают работать параллельно кнопкам.
    if is_admin_command(command):
        _send_admin_result(
            telegram_id,
            user,
            handle_admin_command(command, arguments, user),
        )
        return

    _send_main_menu(
        telegram_id,
        user,
        "Неизвестная команда. Используйте кнопки меню или отправьте /help.",
    )


def _send_main_menu(telegram_id, user, text):
    """Отправляет сообщение вместе с главным меню."""

    send_to_chat(
        telegram_id,
        text,
        reply_markup=create_main_keyboard(user),
    )


def _send_admin_result(telegram_id, user, text):
    """Отправляет результат админ-команды и сохраняет админ-меню."""

    if not _is_admin(user):
        _send_main_menu(telegram_id, user, text)
        return

    send_to_chat(
        telegram_id,
        text,
        reply_markup=create_admin_keyboard(),
    )


def _send_admin_instruction(telegram_id, user, text):
    """Показывает инструкцию к выбранному действию админа."""

    if not _is_admin(user):
        _send_main_menu(
            telegram_id,
            user,
            "⛔ Эта функция доступна только администратору.",
        )
        return

    send_to_chat(
        telegram_id,
        text,
        reply_markup=create_admin_keyboard(),
    )


def _create_start_reply(user):
    """Создаёт приветствие после /start."""

    first_name = user.get("first_name") or "друг"

    return (
        f"🏀 Добро пожаловать, {first_name}!\n\n"
        "Вы зарегистрированы в EvenOddBasketBot.\n\n"
        f"📦 Тариф: {_tariff_title(user)}\n"
        f"{_limit_text(user)}\n\n"
        "Используйте кнопки меню внизу экрана."
    )


def _create_profile_reply(user):
    """Создаёт полный профиль пользователя."""

    username = user.get("username")
    username_text = f"@{username}" if username else "не указан"
    status_text = "активен" if user.get("is_active") else "заблокирован"

    lines = [
        "👤 МОЙ ПРОФИЛЬ",
        "",
        f"Имя: {user.get('first_name') or 'не указано'}",
        f"Username: {username_text}",
        f"Telegram ID: {user['telegram_id']}",
        f"Тариф: {_tariff_title(user)}",
        f"Статус: {status_text}",
        "",
        f"📨 Получено сигналов сегодня: {user.get('signals_today', 0)}",
        _limit_text(user),
    ]

    premium_until = user.get("premium_until")

    if user.get("tariff") == "premium" and premium_until:
        lines.extend(
            [
                "",
                "💎 Premium действует до: "
                f"{premium_until.strftime('%d.%m.%Y %H:%M')} UTC",
            ]
        )

    created_at = user.get("created_at")

    if created_at:
        lines.extend(
            [
                "",
                "📅 Регистрация: "
                f"{created_at.strftime('%d.%m.%Y %H:%M')} UTC",
            ]
        )

    return "\n".join(lines)


def _create_personal_statistics_reply(user):
    """Показывает доступную персональную статистику пользователя."""

    tariff = user.get("tariff")
    signals_today = int(user.get("signals_today") or 0)

    lines = [
        "📈 МОЯ СТАТИСТИКА",
        "",
        f"Тариф: {_tariff_title(user)}",
    ]

    if tariff == "free":
        remaining = get_remaining_free_signals(user)
        lines.extend(
            [
                f"Сигналов получено сегодня: {signals_today}",
                f"Дневной лимит: {FREE_DAILY_SIGNAL_LIMIT}",
                f"Осталось сегодня: {remaining}",
            ]
        )
    else:
        lines.extend(
            [
                "Дневной лимит: без ограничений",
                "Для ADMIN и PREMIUM ограничивающий счётчик не используется.",
            ]
        )

    lines.extend(
        [
            "",
            "Персональную историю WIN/LOSE добавим следующим этапом.",
        ]
    )

    return "\n".join(lines)


def _create_premium_reply(user):
    """Показывает информацию о тарифе Premium."""

    if user.get("tariff") in ("premium", "admin"):
        return (
            "💎 PREMIUM\n\n"
            "У вас уже открыт доступ ко всем сигналам без дневного лимита."
        )

    return (
        "💎 PREMIUM\n\n"
        f"FREE получает до {FREE_DAILY_SIGNAL_LIMIT} сигналов в сутки.\n"
        "PREMIUM получает все подходящие сигналы без дневного ограничения.\n\n"
        "Автоматическую оплату подключим на следующем этапе. "
        "Пока Premium выдаёт администратор."
    )


def _create_help_reply(user):
    """Создаёт краткую справку по боту."""

    lines = [
        "ℹ️ ПОМОЩЬ",
        "",
        "Используйте кнопки внизу Telegram.",
        "",
        "Текстовые команды:",
        "/start — регистрация и главное меню",
        "/menu — открыть главное меню",
        "/profile — мой профиль",
        "/status — тариф и доступ",
        "/myid — профиль и Telegram ID",
        "/help — эта справка",
    ]

    if _is_admin(user):
        lines.extend(
            [
                "",
                "Команды администратора:",
                "/users [PAGE]",
                "/premium TELEGRAM_ID DAYS",
                "/free TELEGRAM_ID",
                "/block TELEGRAM_ID",
                "/unblock TELEGRAM_ID",
            ]
        )

    return "\n".join(lines)


def _create_admin_panel_reply():
    """Создаёт приветствие административного меню."""

    return (
        "👑 АДМИН-ПАНЕЛЬ\n\n"
        "Здесь можно посмотреть пользователей и управлять их доступом.\n\n"
        "После выбора Premium, FREE или блокировки бот покажет готовый "
        "формат команды."
    )


def _limit_text(user):
    """Формирует текст о доступном дневном лимите."""

    remaining = get_remaining_free_signals(user)

    if remaining is None:
        return "✅ Доступ: все сигналы без дневного ограничения"

    return f"🎁 Осталось бесплатных сигналов сегодня: {remaining}"


def _tariff_title(user):
    """Возвращает красивое название тарифа."""

    tariff = (user.get("tariff") or "free").lower()

    if tariff == "admin":
        return "ADMIN 👑"

    if tariff == "premium":
        return "PREMIUM 💎"

    return "FREE 🆓"


def _is_admin(user):
    """Проверяет административный тариф."""

    return bool(user and user.get("tariff") == "admin")
