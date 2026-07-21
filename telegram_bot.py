"""
===========================================================
EvenOddBasketBot

Файл:
telegram_bot.py

Назначение:
Принимает команды, публикации, опросы и нажатия кнопок Telegram.
Поддерживает:
- регистрацию пользователя;
- профиль и дневной лимит;
- главное кнопочное меню;
- административное меню;
- мастер рассылки с предпросмотром и подтверждением;
- текстовые административные команды.
===========================================================
"""

import time

import requests

from admin_broadcast import (
    STAGE_AUDIENCE,
    STAGE_AWAITING_POLL,
    STAGE_AWAITING_POST,
    STAGE_CONFIRM,
    STAGE_DELIVERY,
    audience_title,
    cancel_draft,
    capture_content,
    content_title,
    get_session,
    set_audience,
    set_delivery_mode,
    start_broadcast,
    start_draft,
)
from admin_commands import handle_admin_command, is_admin_command
from config import BOT_TOKEN, FREE_DAILY_SIGNAL_LIMIT, TELEGRAM_POLL_TIMEOUT
from telegram_keyboards import (
    BUTTON_ADMIN_BACK,
    BUTTON_ADMIN_PANEL,
    BUTTON_AUDIENCE_ALL,
    BUTTON_AUDIENCE_FREE,
    BUTTON_AUDIENCE_PREMIUM,
    BUTTON_BACK,
    BUTTON_BLOCK,
    BUTTON_BROADCAST,
    BUTTON_BUY_PREMIUM,
    BUTTON_CANCEL,
    BUTTON_CONFIRM,
    BUTTON_CREATE_POLL,
    BUTTON_CREATE_POST,
    BUTTON_GRANT_PREMIUM,
    BUTTON_HELP,
    BUTTON_PROFILE,
    BUTTON_RECREATE,
    BUTTON_SEND_AND_PIN,
    BUTTON_SEND_NORMAL,
    BUTTON_SET_FREE,
    BUTTON_STATISTICS,
    BUTTON_UNBLOCK,
    BUTTON_USERS,
    create_admin_keyboard,
    create_audience_keyboard,
    create_broadcast_menu_keyboard,
    create_confirm_keyboard,
    create_delivery_keyboard,
    create_main_keyboard,
    create_poll_request_keyboard,
    create_waiting_post_keyboard,
)
from telegram_sender import copy_message, send_to_chat
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
            # Ошибка одного сообщения не должна остановить основного бота.
            print("Ошибка обработки Telegram-команды:", error)
            time.sleep(3)


def _handle_update(update):
    """Обрабатывает одно обновление Telegram."""

    message = update.get("message") or {}
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    telegram_id = chat.get("id")

    # Групповые чаты пока не регистрируем.
    if telegram_id is None or chat.get("type") != "private":
        return

    text = (message.get("text") or "").strip()
    parts = text.split() if text else []
    command = parts[0].split("@")[0].lower() if parts else ""
    arguments = parts[1:] if parts else []

    if command == "/start":
        cancel_draft(telegram_id)
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

    # Для остальных сообщений пользователь также должен быть в базе.
    user = get_user(telegram_id)

    if user is None:
        user = register_user(
            telegram_id=telegram_id,
            first_name=sender.get("first_name"),
            username=sender.get("username"),
            language_code=sender.get("language_code"),
        )

    # Мастер рассылки должен получить фото, видео, текст или опрос
    # раньше обычного обработчика команд и меню.
    if _is_admin(user) and _handle_broadcast_flow(
        telegram_id=telegram_id,
        user=user,
        message=message,
        text=text,
    ):
        return

    # Сообщения без текста, не относящиеся к рассылке, пока игнорируем.
    if not text:
        return

    # -------------------------------------------------------
    # Главное меню и профиль
    # -------------------------------------------------------
    if command == "/menu" or text == BUTTON_BACK:
        cancel_draft(telegram_id)
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

        _send_admin_panel(telegram_id)
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


