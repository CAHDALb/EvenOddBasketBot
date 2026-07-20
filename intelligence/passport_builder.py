"""
passport_builder.py

Сборщик единого Signal Passport.

Этот модуль получает данные о матче и уже рассчитанную
аналитическую статистику, после чего собирает их в одну
стандартную структуру паспорта.

Важно:
    builder не должен самостоятельно обращаться к базе данных.

Его задача:
    1. получить готовые данные;
    2. привести их к единому формату;
    3. сформировать Signal Passport;
    4. вернуть готовый словарь.
"""
from intelligence.passport_model import create_passport
from intelligence.signal_score import calculate_signal_score
from intelligence.confidence import calculate_confidence
from intelligence.explanation import build_recommendation
from intelligence.stability import calculate_stability
from copy import deepcopy
from datetime import datetime
from typing import Any, Optional




# ------------------------------------------------------------
# Допустимые уровни надёжности паспорта
# ------------------------------------------------------------

ALLOWED_LEVELS = {
    "insufficient",
    "low",
    "medium",
    "good",
    "strong",
}


# ------------------------------------------------------------
# Вспомогательные функции
# ------------------------------------------------------------

def _safe_dict(value: Any) -> dict:
    """
    Безопасно приводит значение к словарю.

    Если нам передали словарь, возвращается его копия.
    Во всех остальных случаях возвращается пустой словарь.

    Это защищает паспорт от случайного значения None,
    строки, списка или другого неподходящего типа.
    """

    if isinstance(value, dict):
        return deepcopy(value)

    return {}


