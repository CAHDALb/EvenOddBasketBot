"""
explanation.py

Формирование итоговой аналитической рекомендации
на основании Signal Score, Confidence и исторической статистики.

Модуль ничего не рассчитывает заново.

Он получает уже готовый Signal Passport и объясняет:

- насколько исторически силён сигнал;
- насколько надёжна статистическая база;
- какие у сигнала есть преимущества;
- какие присутствуют предупреждения;
- как следует относиться к сигналу.

Важно:
    рекомендация не является гарантией выигрыша
    и не должна восприниматься как точная вероятность.
"""

from typing import Any


# ------------------------------------------------------------
# Безопасное получение числовых значений
# ------------------------------------------------------------

def safe_float(value: Any) -> float:
    """
    Безопасно преобразует значение в float.

    При ошибке возвращает 0.0.
    """

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    """
    Безопасно преобразует значение в int.

    При ошибке возвращает 0.
    """

    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


# ------------------------------------------------------------
# Проверка входного паспорта
# ------------------------------------------------------------

def validate_recommendation_input(passport: Any) -> None:
    """
    Проверяет наличие данных, необходимых
    для формирования рекомендации.
    """

    if not isinstance(passport, dict):
        raise ValueError(
            "Для формирования рекомендации паспорт "
            "должен быть словарём."
        )

    required_fields = {
        "country",
        "league",
        "match_type",
        "signal_score",
        "confidence",
        "meta",
    }

    missing_fields = required_fields - set(passport.keys())

    if missing_fields:
        raise ValueError(
            "В паспорте отсутствуют обязательные поля: "
            + ", ".join(sorted(missing_fields))
        )


# ------------------------------------------------------------
# Получение уровня Confidence
# ------------------------------------------------------------

def get_confidence_level_code(passport: dict) -> str:
    """
    Возвращает код уровня Confidence.

    Основной источник:
        meta.confidence_analysis.level.code

    Если подробного анализа нет, уровень определяется
    непосредственно по числовому Confidence.
    """

    meta = passport.get("meta", {})

    confidence_analysis = meta.get(
        "confidence_analysis",
        {},
    )

    level = confidence_analysis.get("level", {})

    level_code = level.get("code")

    if level_code:
        return str(level_code)

    confidence = safe_float(
        passport.get("confidence")
    )

    if confidence < 30:
        return "insufficient"

    if confidence < 55:
        return "bronze"

    if confidence < 75:
        return "silver"

    return "gold"


# ------------------------------------------------------------
# Формирование преимуществ
# ------------------------------------------------------------

def build_advantages(passport: dict) -> list[str]:
    """
    Формирует список сильных сторон сигнала.
    """

    advantages: list[str] = []

    country = passport.get("country", {})
    league = passport.get("league", {})
    match_type = passport.get("match_type", {})

    country_roi = safe_float(country.get("roi"))
    league_roi = safe_float(league.get("roi"))
    match_type_roi = safe_float(match_type.get("roi"))

    country_total = safe_int(country.get("total"))
    league_total = safe_int(league.get("total"))
    match_type_total = safe_int(
        match_type.get("total")
    )

    signal_score = safe_float(
        passport.get("signal_score")
    )

    confidence = safe_float(
        passport.get("confidence")
    )

    stability = safe_float(
        passport.get("stability")
    )

    # --------------------------------------------------------
    # Положительная статистика страны
    # --------------------------------------------------------

    if country_roi >= 10:
        advantages.append(
            f"Страна показывает высокий ROI: "
            f"{country_roi:+.2f}%."
        )
    elif country_roi > 0:
        advantages.append(
            f"Страна показывает положительный ROI: "
            f"{country_roi:+.2f}%."
        )

    # --------------------------------------------------------
    # Положительная статистика лиги
    # --------------------------------------------------------

    if league_roi >= 10:
        advantages.append(
            f"Лига показывает высокий ROI: "
            f"{league_roi:+.2f}%."
        )
    elif league_roi > 0:
        advantages.append(
            f"Лига показывает положительный ROI: "
            f"{league_roi:+.2f}%."
        )

    # --------------------------------------------------------
    # Положительная статистика категории
    # --------------------------------------------------------

    if match_type_roi >= 10:
        advantages.append(
            f"Категория матча показывает высокий ROI: "
            f"{match_type_roi:+.2f}%."
        )
    elif match_type_roi > 0:
        advantages.append(
            f"Категория матча показывает положительный ROI: "
            f"{match_type_roi:+.2f}%."
        )

    # --------------------------------------------------------
    # Размер статистической базы
    # --------------------------------------------------------

    minimum_total = min(
        country_total,
        league_total,
        match_type_total,
    )

    if minimum_total >= 100:
        advantages.append(
            "Все аналитические компоненты основаны "
            "минимум на 100 завершённых сигналах."
        )
    elif minimum_total >= 50:
        advantages.append(
            "Все основные выборки содержат не менее "
            "50 завершённых сигналов."
        )

    # --------------------------------------------------------
    # Итоговые оценки
    # --------------------------------------------------------

    if signal_score >= 80:
        advantages.append(
            "Signal Score указывает на сильную "
            "историческую оценку."
        )
    elif signal_score >= 65:
        advantages.append(
            "Signal Score указывает на хорошую "
            "историческую оценку."
        )

    if confidence >= 75:
        advantages.append(
            "Статистическая база имеет высокий "
            "уровень доверия."
        )

    return advantages


