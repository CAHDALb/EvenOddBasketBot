"""
Модуль оценки стабильности истории сигналов.

Stability не оценивает вероятность выигрыша
и не определяет прибыльность стратегии.

Он анализирует характер последовательности результатов:

- максимальную серию поражений;
- максимальную условную просадку;
- длительность восстановления;
- равномерность результатов;
- концентрацию выигрышей.

Для моделирования используется условная фиксированная ставка:

    WIN  = +1 единица
    LOSE = -1 единица

Коэффициенты и реальные размеры ставок здесь не учитываются.
"""

from typing import Any, Optional


# ------------------------------------------------------------
# Настройки модуля
# ------------------------------------------------------------

STABILITY_VERSION = "0.1"

MIN_HISTORY_SIZE = 10

VALID_WIN_VALUES = {
    "WIN",
    "W",
    "WON",
    "ПОБЕДА",
    "ВЫИГРЫШ",
}

VALID_LOSE_VALUES = {
    "LOSE",
    "LOSS",
    "L",
    "LOST",
    "ПОРАЖЕНИЕ",
    "ПРОИГРЫШ",
}


# ------------------------------------------------------------
# Безопасная подготовка истории
# ------------------------------------------------------------

def _normalize_result(value: Any) -> Optional[str]:
    """
    Преобразует один результат к стандартному виду.

    Возвращает:
        "WIN"
        "LOSE"
        None — если значение не удалось распознать.
    """

    if value is None:
        return None

    # Булевы значения:
    # True  -> WIN
    # False -> LOSE
    if isinstance(value, bool):
        return "WIN" if value else "LOSE"

    text = str(value).strip().upper()

    if text in VALID_WIN_VALUES:
        return "WIN"

    if text in VALID_LOSE_VALUES:
        return "LOSE"

    return None


def _normalize_history(history: Any) -> list[str]:
    """
    Подготавливает историю результатов.

    Некорректные значения пропускаются.
    """

    if not isinstance(history, (list, tuple)):
        return []

    normalized_history = []

    for value in history:
        normalized_result = _normalize_result(value)

        if normalized_result is not None:
            normalized_history.append(normalized_result)

    return normalized_history


# ------------------------------------------------------------
# Расчёт серий
# ------------------------------------------------------------

def _calculate_streaks(history: list[str]) -> dict:
    """
    Рассчитывает победные и проигрышные серии.
    """

    if not history:
        return {
            "max_winning_streak": 0,
            "max_losing_streak": 0,
            "current_streak": 0,
            "current_streak_type": None,
            "losing_streaks": [],
            "winning_streaks": [],
        }

    max_winning_streak = 0
    max_losing_streak = 0

    current_type = history[0]
    current_length = 0

    winning_streaks = []
    losing_streaks = []

    for result in history:
        if result == current_type:
            current_length += 1
        else:
            if current_type == "WIN":
                winning_streaks.append(current_length)
                max_winning_streak = max(
                    max_winning_streak,
                    current_length,
                )
            else:
                losing_streaks.append(current_length)
                max_losing_streak = max(
                    max_losing_streak,
                    current_length,
                )

            current_type = result
            current_length = 1

    # Добавляем последнюю серию
    if current_type == "WIN":
        winning_streaks.append(current_length)
        max_winning_streak = max(
            max_winning_streak,
            current_length,
        )
    else:
        losing_streaks.append(current_length)
        max_losing_streak = max(
            max_losing_streak,
            current_length,
        )

    return {
        "max_winning_streak": max_winning_streak,
        "max_losing_streak": max_losing_streak,
        "current_streak": current_length,
        "current_streak_type": current_type,
        "winning_streaks": winning_streaks,
        "losing_streaks": losing_streaks,
    }


# ------------------------------------------------------------
# Расчёт условной кривой банка
# ------------------------------------------------------------

def _build_equity_curve(history: list[str]) -> list[int]:
    """
    Строит условную кривую результата.

    WIN  = +1
    LOSE = -1

    Первое значение равно нулю.
    """

    equity_curve = [0]
    balance = 0

    for result in history:
        if result == "WIN":
            balance += 1
        else:
            balance -= 1

        equity_curve.append(balance)

    return equity_curve


# ------------------------------------------------------------
# Расчёт максимальной просадки
# ------------------------------------------------------------