def _handle_broadcast_flow(telegram_id, user, message, text):
    """Обрабатывает все шаги административной рассылки."""

    session = get_session(telegram_id)

    # Вход в раздел рассылки возможен и без активного черновика.
    if text == BUTTON_BROADCAST:
        cancel_draft(telegram_id)
        send_to_chat(
            telegram_id,
            _create_broadcast_menu_reply(),
            reply_markup=create_broadcast_menu_keyboard(),
        )
        return True

    if text == BUTTON_ADMIN_BACK:
        cancel_draft(telegram_id)
        _send_admin_panel(telegram_id)
        return True

    if text == BUTTON_CANCEL:
        cancel_draft(telegram_id)
        send_to_chat(
            telegram_id,
            "❌ Рассылка отменена. Ничего не было отправлено.",
            reply_markup=create_admin_keyboard(),
        )
        return True

    if text == BUTTON_CREATE_POST:
        start_draft(telegram_id, "post")
        send_to_chat(
            telegram_id,
            "📝 СОЗДАНИЕ ПУБЛИКАЦИИ\n\n"
            "Отправьте следующим сообщением готовый пост.\n\n"
            "Поддерживаются текст, фото, видео, анимация, документ, "
            "аудио и голосовое сообщение. Подпись и форматирование "
            "будут сохранены.",
            reply_markup=create_waiting_post_keyboard(),
        )
        return True

    if text == BUTTON_CREATE_POLL:
        start_draft(telegram_id, "poll")
        send_to_chat(
            telegram_id,
            "📊 СОЗДАНИЕ ОПРОСА\n\n"
            "Нажмите кнопку ниже, создайте обычный Telegram-опрос "
            "и отправьте его боту.",
            reply_markup=create_poll_request_keyboard(),
        )
        return True

    if text == BUTTON_RECREATE:
        cancel_draft(telegram_id)
        send_to_chat(
            telegram_id,
            "✏️ Старый черновик удалён. Выберите новый тип публикации.",
            reply_markup=create_broadcast_menu_keyboard(),
        )
        return True

    if not session:
        return False

    # Ожидаем готовый контент от администратора.
    if session["stage"] in {STAGE_AWAITING_POST, STAGE_AWAITING_POLL}:
        success, error = capture_content(telegram_id, message)

        if not success:
            keyboard = (
                create_poll_request_keyboard()
                if session["stage"] == STAGE_AWAITING_POLL
                else create_waiting_post_keyboard()
            )
            send_to_chat(
                telegram_id,
                f"❌ {error}",
                reply_markup=keyboard,
            )
            return True

        preview_result = copy_message(
            chat_id=telegram_id,
            from_chat_id=telegram_id,
            message_id=message["message_id"],
        )

        if not preview_result.get("ok"):
            cancel_draft(telegram_id)
            send_to_chat(
                telegram_id,
                "❌ Telegram не смог создать предпросмотр. "
                "Черновик отменён, попробуйте другой формат.",
                reply_markup=create_admin_keyboard(),
            )
            return True

        send_to_chat(
            telegram_id,
            "👁 ПРЕДПРОСМОТР ВЫШЕ\n\n"
            "Теперь выберите, кому отправить публикацию.",
            reply_markup=create_audience_keyboard(),
        )
        return True

    if session["stage"] == STAGE_AUDIENCE:
        audience = {
            BUTTON_AUDIENCE_ALL: "all",
            BUTTON_AUDIENCE_PREMIUM: "premium",
            BUTTON_AUDIENCE_FREE: "free",
        }.get(text)

        if audience is None:
            send_to_chat(
                telegram_id,
                "Выберите аудиторию кнопкой ниже.",
                reply_markup=create_audience_keyboard(),
            )
            return True

        set_audience(telegram_id, audience)
        send_to_chat(
            telegram_id,
            "👥 АУДИТОРИЯ ВЫБРАНА\n\n"
            f"Получатели: {audience_title(audience)}.\n\n"
            "Теперь выберите обычную отправку или отправку "
            "с закреплением сообщения у каждого пользователя.",
            reply_markup=create_delivery_keyboard(),
        )
        return True

    if session["stage"] == STAGE_DELIVERY:
        if text == BUTTON_SEND_NORMAL:
            updated = set_delivery_mode(telegram_id, pin=False)
        elif text == BUTTON_SEND_AND_PIN:
            updated = set_delivery_mode(telegram_id, pin=True)
        else:
            send_to_chat(
                telegram_id,
                "Выберите способ отправки кнопкой ниже.",
                reply_markup=create_delivery_keyboard(),
            )
            return True

        send_to_chat(
            telegram_id,
            _create_broadcast_confirmation(updated),
            reply_markup=create_confirm_keyboard(),
        )
        return True

    if session["stage"] == STAGE_CONFIRM:
        if text != BUTTON_CONFIRM:
            send_to_chat(
                telegram_id,
                "Для запуска нажмите «✅ Подтвердить» или отмените рассылку.",
                reply_markup=create_confirm_keyboard(),
            )
            return True

        if not start_broadcast(telegram_id):
            send_to_chat(
                telegram_id,
                "❌ Не удалось запустить рассылку: черновик устарел.",
                reply_markup=create_admin_keyboard(),
            )
        return True

    return False


def _send_main_menu(telegram_id, user, text):
    """Отправляет сообщение вместе с главным меню."""

    send_to_chat(
        telegram_id,
        text,
        reply_markup=create_main_keyboard(user),
    )


def _send_admin_panel(telegram_id):
    """Открывает основное административное меню."""

    send_to_chat(
        telegram_id,
        _create_admin_panel_reply(),
        reply_markup=create_admin_keyboard(),
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
                "",
                "Кнопка «📢 Рассылка» открывает мастер публикаций.",
            ]
        )

    return "\n".join(lines)


def _create_admin_panel_reply():
    """Создаёт приветствие административного меню."""

    return (
        "👑 АДМИН-ПАНЕЛЬ\n\n"
        "Здесь можно управлять пользователями и делать публикации.\n\n"
        "Раздел «📢 Рассылка» поддерживает текст, фото, видео, "
        "файлы и обычные Telegram-опросы."
    )


def _create_broadcast_menu_reply():
    """Описание первого экрана рассылки."""

    return (
        "📢 АДМИНСКАЯ РАССЫЛКА\n\n"
        "1. Создайте публикацию или опрос.\n"
        "2. Проверьте предпросмотр.\n"
        "3. Выберите аудиторию.\n"
        "4. Выберите обычную отправку или закрепление.\n"
        "5. Подтвердите запуск.\n\n"
        "До финального подтверждения пользователи ничего не получат."
    )


def _create_broadcast_confirmation(session):
    """Формирует финальную карточку подтверждения."""

    pin_text = "да" if session.get("pin") else "нет"

    return (
        "⚠️ ПОДТВЕРЖДЕНИЕ РАССЫЛКИ\n\n"
        f"Тип: {content_title(session.get('content_kind'))}\n"
        f"Аудитория: {audience_title(session.get('audience'))}\n"
        f"Закрепить у получателей: {pin_text}\n\n"
        "После нажатия «✅ Подтвердить» рассылка начнётся сразу."
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