# ------------------------------------------------------------
# Формирование предупреждений
# ------------------------------------------------------------

def build_warnings(passport: dict) -> list[str]:
    """
    Формирует список слабых сторон и рисков сигнала.
    """

    warnings: list[str] = []

    country = passport.get("country", {})
    league = passport.get("league", {})
    match_type = passport.get("match_type", {})

    country_roi = safe_float(country.get("roi"))
    league_roi = safe_float(league.get("roi"))
    match_type_roi = safe_float(match_type.get("roi"))

    country_total = safe_int(country.get("total"))
    league_total = safe_int(league.get("total"))
    match_type_total = safe_int(
        match_type.get("total")
    )

    signal_score = safe_float(
        passport.get("signal_score")
    )

    stability = safe_float(
        passport.get("stability")
    )

    confidence = safe_float(
        passport.get("confidence")
    )

    # --------------------------------------------------------
    # Отрицательный ROI
    # --------------------------------------------------------

    if country_roi < 0:
        warnings.append(
            f"Страна имеет отрицательный ROI: "
            f"{country_roi:+.2f}%."
        )

    if league_roi < 0:
        warnings.append(
            f"Лига имеет отрицательный ROI: "
            f"{league_roi:+.2f}%."
        )

    if match_type_roi < 0:
        warnings.append(
            f"Категория матча имеет отрицательный ROI: "
            f"{match_type_roi:+.2f}%."
        )

    # --------------------------------------------------------
    # Малые выборки
    # --------------------------------------------------------

    sample_sections = [
        ("страны", country_total),
        ("лиги", league_total),
        ("категории", match_type_total),
    ]

    for section_title, total in sample_sections:
        if total < 10:
            warnings.append(
                f"Выборка {section_title} содержит только "
                f"{total} завершённых сигналов."
            )
        elif total < 25:
            warnings.append(
                f"Выборка {section_title} пока небольшая: "
                f"{total} завершённых сигналов."
            )

    minimum_total = min(
        country_total,
        league_total,
        match_type_total,
    )

    maximum_total = max(
        country_total,
        league_total,
        match_type_total,
    )

    if maximum_total > 0:
        balance_ratio = minimum_total / maximum_total

        if balance_ratio < 0.25:
            warnings.append(
                "Размеры статистических выборок сильно "
                "различаются между собой."
            )
        elif balance_ratio < 0.50:
            warnings.append(
                "Статистические выборки распределены "
                "не вполне равномерно."
            )

    # --------------------------------------------------------
    # Итоговые показатели
    # --------------------------------------------------------

    if signal_score < 30:
        warnings.append(
            "Signal Score пока недостаточен для "
            "положительной исторической оценки."
        )
    elif signal_score < 50:
        warnings.append(
            "Signal Score указывает на слабую "
            "историческую статистику."
        )

    if confidence < 30:
        warnings.append(
            "Статистики недостаточно для уверенного вывода."
        )
    elif confidence < 55:
        warnings.append(
            "Уровень доверия к статистической базе "
            "остаётся невысоким."
        )

    return warnings


# ------------------------------------------------------------
# Определение решения
# ------------------------------------------------------------

def determine_action(
    signal_score: float,
    confidence: float,
    stability: float,
) -> dict:
    """
    Определяет итоговое действие системы.

    Действие пока является аналитической категорией,
    а не автоматическим разрешением поставить деньги.
    """

    if signal_score < 30 or confidence < 30:
        return {
            "code": "skip",
            "title": "Пропустить",
            "icon": "⛔",
        }

    if signal_score < 50 or confidence < 55:
        return {
            "code": "caution",
            "title": "Только осторожное наблюдение",
            "icon": "🔴",
        }

    if signal_score < 65 or confidence < 75:
        return {
            "code": "consider",
            "title": "Можно рассматривать",
            "icon": "🟡",
        }

    if signal_score < 80:
        return {
            "code": "approve",
            "title": "Положительная рекомендация",
            "icon": "🟢",
        }

    return {
        "code": "priority",
        "title": "Высокий аналитический приоритет",
        "icon": "⭐",
    }


