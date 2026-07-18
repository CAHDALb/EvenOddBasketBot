"""
Ограничения риска для виртуального фонда.
"""

MIN_COMPLETED_SIGNALS = 100
REAL_BANK_REVIEW_SIGNALS = 500

MAX_STAKE_PERCENT = 1.00


def can_start_virtual_fund(completed_signals):
    """
    Можно ли запускать виртуальный фонд.
    """

    return completed_signals >= MIN_COMPLETED_SIGNALS


def can_review_real_bank(completed_signals):
    """
    Достаточно ли сигналов для оценки реального банка.

    Это не означает автоматическое разрешение
    использовать реальные деньги.
    """

    return completed_signals >= REAL_BANK_REVIEW_SIGNALS


def validate_stake_percent(stake_percent):
    """
    Проверяет допустимый размер ставки.
    """

    if stake_percent <= 0:
        raise ValueError(
            "Процент ставки должен быть больше нуля."
        )

    if stake_percent > MAX_STAKE_PERCENT:
        raise ValueError(
            f"Ставка не должна превышать "
            f"{MAX_STAKE_PERCENT:.2f}% банка."
        )

    return True