"""
Финансовые расчёты виртуального фонда.
"""


def calculate_profit(initial_bank, current_bank):
    """
    Чистая прибыль или убыток.
    """

    return current_bank - initial_bank


def calculate_return_percent(initial_bank, current_bank):
    """
    Доходность относительно начального банка.
    """

    if initial_bank <= 0:
        return 0.0

    profit = calculate_profit(
        initial_bank=initial_bank,
        current_bank=current_bank,
    )

    return profit / initial_bank * 100


def calculate_max_drawdown(bank_history):
    """
    Максимальная просадка банка в процентах.

    bank_history:
    [100000, 99500, 100200, ...]
    """

    if not bank_history:
        return 0.0

    peak = bank_history[0]
    max_drawdown = 0.0

    for bank in bank_history:

        if bank > peak:
            peak = bank

        if peak <= 0:
            continue

        drawdown = (bank - peak) / peak * 100

        if drawdown < max_drawdown:
            max_drawdown = drawdown

    return max_drawdown