# ------------------------------------------------------------
# Определение риска
# ------------------------------------------------------------

def determine_risk(
    signal_score: float,
    confidence: float,
    stability: float,
) -> dict:
    """
    Определяет аналитический уровень риска.

    Настоящую стабильность и просадку мы добавим позднее.
    Поэтому текущая оценка риска считается предварительной.
    """

    weakest_value = min(
        signal_score,
        confidence,
    )

    if weakest_value < 30:
        return {
            "code": "very_high",
            "title": "Очень высокий риск",
        }

    if weakest_value < 50:
        return {
            "code": "high",
            "title": "Высокий риск",
        }

    if weakest_value < 65:
        return {
            "code": "moderate",
            "title": "Умеренный риск",
        }

    if weakest_value < 80:
        return {
            "code": "controlled",
            "title": "Контролируемый риск",
        }

    return {
        "code": "reduced",
        "title": "Пониженный аналитический риск",
    }


# ------------------------------------------------------------
# Расчёт приоритета
# ------------------------------------------------------------

def calculate_priority(
    signal_score: float,
    confidence: float,
    stability: float,
) -> float:
    """
    Рассчитывает итоговый аналитический приоритет.

    Signal Score — 40%
    Confidence  — 35%
    Stability   — 25%

    Итоговый показатель не является вероятностью выигрыша.
    """

    priority = (
        signal_score * 0.40
        + confidence * 0.35
        + stability * 0.25
    )

    priority = max(
        0.0,
        min(priority, 100.0),
    )

    return round(priority, 2)


# ------------------------------------------------------------
# Формирование итогового текста
# ------------------------------------------------------------

def build_summary(
    action_code: str,
    signal_score: float,
    confidence: float,
) -> str:
    """
    Формирует короткое понятное заключение.
    """

    if action_code == "skip":
        return (
            "Исторических данных или их качества пока "
            "недостаточно. Сигнал рекомендуется пропустить."
        )

    if action_code == "caution":
        return (
            "Сигнал имеет слабую либо недостаточно надёжную "
            "историческую основу. Увеличение размера ставки "
            "не рекомендуется."
        )

    if action_code == "consider":
        return (
            "Сигнал можно рассматривать, но статистическая "
            "основа пока не позволяет повышать размер ставки."
        )

    if action_code == "approve":
        return (
            "Историческая оценка и надёжность данных "
            "находятся на хорошем уровне. Допустим обычный "
            "размер ставки в рамках выбранного риск-менеджмента."
        )

    return (
        "Сигнал имеет высокий аналитический приоритет. "
        "Однако даже высокая оценка не исключает проигрыш "
        "отдельной ставки."
    )


# ------------------------------------------------------------
# Основная функция Recommendation Engine
# ------------------------------------------------------------

def build_recommendation(passport: dict) -> dict:
    """
    Формирует полную рекомендацию по Signal Passport.

    Возвращает:

    {
        "version": "0.1",
        "action": {...},
        "risk": {...},
        "priority": 60.0,
        "summary": "...",
        "advantages": [...],
        "warnings": [...],
        "signal_score": 58,
        "confidence": 63,
        "confidence_level": "silver"
    }
    """

    validate_recommendation_input(passport)

    signal_score = safe_float(
        passport.get("signal_score")
    )

    confidence = safe_float(
        passport.get("confidence")
    )

    stability = safe_float(
        passport.get("stability")
    )

    action = determine_action(
        signal_score=signal_score,
        confidence=confidence,
        stability=stability,
    )

    risk = determine_risk(
        signal_score=signal_score,
        confidence=confidence,
        stability=stability,
    )

    priority = calculate_priority(
        signal_score=signal_score,
        confidence=confidence,
        stability=stability,
    )

    advantages = build_advantages(passport)
    warnings = build_warnings(passport)

    summary = build_summary(
        action_code=action["code"],
        signal_score=signal_score,
        confidence=confidence,
    )

    confidence_level = get_confidence_level_code(
        passport
    )

    return {
        "version": "0.1",
        "action": action,
        "risk": risk,
        "priority": priority,
        "summary": summary,
        "advantages": advantages,
        "warnings": warnings,
        "signal_score": signal_score,
        "stability": stability,
        "confidence": confidence,
        "confidence_level": confidence_level,
        "is_probability": False,
        "warning": (
            "Рекомендация основана на исторической "
            "статистике и не гарантирует выигрыш."
        ),
    }