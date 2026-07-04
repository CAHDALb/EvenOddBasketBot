import os
from dotenv import load_dotenv

# Загружаем переменные из .env (локально)
load_dotenv()

# ===========================
# Telegram
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHAT_IDS = [
    chat_id.strip()
    for chat_id in os.getenv("CHAT_IDS", "").split(",")
    if chat_id.strip()
]

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