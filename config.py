import os
from dotenv import load_dotenv

# Загружаем переменные из .env (локально)
load_dotenv()

# ===========================
# Telegram
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Старую переменную CHAT_IDS сохраняем для плавного перехода.
# Все ID из неё при запуске автоматически станут администраторами.
CHAT_IDS = [
    chat_id.strip()
    for chat_id in os.getenv("CHAT_IDS", "").split(",")
    if chat_id.strip()
]

# Можно использовать отдельную переменную ADMIN_TELEGRAM_IDS.
ADMIN_TELEGRAM_IDS = [
    chat_id.strip()
    for chat_id in os.getenv(
        "ADMIN_TELEGRAM_IDS",
        os.getenv("CHAT_IDS", ""),
    ).split(",")
    if chat_id.strip()
]

FREE_DAILY_SIGNAL_LIMIT = int(
    os.getenv("FREE_DAILY_SIGNAL_LIMIT", "2")
)

TELEGRAM_POLL_TIMEOUT = int(
    os.getenv("TELEGRAM_POLL_TIMEOUT", "25")
)

# ===========================
# Интервал проверки
# ===========================

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "180"))

# ===========================
# Flashscore
# ===========================

HEADERS = {
    "X-Fsign": "SW9D1eZo"
}

FEED = "f_3_0_4_ru_1"
