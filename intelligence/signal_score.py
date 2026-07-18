"""
===========================================================
EvenOddBasketBot

Файл:
intelligence/signal_score.py

Назначение:
Рассчитывает Signal Score по шкале от 0 до 100.

Важно:
Signal Score не является вероятностью выигрыша.

Он оценивает:
- качество исторической статистики;
- размер выборки;
- исторический ROI;
- надёжность доступных данных.

Версия:
Signal Score v0.1
===========================================================
"""


def safe_int(value):
    """
    Безопасно переводит значение в целое число.
    """

    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def safe_float(value):
    """
    Безопасно переводит значение в число float.
    """

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def calculate_country_points(statistics):
    """
    Рассчитывает баллы страны.

    Максимум: 20 баллов.
    """

    total = safe_int(statistics.get("total"))
    roi = safe_float(statistics.get("roi"))

    if total < 10:
        points = 0
        reason = (
            f"Только {total} завершённых сигналов. "
            "Минимум для оценки страны — 10."
        )

    elif roi < 0:
        points = 2
        reason = (
            f"Выборка: {total}. ROI отрицательный: {roi:+.2f}."
        )

    elif total >= 100 and roi > 0:
        points = 20
        reason = (
            f"Крупная выборка: {total}. "
            f"Положительный ROI: {roi:+.2f}."
        )

    elif total >= 50 and roi > 10:
        points = 15
        reason = (
            f"Выборка: {total}. Высокий ROI: {roi:+.2f}."
        )

    elif total >= 25 and roi >= 5:
        points = 10
        reason = (
            f"Выборка: {total}. ROI: {roi:+.2f}."
        )

    elif roi >= 0:
        points = 6
        reason = (
            f"Выборка: {total}. "
            f"ROI неотрицательный: {roi:+.2f}."
        )

    else:
        points = 0
        reason = "Недостаточно данных."

    return {
        "name": "Страна",
        "points": points,
        "max_points": 20,
        "total": total,
        "roi": roi,
        "reason": reason,
    }


def calculate_league_points(statistics):
    """
    Рассчитывает баллы лиги.

    Максимум: 35 баллов.
    """

    total = safe_int(statistics.get("total"))
    roi = safe_float(statistics.get("roi"))

    if total < 10:
        points = 0
        reason = (
            f"Только {total} завершённых сигналов. "
            "Минимум для оценки лиги — 10."
        )

    elif roi < 0:
        points = 3
        reason = (
            f"Выборка: {total}. ROI отрицательный: {roi:+.2f}."
        )

    elif total >= 100 and roi > 10:
        points = 35
        reason = (
            f"Крупная выборка: {total}. "
            f"Сильный ROI: {roi:+.2f}."
        )

    elif total >= 50 and roi >= 10:
        points = 25
        reason = (
            f"Выборка: {total}. Высокий ROI: {roi:+.2f}."
        )

    elif total >= 25 and roi >= 5:
        points = 15
        reason = (
            f"Выборка: {total}. ROI: {roi:+.2f}."
        )

    elif roi >= 0:
        points = 8
        reason = (
            f"Выборка: {total}. "
            f"ROI неотрицательный: {roi:+.2f}."
        )

    else:
        points = 0
        reason = "Недостаточно данных."

    return {
        "name": "Лига",
        "points": points,
        "max_points": 35,
        "total": total,
        "roi": roi,
        "reason": reason,
    }


def calculate_match_type_points(statistics):
    """
    Рассчитывает баллы категории матча.

    Максимум: 15 баллов.
    """

    total = safe_int(statistics.get("total"))
    roi = safe_float(statistics.get("roi"))

    if total < 20:
        points = 0
        reason = (
            f"Только {total} завершённых сигналов. "
            "Минимум для оценки категории — 20."
        )

    elif roi < 0:
        points = 2
        reason = (
            f"Выборка: {total}. ROI отрицательный: {roi:+.2f}."
        )

    elif total >= 100 and roi > 10:
        points = 15
        reason = (
            f"Крупная выборка: {total}. "
            f"Сильный ROI: {roi:+.2f}."
        )

    elif total >= 50 and roi >= 5:
        points = 10
        reason = (
            f"Выборка: {total}. ROI: {roi:+.2f}."
        )

    elif roi >= 0:
        points = 5
        reason = (
            f"Выборка: {total}. "
            f"ROI неотрицательный: {roi:+.2f}."
        )

    else:
        points = 0
        reason = "Недостаточно данных."

    return {
        "name": "Категория",
        "points": points,
        "max_points": 15,
        "total": total,
        "roi": roi,
        "reason": reason,
    }


