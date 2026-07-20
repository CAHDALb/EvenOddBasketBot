"""
confidence.py

Расчёт уровня доверия к Signal Score.

Confidence не оценивает вероятность выигрыша сигнала
и не заменяет Signal Score.

Его задача — показать, насколько надёжны данные,
на основании которых рассчитана историческая оценка.

Confidence учитывает:

1. минимальный размер выборки;
2. средний размер выборки;
3. полноту статистических данных;
4. равномерность доступных выборок.

Результат рассчитывается по шкале от 0 до 100.
"""

from typing import Any


# ------------------------------------------------------------
# Безопасное преобразование значений
# ------------------------------------------------------------

def safe_int(value: Any) -> int:
    """
    Безопасно преобразует значение в целое число.

    При ошибке возвращает 0.
    """

    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def safe_float(value: Any) -> float:
    """
    Безопасно преобразует значение в число float.

    При ошибке возвращает 0.0.
    """

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------
# Проверка структуры паспорта
# ------------------------------------------------------------

def validate_confidence_input(passport: Any) -> None:
    """
    Проверяет наличие разделов, необходимых
    для расчёта Confidence.

    При отсутствии обязательных данных выбрасывает ValueError.
    """

    if not isinstance(passport, dict):
        raise ValueError(
            "Для расчёта Confidence паспорт должен быть словарём."
        )

    required_sections = {
        "country",
        "league",
        "match_type",
    }

    missing_sections = required_sections - set(passport.keys())

    if missing_sections:
        raise ValueError(
            "В паспорте отсутствуют разделы: "
            + ", ".join(sorted(missing_sections))
        )

    for section_name in required_sections:
        if not isinstance(passport[section_name], dict):
            raise ValueError(
                f"Раздел {section_name} должен быть словарём."
            )


# ------------------------------------------------------------
# Получение размеров выборок
# ------------------------------------------------------------

def get_sample_totals(passport: dict) -> list[int]:
    """
    Возвращает размеры выборок:

    - страны;
    - лиги;
    - категории матча.
    """

    return [
        safe_int(passport["country"].get("total")),
        safe_int(passport["league"].get("total")),
        safe_int(passport["match_type"].get("total")),
    ]


# ------------------------------------------------------------
# Оценка минимальной выборки
# ------------------------------------------------------------

def calculate_minimum_sample_points(passport: dict) -> dict:
    """
    Рассчитывает баллы по самой маленькой выборке.

    Максимум: 50 баллов.

    Самая маленькая выборка важна потому, что итоговая
    аналитика не должна считаться надёжной, если хотя бы
    один из её компонентов основан на малом числе сигналов.
    """

    totals = get_sample_totals(passport)
    minimum_total = min(totals)

    if minimum_total < 10:
        points = 0
        reason = (
            f"Минимальная выборка составляет только "
            f"{minimum_total} завершённых сигналов."
        )

    elif minimum_total < 25:
        points = 10
        reason = (
            f"Минимальная выборка равна {minimum_total}. "
            "Данных пока немного."
        )

    elif minimum_total < 50:
        points = 25
        reason = (
            f"Минимальная выборка равна {minimum_total}. "
            "Данных достаточно для предварительной оценки."
        )

    elif minimum_total < 100:
        points = 40
        reason = (
            f"Минимальная выборка равна {minimum_total}. "
            "Статистическая база уже достаточно крупная."
        )

    else:
        points = 50
        reason = (
            f"Минимальная выборка равна {minimum_total}. "
            "Все компоненты основаны на крупной статистике."
        )

    return {
        "name": "Минимальная выборка",
        "points": points,
        "max_points": 50,
        "minimum_total": minimum_total,
        "reason": reason,
    }


# ------------------------------------------------------------
# Оценка среднего размера выборок
# ------------------------------------------------------------

def calculate_average_sample_points(passport: dict) -> dict:
    """
    Рассчитывает баллы по среднему размеру выборок.

    Максимум: 25 баллов.
    """

    totals = get_sample_totals(passport)
    average_total = sum(totals) / len(totals)

    if average_total < 10:
        points = 0

    elif average_total < 25:
        points = 5

    elif average_total < 50:
        points = 10

    elif average_total < 100:
        points = 18

    else:
        points = 25

    return {
        "name": "Средний размер выборки",
        "points": points,
        "max_points": 25,
        "average_total": round(average_total, 2),
        "reason": (
            "Средний размер выборок страны, лиги "
            f"и категории: {average_total:.2f}."
        ),
    }


# ------------------------------------------------------------
# Проверка полноты статистики
# ------------------------------------------------------------