def _safe_number(
    value: Any,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> Optional[float]:
    """
    Безопасно преобразует значение в число.

    Используется для Signal Score и Confidence.

    Аргументы:
        value:
            Значение, которое нужно преобразовать.

        minimum:
            Минимально допустимое значение.

        maximum:
            Максимально допустимое значение.

    Возвращает:
        float:
            Корректное число в допустимом диапазоне.

        None:
            Если значение отсутствует или не является числом.
    """

    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    # Не разрешаем значению выйти за допустимые границы
    number = max(minimum, min(maximum, number))

    return round(number, 2)


def _safe_text(value: Any) -> Optional[str]:
    """
    Безопасно преобразует значение в текст.

    Пустые строки считаются отсутствующим значением
    и заменяются на None.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def _normalize_level(level: Any) -> Optional[str]:
    """
    Проверяет уровень исторической оценки сигнала.

    Допустимые значения:
        insufficient
        low
        medium
        good
        strong
    """

    normalized_level = _safe_text(level)

    if normalized_level is None:
        return None

    normalized_level = normalized_level.lower()

    if normalized_level not in ALLOWED_LEVELS:
        return None

    return normalized_level


# ------------------------------------------------------------
# Основная функция построения паспорта
# ------------------------------------------------------------

def build_signal_passport(
    *,
    country_stats: Optional[dict] = None,
    league_stats: Optional[dict] = None,
    match_type_stats: Optional[dict] = None,
    signal_score: Any = None,
    confidence: Any = None,
    level: Any = None,
    recommendation: Any = None,
    history: Optional[dict] = None,
    history_results: Optional[list] = None,
    match_data: Optional[dict] = None,
) -> dict:
    """
    Создаёт заполненный Signal Passport.

    Все параметры передаются по имени. Это сделано специально,
    чтобы при вызове функции было понятно, какие именно данные
    мы передаём.

    Пример:

        passport = build_signal_passport(
            country_stats=country_stats,
            league_stats=league_stats,
            match_type_stats=match_type_stats,
            signal_score=82.5,
            confidence=74.0,
            level="silver",
            recommendation="Сигнал выше среднего",
        )

    Аргументы:
        country_stats:
            Статистика по стране.

        league_stats:
            Статистика по лиге.

        match_type_stats:
            Статистика по типу матча:
            мужчины, женщины, молодёжные и так далее.

        signal_score:
            Историческая оценка сигнала от 0 до 100.

        confidence:
            Уровень статистического доверия от 0 до 100%.

        level:
            Уровень надёжности:
            insufficient, bronze, silver или gold.

        recommendation:
            Итоговая текстовая рекомендация.

        history:
            Дополнительная история:
            серии, последние результаты, ROI и другие данные.

        match_data:
            Основные сведения о матче.
            Пока они сохраняются внутри meta,
            чтобы не менять версию структуры паспорта.

    Возвращает:
        dict:
            Полностью сформированный Signal Passport.
    """

    # Создаём новый паспорт только через passport_model.py
    passport = create_passport()

    # --------------------------------------------------------
    # Добавляем историческую статистику
    # --------------------------------------------------------

    passport["country"] = _safe_dict(country_stats)
    passport["league"] = _safe_dict(league_stats)
    passport["match_type"] = _safe_dict(match_type_stats)

    # --------------------------------------------------------
    # Если Signal Score не передан вручную,
    # рассчитываем его автоматически.
    # --------------------------------------------------------

    if signal_score is None:

        # --------------------------------------------------------
        # Рассчитываем Signal Score
        # --------------------------------------------------------

        score_result = calculate_signal_score(passport)

        passport["signal_score"] = score_result["score"]
        passport["level"] = score_result["level"]["code"]

        passport["meta"]["signal_score_analysis"] = (
            score_result
        )

        # --------------------------------------------------------
        # Рассчитываем Confidence
        # --------------------------------------------------------

        if confidence is None:
            confidence_result = calculate_confidence(passport)

            passport["confidence"] = (
                confidence_result["confidence"]
            )

            passport["meta"]["confidence_analysis"] = (
                confidence_result
            )
        else:
            passport["confidence"] = _safe_number(
                confidence
            )
        # --------------------------------------------------------
        # Рассчитываем Confidence
        # --------------------------------------------------------

        if confidence is None:
            confidence_result = calculate_confidence(passport)

            passport["confidence"] = (
                confidence_result["confidence"]
            )

            passport["meta"]["confidence_analysis"] = (
                confidence_result
            )
        else:
            passport["confidence"] = _safe_number(
                confidence
            )

        # --------------------------------------------------------
        # Рассчитываем Stability
        # --------------------------------------------------------

        stability_result = calculate_stability(
            history_results
        )

        passport["stability"] = (
            stability_result["stability"]
        )

        passport["meta"]["stability_analysis"] = (
            stability_result
        )

        # --------------------------------------------------------
        # Формируем аналитическую рекомендацию
        #
        # Важно:
        # Recommendation рассчитывается только после Confidence.
        # Она не блокирует отправку сигнала.
        # --------------------------------------------------------

        if recommendation is None:
            recommendation_result = build_recommendation(
                passport
            )

            passport["recommendation"] = (
                recommendation_result["summary"]
            )

            passport["meta"]["recommendation_analysis"] = (
                recommendation_result
            )
        else:
            passport["recommendation"] = _safe_text(
                recommendation
            )

    else:
        passport["signal_score"] = _safe_number(signal_score)
        passport["confidence"] = _safe_number(confidence)
        passport["level"] = _normalize_level(level)
        passport["recommendation"] = _safe_text(recommendation)

    # --------------------------------------------------------
    # Добавляем дополнительную историю
    # --------------------------------------------------------

    passport["history"] = _safe_dict(history)

    # --------------------------------------------------------
    # Добавляем сведения о матче
    # --------------------------------------------------------
    #
    # В текущей версии паспорта 1.0 отдельного блока match нет.
    # Поэтому временно сохраняем сведения о матче внутри meta.
    #
    # Позже, когда обновим паспорт до версии 1.1,
    # мы вынесем эти данные в отдельный раздел "match".
    # --------------------------------------------------------

    passport["meta"]["match"] = _safe_dict(match_data)

    # Обновляем время окончательной сборки паспорта
    passport["meta"]["built_at"] = datetime.now()

    return passport


# ------------------------------------------------------------
# Проверка корректности структуры паспорта
# ------------------------------------------------------------

def validate_signal_passport(passport: Any) -> tuple[bool, list[str]]:
    """
    Проверяет, соответствует ли объект структуре Signal Passport.

    Возвращает:
        tuple:
            Первый элемент:
                True — паспорт корректный.
                False — паспорт содержит ошибки.

            Второй элемент:
                список найденных ошибок.
    """

    errors: list[str] = []

    # Паспорт обязательно должен быть словарём
    if not isinstance(passport, dict):
        return False, ["Signal Passport должен быть словарём."]

    # Обязательные поля верхнего уровня
    required_fields = {
        "version",
        "country",
        "league",
        "match_type",
        "signal_score",
        "confidence",
        "level",
        "recommendation",
        "history",
        "meta",
    }

    missing_fields = required_fields - set(passport.keys())

    for field_name in sorted(missing_fields):
        errors.append(
            f"В паспорте отсутствует обязательное поле: {field_name}"
        )

    # Если поле отсутствует, дальнейшая проверка его типа не нужна
    if "country" in passport and not isinstance(passport["country"], dict):
        errors.append("Поле country должно быть словарём.")

    if "league" in passport and not isinstance(passport["league"], dict):
        errors.append("Поле league должно быть словарём.")

    if (
        "match_type" in passport
        and not isinstance(passport["match_type"], dict)
    ):
        errors.append("Поле match_type должно быть словарём.")

    if "history" in passport and not isinstance(passport["history"], dict):
        errors.append("Поле history должно быть словарём.")

    if "meta" in passport and not isinstance(passport["meta"], dict):
        errors.append("Поле meta должно быть словарём.")

    # Проверяем диапазон Signal Score
    signal_score = passport.get("signal_score")

    if signal_score is not None:
        if not isinstance(signal_score, (int, float)):
            errors.append("Поле signal_score должно быть числом или None.")
        elif not 0 <= signal_score <= 100:
            errors.append(
                "Поле signal_score должно находиться в диапазоне от 0 до 100."
            )

    # Проверяем диапазон Confidence
    confidence = passport.get("confidence")

    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            errors.append("Поле confidence должно быть числом или None.")
        elif not 0 <= confidence <= 100:
            errors.append(
                "Поле confidence должно находиться в диапазоне от 0 до 100."
            )

    # Проверяем уровень надёжности
    level = passport.get("level")

    if level is not None and level not in ALLOWED_LEVELS:
        errors.append(
            "Поле level должно иметь одно из значений: "
            "insufficient, low, medium, good или strong."
        )

    return len(errors) == 0, errors