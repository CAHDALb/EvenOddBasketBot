"""
===========================================================
EvenOddBasketBot

Файл:
telegram_keyboards.py

Назначение:
Создаёт кнопочные меню Telegram:
- главное меню пользователя;
- административное меню.
===========================================================
"""


# Кнопки главного меню
BUTTON_PROFILE = "👤 Мой профиль"
BUTTON_STATISTICS = "📈 Моя статистика"
BUTTON_BUY_PREMIUM = "💎 Купить Premium"
BUTTON_HELP = "ℹ️ Помощь"
BUTTON_ADMIN_PANEL = "👑 Админ-панель"

# Кнопки административного меню
BUTTON_USERS = "👥 Пользователи"
BUTTON_GRANT_PREMIUM = "💎 Выдать Premium"
BUTTON_SET_FREE = "🆓 Перевести в FREE"
BUTTON_BLOCK = "🚫 Заблокировать"
BUTTON_UNBLOCK = "✅ Разблокировать"
BUTTON_BACK = "⬅ Назад"


MAIN_MENU_BUTTONS = {
    BUTTON_PROFILE,
    BUTTON_STATISTICS,
    BUTTON_BUY_PREMIUM,
    BUTTON_HELP,
    BUTTON_ADMIN_PANEL,
    BUTTON_BACK,
}

ADMIN_MENU_BUTTONS = {
    BUTTON_USERS,
    BUTTON_GRANT_PREMIUM,
    BUTTON_SET_FREE,
    BUTTON_BLOCK,
    BUTTON_UNBLOCK,
}


def create_main_keyboard(user):
    """Возвращает главное меню с учётом тарифа пользователя."""

    keyboard = [
        [BUTTON_PROFILE, BUTTON_STATISTICS],
        [BUTTON_BUY_PREMIUM, BUTTON_HELP],
    ]

    if user and user.get("tariff") == "admin":
        keyboard.append([BUTTON_ADMIN_PANEL])

    return _reply_keyboard(keyboard, "Выберите раздел меню")


def create_admin_keyboard():
    """Возвращает меню управления пользователями для ADMIN."""

    keyboard = [
        [BUTTON_USERS],
        [BUTTON_GRANT_PREMIUM, BUTTON_SET_FREE],
        [BUTTON_BLOCK, BUTTON_UNBLOCK],
        [BUTTON_BACK],
    ]

    return _reply_keyboard(keyboard, "Выберите действие администратора")


def _reply_keyboard(keyboard, placeholder):
    """Формирует Telegram ReplyKeyboardMarkup в виде словаря."""

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": placeholder,
    }
