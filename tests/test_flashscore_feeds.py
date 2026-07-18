import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

import requests

from config import HEADERS


MATCH_ID = "U3RX1Dxg"

# Проверяем несколько вероятных лент:
# 0  — сегодня;
# -1 — вчера;
# 3  — все события;
# 4  — LIVE-события.
FEEDS = [
    "f_3_0_3_ru_1",
    "f_3_0_4_ru_1",
    "f_3_-1_3_ru_1",
    "f_3_-1_4_ru_1",
]


for feed in FEEDS:

    url = (
        "https://local-ruua.flashscore.ninja/"
        f"32/x/feed/{feed}"
    )

    print("=" * 70)
    print("Проверяем feed:", feed)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20,
        )

        print("HTTP:", response.status_code)
        print("Размер ответа:", len(response.text))

        if MATCH_ID in response.text:
            print("✅ МАТЧ НАЙДЕН:", MATCH_ID)

            position = response.text.find(MATCH_ID)

            # Показываем фрагмент сырого ответа вокруг ID
            start = max(0, position - 300)
            end = position + 1500

            print(response.text[start:end])

        else:
            print("❌ Матч не найден")

    except requests.RequestException as error:
        print("Ошибка запроса:", error)