def calculate_reliability_points(passport):
    """
    Оценивает надёжность выборки.

    Используется минимальная выборка среди:
    - страны;
    - лиги;
    - категории.

    Максимум: 20 баллов.
    """

    totals = [
        safe_int(passport["country"].get("total")),
        safe_int(passport["league"].get("total")),
        safe_int(passport["match_type"].get("total")),
    ]

    minimum_total = min(totals)

    if minimum_total < 10:
        points = 0
    elif minimum_total < 25:
        points = 5
    elif minimum_total < 50:
        points = 10
    elif minimum_total < 100:
        points = 15
    else:
        points = 20

    return {
        "name": "Надёжность выборки",
        "points": points,
        "max_points": 20,
        "minimum_total": minimum_total,
        "reason": (
            "Баллы рассчитаны по самой маленькой выборке: "
            f"{minimum_total} завершённых сигналов."
        ),
    }


def calculate_overall_roi_points(passport):
    """
    Рассчитывает баллы общего ROI.

    Используется средний ROI:
    - страны;
    - лиги;
    - категории.

    Максимум: 10 баллов.
    """

    roi_values = [
        safe_float(passport["country"].get("roi")),
        safe_float(passport["league"].get("roi")),
        safe_float(passport["match_type"].get("roi")),
    ]

    average_roi = sum(roi_values) / len(roi_values)

    if average_roi < -10:
        points = 0
    elif average_roi < 0:
        points = 2
    elif average_roi < 5:
        points = 5
    elif average_roi < 10:
        points = 8
    else:
        points = 10

    return {
        "name": "Общий ROI",
        "points": points,
        "max_points": 10,
        "average_roi": average_roi,
        "reason": (
            "Средний ROI страны, лиги и категории: "
            f"{average_roi:+.2f}."
        ),
    }


def get_score_level(score):
    """
    Возвращает текстовый уровень Signal Score.
    """

    if score < 30:
        return {
            "code": "insufficient",
            "icon": "⚪",
            "title": "Недостаточно данных или слабая история",
        }

    if score < 50:
        return {
            "code": "low",
            "icon": "🔴",
            "title": "Низкая историческая оценка",
        }

    if score < 65:
        return {
            "code": "medium",
            "icon": "🟡",
            "title": "Средняя историческая оценка",
        }

    if score < 80:
        return {
            "code": "good",
            "icon": "🟢",
            "title": "Хорошая историческая оценка",
        }

    return {
        "code": "strong",
        "icon": "🟢",
        "title": "Сильная историческая оценка",
    }


def calculate_signal_score(passport):
    """
    Рассчитывает полный Signal Score.

    passport должен содержать:

    {
        "country": {...},
        "league": {...},
        "match_type": {...}
    }

    Возвращает:
    - итоговый Score;
    - уровень;
    - подробное объяснение каждого компонента.
    """

    required_keys = {
        "country",
        "league",
        "match_type",
    }

    missing_keys = required_keys - set(passport)

    if missing_keys:
        raise ValueError(
            "В паспорте сигнала отсутствуют поля: "
            + ", ".join(sorted(missing_keys))
        )

    components = [
        calculate_country_points(
            passport["country"]
        ),
        calculate_league_points(
            passport["league"]
        ),
        calculate_match_type_points(
            passport["match_type"]
        ),
        calculate_reliability_points(passport),
        calculate_overall_roi_points(passport),
    ]

    score = sum(
        component["points"]
        for component in components
    )

    # Дополнительная защита
    score = max(0, min(score, 100))

    level = get_score_level(score)

    return {
        "version": "0.1",
        "score": score,
        "max_score": 100,
        "level": level,
        "components": components,
        "is_probability": False,
        "warning": (
            "Signal Score не является вероятностью выигрыша "
            "и пока не используется для фильтрации сигналов."
        ),
    }