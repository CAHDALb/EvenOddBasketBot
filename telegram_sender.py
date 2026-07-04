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

    last_result = None

    # =====================================================
    # Отправляем сообщение каждому пользователю
    # =====================================================

    for chat_id in CHAT_IDS:

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text
            }
        )

        last_result = response.json()

    return last_result

    return response.json()