def _calculate_drawdown(equity_curve: list[int]) -> dict:
    """
    Рассчитывает максимальную условную просадку.

    Просадка считается от предыдущего максимума
    кривой результата до следующего минимума.
    """

    if not equity_curve:
        return {
            "max_drawdown": 0,
            "peak_value": 0,
            "bottom_value": 0,
            "peak_index": 0,
            "bottom_index": 0,
        }

    running_peak = equity_curve[0]
    running_peak_index = 0

    max_drawdown = 0
    max_peak_value = equity_curve[0]
    max_bottom_value = equity_curve[0]
    max_peak_index = 0
    max_bottom_index = 0

    for index, value in enumerate(equity_curve):
        if value > running_peak:
            running_peak = value
            running_peak_index = index

        current_drawdown = running_peak - value

        if current_drawdown > max_drawdown:
            max_drawdown = current_drawdown
            max_peak_value = running_peak
            max_bottom_value = value
            max_peak_index = running_peak_index
            max_bottom_index = index

    return {
        "max_drawdown": max_drawdown,
        "peak_value": max_peak_value,
        "bottom_value": max_bottom_value,
        "peak_index": max_peak_index,
        "bottom_index": max_bottom_index,
    }


# ------------------------------------------------------------
# Расчёт восстановления
# ------------------------------------------------------------

def _calculate_recovery(
    equity_curve: list[int],
    drawdown: dict,
) -> dict:
    """
    Определяет, восстановилась ли кривая после
    максимальной просадки.

    Восстановление считается завершённым,
    когда результат снова достигает значения
    предыдущего максимума.
    """

    peak_value = drawdown.get("peak_value", 0)
    bottom_index = drawdown.get("bottom_index", 0)

    if drawdown.get("max_drawdown", 0) <= 0:
        return {
            "recovered": True,
            "recovery_length": 0,
            "recovery_index": bottom_index,
            "unrecovered_length": 0,
        }

    for index in range(bottom_index + 1, len(equity_curve)):
        if equity_curve[index] >= peak_value:
            return {
                "recovered": True,
                "recovery_length": index - bottom_index,
                "recovery_index": index,
                "unrecovered_length": 0,
            }

    return {
        "recovered": False,
        "recovery_length": None,
        "recovery_index": None,
        "unrecovered_length": (
            len(equity_curve) - 1 - bottom_index
        ),
    }


# ------------------------------------------------------------
# Расчёт переключений WIN / LOSE
# ------------------------------------------------------------

def _calculate_alternation(history: list[str]) -> dict:
    """
    Оценивает равномерность чередования результатов.

    Чем чаще WIN и LOSE сменяют друг друга,
    тем меньше результаты собраны в длинные серии.
    """

    total_transitions = max(0, len(history) - 1)

    if total_transitions == 0:
        return {
            "changes": 0,
            "total_transitions": 0,
            "alternation_ratio": 0.0,
        }

    changes = 0

    for previous, current in zip(
        history,
        history[1:],
    ):
        if previous != current:
            changes += 1

    alternation_ratio = changes / total_transitions

    return {
        "changes": changes,
        "total_transitions": total_transitions,
        "alternation_ratio": round(
            alternation_ratio,
            4,
        ),
    }


# ------------------------------------------------------------
# Концентрация выигрышей
# ------------------------------------------------------------

def _calculate_win_concentration(
    history: list[str],
    block_size: int = 10,
) -> dict:
    """
    Проверяет, насколько выигрыши сосредоточены
    в отдельных блоках истории.

    История делится на блоки по 10 результатов.
    Затем сравнивается самый успешный блок
    с общим количеством выигрышей.
    """

    total_wins = history.count("WIN")

    if total_wins == 0:
        return {
            "block_size": block_size,
            "blocks": [],
            "maximum_block_wins": 0,
            "concentration_ratio": 1.0,
        }

    blocks = []

    for start in range(0, len(history), block_size):
        block = history[start:start + block_size]
        block_wins = block.count("WIN")

        blocks.append({
            "start": start,
            "end": start + len(block) - 1,
            "total": len(block),
            "wins": block_wins,
        })

    maximum_block_wins = max(
        block["wins"]
        for block in blocks
    )

    concentration_ratio = (
        maximum_block_wins / total_wins
    )

    return {
        "block_size": block_size,
        "blocks": blocks,
        "maximum_block_wins": maximum_block_wins,
        "concentration_ratio": round(
            concentration_ratio,
            4,
        ),
    }


# ------------------------------------------------------------
# Баллы за максимальную серию поражений
# ------------------------------------------------------------

