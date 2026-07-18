"""
===========================================================
EvenOddBasketBot

Файл:
telegram_sender.py

Назначение:
Отправляет сообщения всем получателям.

Версия:
0.4
===========================================================
"""

import requests

from config import BOT_TOKEN, CHAT_IDS


def send_telegram(text):
    """
    Отправляет сообщение всем пользователям,
    указанным в CHAT_IDS.
    """

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    last_result = {
        "ok": False,
        "description": "Сообщение не было отправлено."
    }

    # =====================================================
    # Отправляем сообщение каждому пользователю
    # =====================================================

    for chat_id in CHAT_IDS:

        try:

            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                },
                timeout=20,
            )

            last_result = response.json()

        except requests.RequestException as error:

            last_result = {
                "ok": False,
                "description": str(error),
            }

    return last_result