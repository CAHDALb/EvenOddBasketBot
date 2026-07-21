"""
===========================================================
EvenOddBasketBot

Файл:
telegram_keyboards.py

Назначение:
Создаёт кнопочные меню Telegram:
- главное меню пользователя;
- административное меню;
- мастер административной рассылки.
===========================================================
"""


# Кнопки главного меню
BUTTON_PROFILE = "👤 Мой профиль"
BUTTON_STATISTICS = "📈 Моя статистика"
BUTTON_BUY_PREMIUM = "💎 Купить Premium"
BUTTON_HELP = "ℹ️ Помощь"
BUTTON_ABOUT = "🏀 О проекте"
BUTTON_ADMIN_PANEL = "👑 Админ-панель"

# Кнопки административного меню
BUTTON_USERS = "👥 Пользователи"
BUTTON_GRANT_PREMIUM = "💎 Выдать Premium"
BUTTON_SET_FREE = "🆓 Перевести в FREE"
BUTTON_BLOCK = "🚫 Заблокировать"
BUTTON_UNBLOCK = "✅ Разблокировать"
BUTTON_BROADCAST = "📢 Рассылка"
BUTTON_BACK = "⬅ Назад"

# Кнопки мастера рассылки
BUTTON_CREATE_POST = "📝 Создать публикацию"
BUTTON_CREATE_POLL = "📊 Создать опрос"
BUTTON_REQUEST_POLL = "📊 Открыть конструктор опроса"
BUTTON_AUDIENCE_ALL = "📢 Отправить всем"
BUTTON_AUDIENCE_PREMIUM = "💎 Только PREMIUM"
BUTTON_AUDIENCE_FREE = "🆓 Только FREE"
BUTTON_SEND_NORMAL = "📤 Отправить"
BUTTON_SEND_AND_PIN = "📌 Отправить и закрепить"
BUTTON_RECREATE = "✏️ Создать заново"
BUTTON_CONFIRM = "✅ Подтвердить"
BUTTON_CANCEL = "❌ Отмена"
BUTTON_ADMIN_BACK = "⬅ В админ-панель"


MAIN_MENU_BUTTONS = {
    BUTTON_PROFILE,
    BUTTON_STATISTICS,
    BUTTON_BUY_PREMIUM,
    BUTTON_HELP,
    BUTTON_ABOUT,
    BUTTON_ADMIN_PANEL,
    BUTTON_BACK,
}

ADMIN_MENU_BUTTONS = {
    BUTTON_USERS,
    BUTTON_GRANT_PREMIUM,
    BUTTON_SET_FREE,
    BUTTON_BLOCK,
    BUTTON_UNBLOCK,
    BUTTON_BROADCAST,
}

BROADCAST_BUTTONS = {
    BUTTON_CREATE_POST,
    BUTTON_CREATE_POLL,
    BUTTON_REQUEST_POLL,
    BUTTON_AUDIENCE_ALL,
    BUTTON_AUDIENCE_PREMIUM,
    BUTTON_AUDIENCE_FREE,
    BUTTON_SEND_NORMAL,
    BUTTON_SEND_AND_PIN,
    BUTTON_RECREATE,
    BUTTON_CONFIRM,
    BUTTON_CANCEL,
    BUTTON_ADMIN_BACK,
}


def create_main_keyboard(user):
    """Возвращает главное меню с учётом тарифа пользователя."""

    keyboard = [
        [BUTTON_PROFILE, BUTTON_STATISTICS],
        [BUTTON_BUY_PREMIUM, BUTTON_ABOUT],
        [BUTTON_HELP],
    ]

    if user and user.get("tariff") == "admin":
        keyboard.append([BUTTON_ADMIN_PANEL])

    return _reply_keyboard(keyboard, "Выберите раздел меню")


def create_admin_keyboard():
    """Возвращает меню управления пользователями для ADMIN."""

    keyboard = [
        [BUTTON_USERS, BUTTON_BROADCAST],
        [BUTTON_GRANT_PREMIUM, BUTTON_SET_FREE],
        [BUTTON_BLOCK, BUTTON_UNBLOCK],
        [BUTTON_BACK],
    ]

    return _reply_keyboard(keyboard, "Выберите действие администратора")


def create_broadcast_menu_keyboard():
    """Первый экран мастера рассылки."""

    keyboard = [
        [BUTTON_CREATE_POST],
        [BUTTON_CREATE_POLL],
        [BUTTON_ADMIN_BACK],
    ]

    return _reply_keyboard(keyboard, "Выберите тип публикации")


def create_waiting_post_keyboard():
    """Клавиатура ожидания текста, фото, видео или файла."""

    return _reply_keyboard(
        [[BUTTON_CANCEL]],
        "Отправьте готовую публикацию",
    )


def create_poll_request_keyboard():
    """Открывает штатный конструктор обычного Telegram-опроса."""

    keyboard = [
        [
            {
                "text": BUTTON_REQUEST_POLL,
                "request_poll": {"type": "regular"},
            }
        ],
        [BUTTON_CANCEL],
    ]

    return _reply_keyboard(keyboard, "Создайте обычный опрос")


def create_audience_keyboard():
    """Выбор получателей публикации."""

    keyboard = [
        [BUTTON_AUDIENCE_ALL],
        [BUTTON_AUDIENCE_PREMIUM, BUTTON_AUDIENCE_FREE],
        [BUTTON_RECREATE, BUTTON_CANCEL],
    ]

    return _reply_keyboard(keyboard, "Выберите аудиторию")


def create_delivery_keyboard():
    """Выбор обычной отправки или отправки с закреплением."""

    keyboard = [
        [BUTTON_SEND_NORMAL],
        [BUTTON_SEND_AND_PIN],
        [BUTTON_RECREATE, BUTTON_CANCEL],
    ]

    return _reply_keyboard(keyboard, "Выберите способ отправки")


def create_confirm_keyboard():
    """Финальное подтверждение рассылки."""

    keyboard = [
        [BUTTON_CONFIRM],
        [BUTTON_RECREATE, BUTTON_CANCEL],
    ]

    return _reply_keyboard(keyboard, "Подтвердите рассылку")


def _reply_keyboard(keyboard, placeholder):
    """Формирует Telegram ReplyKeyboardMarkup в виде словаря."""

    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": placeholder,
    }