def _score_losing_streak(
    max_losing_streak: int,
) -> dict:
    """
    Максимум: 30 баллов.
    """

    if max_losing_streak <= 2:
        points = 30
        reason = (
            f"Максимальная серия поражений: "
            f"{max_losing_streak}. Очень короткая серия."
        )
    elif max_losing_streak <= 4:
        points = 24
        reason = (
            f"Максимальная серия поражений: "
            f"{max_losing_streak}. Допустимый уровень."
        )
    elif max_losing_streak <= 6:
        points = 17
        reason = (
            f"Максимальная серия поражений: "
            f"{max_losing_streak}. Возможна заметная "
            f"психологическая нагрузка."
        )
    elif max_losing_streak <= 8:
        points = 9
        reason = (
            f"Максимальная серия поражений: "
            f"{max_losing_streak}. Высокая нагрузка "
            f"на банк и дисциплину."
        )
    else:
        points = 2
        reason = (
            f"Максимальная серия поражений: "
            f"{max_losing_streak}. Очень высокий риск "
            f"длительной неудачной серии."
        )

    return {
        "name": "Максимальная серия поражений",
        "points": points,
        "max_points": 30,
        "value": max_losing_streak,
        "reason": reason,
    }


# ------------------------------------------------------------
# Баллы за условную просадку
# ------------------------------------------------------------

def _score_drawdown(
    max_drawdown: int,
    history_size: int,
) -> dict:
    """
    Максимум: 25 баллов.

    Просадка сравнивается с размером всей истории.
    """

    if history_size <= 0:
        drawdown_ratio = 1.0
    else:
        drawdown_ratio = max_drawdown / history_size

    if drawdown_ratio <= 0.05:
        points = 25
    elif drawdown_ratio <= 0.10:
        points = 21
    elif drawdown_ratio <= 0.15:
        points = 16
    elif drawdown_ratio <= 0.25:
        points = 10
    else:
        points = 3

    return {
        "name": "Максимальная условная просадка",
        "points": points,
        "max_points": 25,
        "max_drawdown": max_drawdown,
        "drawdown_ratio": round(
            drawdown_ratio,
            4,
        ),
        "reason": (
            f"Максимальная условная просадка составила "
            f"{max_drawdown} единиц, или "
            f"{drawdown_ratio * 100:.2f}% "
            f"от размера исследуемой истории."
        ),
    }


# ------------------------------------------------------------
# Баллы за восстановление
# ------------------------------------------------------------

def _score_recovery(recovery: dict) -> dict:
    """
    Максимум: 20 баллов.
    """

    if recovery.get("recovered"):
        recovery_length = (
            recovery.get("recovery_length") or 0
        )

        if recovery_length <= 3:
            points = 20
        elif recovery_length <= 7:
            points = 16
        elif recovery_length <= 15:
            points = 11
        elif recovery_length <= 30:
            points = 6
        else:
            points = 3

        reason = (
            f"После максимальной просадки восстановление "
            f"заняло {recovery_length} результатов."
        )
    else:
        points = 0
        unrecovered_length = recovery.get(
            "unrecovered_length",
            0,
        )

        reason = (
            f"Максимальная просадка ещё не восстановлена. "
            f"После её минимума прошло "
            f"{unrecovered_length} результатов."
        )

    return {
        "name": "Восстановление после просадки",
        "points": points,
        "max_points": 20,
        "recovered": recovery.get("recovered"),
        "recovery_length": recovery.get(
            "recovery_length"
        ),
        "reason": reason,
    }


# ------------------------------------------------------------
# Баллы за равномерность
# ------------------------------------------------------------

def _score_alternation(alternation: dict) -> dict:
    """
    Максимум: 15 баллов.

    Здесь не требуется идеальное чередование.
    Слишком низкое значение указывает на длинные серии.
    """

    ratio = alternation.get(
        "alternation_ratio",
        0.0,
    )

    if 0.45 <= ratio <= 0.75:
        points = 15
        reason = (
            "Результаты достаточно равномерно "
            "распределены по истории."
        )
    elif 0.30 <= ratio < 0.45:
        points = 11
        reason = (
            "В истории присутствуют серии, "
            "но распределение остаётся приемлемым."
        )
    elif ratio > 0.75:
        points = 12
        reason = (
            "Результаты очень часто чередуются. "
            "Длинные серии встречаются редко."
        )
    elif 0.15 <= ratio < 0.30:
        points = 6
        reason = (
            "Результаты заметно сгруппированы "
            "в победные и проигрышные серии."
        )
    else:
        points = 2
        reason = (
            "Результаты сильно сконцентрированы "
            "в длинных однотипных сериях."
        )

    return {
        "name": "Равномерность результатов",
        "points": points,
        "max_points": 15,
        "alternation_ratio": ratio,
        "reason": reason,
    }


# ------------------------------------------------------------
# Баллы за концентрацию выигрышей
# ------------------------------------------------------------

