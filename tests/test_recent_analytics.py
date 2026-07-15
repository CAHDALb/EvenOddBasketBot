import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from analytics import (
    get_recent_statistics,
    get_risk_indicator,
)


recent = get_recent_statistics(limit=10)
risk = get_risk_indicator(recent)

print("=" * 55)
print("Последние результаты стратегии")
print("=" * 55)

if recent["total"] == 0:
    print("Завершённых сигналов пока нет.")
else:
    print("История       :", recent["history_line"])
    print("Всего         :", recent["total"])
    print("WIN           :", recent["wins"])
    print("LOSE          :", recent["loses"])
    print("Проходимость  :", f"{recent['win_rate']:.2f}%")

    streak = recent["streak"]

    if streak["result"] is not None:
        streak_name = (
            "WIN"
            if streak["result"] == "win"
            else "LOSE"
        )

        print(
            "Текущая серия:",
            streak["length"],
            streak_name,
        )

print("-" * 55)
print(
    "Индикатор     :",
    risk["icon"],
    risk["title"],
)
print("Комментарий   :", risk["message"])
print("=" * 55)