def calculate_data_completeness_points(passport: dict) -> dict:
    """
    Проверяет наличие основных статистических полей.

    Для каждого раздела проверяются:

    - total;
    - roi.

    Всего проверяется 6 значений.

    Максимум: 15 баллов.
    """

    section_names = [
        "country",
        "league",
        "match_type",
    ]

    required_fields = [
        "total",
        "roi",
    ]

    completed_fields = 0
    total_fields = len(section_names) * len(required_fields)

    missing_fields: list[str] = []

    for section_name in section_names:
        statistics = passport[section_name]

        for field_name in required_fields:
            value = statistics.get(field_name)

            if value is not None and value != "":
                completed_fields += 1
            else:
                missing_fields.append(
                    f"{section_name}.{field_name}"
                )

    if total_fields == 0:
        completeness_percent = 0.0
    else:
        completeness_percent = (
            completed_fields / total_fields
        ) * 100

    points = round(
        completeness_percent / 100 * 15,
        2,
    )

    if missing_fields:
        reason = (
            f"Заполнено {completed_fields} из {total_fields} "
            "обязательных статистических значений. "
            "Отсутствуют: "
            + ", ".join(missing_fields)
            + "."
        )
    else:
        reason = (
            "Все обязательные статистические значения заполнены."
        )

    return {
        "name": "Полнота данных",
        "points": points,
        "max_points": 15,
        "completed_fields": completed_fields,
        "total_fields": total_fields,
        "completeness_percent": round(
            completeness_percent,
            2,
        ),
        "missing_fields": missing_fields,
        "reason": reason,
    }


# ------------------------------------------------------------
# Оценка равномерности выборок
# ------------------------------------------------------------

def calculate_sample_balance_points(passport: dict) -> dict:
    """
    Проверяет равномерность размеров выборок.

    Максимум: 10 баллов.

    Например:

        страна: 1000
        лига: 12
        категория: 500

    Такая статистика считается неравномерной, потому что
    один компонент значительно слабее остальных.
    """

    totals = get_sample_totals(passport)

    minimum_total = min(totals)
    maximum_total = max(totals)

    if maximum_total <= 0:
        balance_ratio = 0.0
        points = 0.0
    else:
        balance_ratio = minimum_total / maximum_total
        points = round(balance_ratio * 10, 2)

    return {
        "name": "Равномерность выборок",
        "points": points,
        "max_points": 10,
        "minimum_total": minimum_total,
        "maximum_total": maximum_total,
        "balance_ratio": round(balance_ratio, 4),
        "reason": (
            "Отношение минимальной выборки к максимальной: "
            f"{balance_ratio * 100:.2f}%."
        ),
    }


# ------------------------------------------------------------
# Определение уровня Confidence
# ------------------------------------------------------------

def get_confidence_level(confidence: float) -> dict:
    """
    Возвращает уровень доверия к аналитической оценке.

    Уровни Confidence не совпадают с уровнями Signal Score.
    """

    if confidence < 30:
        return {
            "code": "insufficient",
            "icon": "⚪",
            "title": "Недостаточно статистики",
        }

    if confidence < 55:
        return {
            "code": "bronze",
            "icon": "🟤",
            "title": "Начальный уровень доверия",
        }

    if confidence < 75:
        return {
            "code": "silver",
            "icon": "⚪",
            "title": "Средний уровень доверия",
        }

    return {
        "code": "gold",
        "icon": "🟡",
        "title": "Высокий уровень доверия",
    }


# ------------------------------------------------------------
# Основной расчёт Confidence
# ------------------------------------------------------------

def calculate_confidence(passport: dict) -> dict:
    """
    Рассчитывает итоговый Confidence от 0 до 100.

    Passport должен содержать:

    {
        "country": {...},
        "league": {...},
        "match_type": {...}
    }

    Возвращает:

    {
        "version": "0.1",
        "confidence": 68.5,
        "max_confidence": 100,
        "level": {...},
        "components": [...]
    }
    """

    validate_confidence_input(passport)

    components = [
        calculate_minimum_sample_points(passport),
        calculate_average_sample_points(passport),
        calculate_data_completeness_points(passport),
        calculate_sample_balance_points(passport),
    ]

    confidence = sum(
        safe_float(component["points"])
        for component in components
    )

    # Защита от выхода за диапазон 0–100
    confidence = max(
        0.0,
        min(confidence, 100.0),
    )

    confidence = round(confidence, 2)

    level = get_confidence_level(confidence)

    return {
        "version": "0.1",
        "confidence": confidence,
        "max_confidence": 100,
        "level": level,
        "components": components,

        # Confidence также не является вероятностью выигрыша
        "is_probability": False,

        "warning": (
            "Confidence показывает надёжность статистической "
            "базы, но не вероятность выигрыша отдельного сигнала."
        ),
    }