def _score_win_concentration(
    concentration: dict,
    total_blocks: int,
) -> dict:
    """
    Максимум: 10 баллов.
    """

    ratio = concentration.get(
        "concentration_ratio",
        1.0,
    )

    # При одном блоке концентрацию оценивать нельзя
    if total_blocks <= 1:
        points = 5
        reason = (
            "История слишком короткая для полноценной "
            "оценки концентрации выигрышей."
        )
    elif ratio <= 0.20:
        points = 10
        reason = (
            "Выигрыши хорошо распределены "
            "по разным участкам истории."
        )
    elif ratio <= 0.30:
        points = 8
        reason = (
            "Концентрация выигрышей находится "
            "на приемлемом уровне."
        )
    elif ratio <= 0.45:
        points = 5
        reason = (
            "Заметная часть выигрышей сосредоточена "
            "в одном участке истории."
        )
    else:
        points = 2
        reason = (
            "Большая доля выигрышей сосредоточена "
            "в одном участке истории."
        )

    return {
        "name": "Концентрация выигрышей",
        "points": points,
        "max_points": 10,
        "concentration_ratio": ratio,
        "reason": reason,
    }


# ------------------------------------------------------------
# Определение уровня Stability
# ------------------------------------------------------------

def _get_stability_level(
    stability: float,
) -> dict:
    """
    Возвращает уровень стабильности.
    """

    if stability < 35:
        return {
            "code": "low",
            "icon": "🔴",
            "title": "Низкая стабильность",
        }

    if stability < 55:
        return {
            "code": "medium",
            "icon": "🟠",
            "title": "Умеренная стабильность",
        }

    if stability < 75:
        return {
            "code": "good",
            "icon": "🟡",
            "title": "Хорошая стабильность",
        }

    return {
        "code": "strong",
        "icon": "🟢",
        "title": "Высокая стабильность",
    }


# ------------------------------------------------------------
# Основная функция
# ------------------------------------------------------------

def calculate_stability(history: Any) -> dict:
    """
    Рассчитывает Stability для истории сигналов.

    Аргументы:
        history:
            Последовательность результатов.

    Возвращает:
        Подробный словарь с итоговым баллом,
        компонентами и служебной аналитикой.
    """

    normalized_history = _normalize_history(history)
    history_size = len(normalized_history)

    wins = normalized_history.count("WIN")
    losses = normalized_history.count("LOSE")

    # Недостаточно данных для полноценного расчёта
    if history_size < MIN_HISTORY_SIZE:
        return {
            "version": STABILITY_VERSION,
            "stability": 0,
            "max_stability": 100,
            "level": {
                "code": "insufficient",
                "icon": "⚪",
                "title": "Недостаточно данных",
            },
            "history_size": history_size,
            "wins": wins,
            "losses": losses,
            "components": [],
            "streaks": {
                "max_winning_streak": 0,
                "max_losing_streak": 0,
                "current_streak": 0,
                "current_streak_type": None,
            },
            "drawdown": {
                "max_drawdown": 0,
            },
            "recovery": {
                "recovered": False,
                "recovery_length": None,
            },
            "alternation": {
                "alternation_ratio": 0.0,
            },
            "win_concentration": {
                "concentration_ratio": 0.0,
            },
            "is_probability": False,
            "warning": (
                f"Для оценки Stability требуется минимум "
                f"{MIN_HISTORY_SIZE} корректных результатов."
            ),
        }

    streaks = _calculate_streaks(
        normalized_history
    )

    equity_curve = _build_equity_curve(
        normalized_history
    )

    drawdown = _calculate_drawdown(
        equity_curve
    )

    recovery = _calculate_recovery(
        equity_curve,
        drawdown,
    )

    alternation = _calculate_alternation(
        normalized_history
    )

    win_concentration = (
        _calculate_win_concentration(
            normalized_history
        )
    )

    components = [
        _score_losing_streak(
            streaks["max_losing_streak"]
        ),
        _score_drawdown(
            drawdown["max_drawdown"],
            history_size,
        ),
        _score_recovery(
            recovery
        ),
        _score_alternation(
            alternation
        ),
        _score_win_concentration(
            win_concentration,
            len(win_concentration["blocks"]),
        ),
    ]

    stability = sum(
        component["points"]
        for component in components
    )

    stability = round(
        float(stability),
        2,
    )

    return {
        "version": STABILITY_VERSION,
        "stability": stability,
        "max_stability": 100,
        "level": _get_stability_level(
            stability
        ),
        "history_size": history_size,
        "wins": wins,
        "losses": losses,
        "components": components,
        "streaks": streaks,
        "drawdown": {
            **drawdown,
            "equity_curve": equity_curve,
        },
        "recovery": recovery,
        "alternation": alternation,
        "win_concentration": win_concentration,
        "is_probability": False,
        "warning": (
            "Stability оценивает характер распределения "
            "исторических результатов. Показатель не является "
            "вероятностью выигрыша и не учитывает коэффициенты, "
            "ROI или реальные размеры ставок."
        ),
    }