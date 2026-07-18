"""
Ядро виртуального фонда EvenOddBasketBot.
"""

from financial.bank_models import get_bank_model
from financial.fund_statistics import (
    calculate_profit,
    calculate_return_percent,
    calculate_max_drawdown,
)
from financial.risk_manager import (
    can_start_virtual_fund,
    validate_stake_percent,
)


class VirtualFund:
    """
    Представляет один виртуальный банк.

    Пока фонд не подключён к результатам сигналов.
    На первом этапе он хранит настройки
    и показывает статус готовности.
    """

    def __init__(
        self,
        model_name,
        completed_signals,
        initial_bank=100_000,
    ):
        self.model_name = model_name
        self.completed_signals = completed_signals
        self.initial_bank = float(initial_bank)
        self.current_bank = float(initial_bank)
        self.bank_history = [float(initial_bank)]

        self.model = get_bank_model(model_name)

        validate_stake_percent(
            self.model["stake_percent"]
        )

    @property
    def is_active(self):
        """
        Запущен ли виртуальный фонд.
        """

        return can_start_virtual_fund(
            self.completed_signals
        )

    @property
    def progress_percent(self):
        """
        Прогресс до запуска фонда.
        """

        progress = self.completed_signals / 100 * 100

        return min(progress, 100.0)

    def get_status(self):
        """
        Возвращает состояние фонда для сайта.
        """

        if self.is_active:
            status = "active"
            status_text = "Виртуальный фонд активен"
        else:
            status = "waiting"
            status_text = (
                "Ожидает 100 завершённых сигналов"
            )

        return {
            "model_name": self.model_name,
            "model_title": self.model["title"],
            "description": self.model["description"],
            "stake_percent": self.model["stake_percent"],
            "initial_bank": self.initial_bank,
            "current_bank": self.current_bank,
            "profit": calculate_profit(
                self.initial_bank,
                self.current_bank,
            ),
            "return_percent": calculate_return_percent(
                self.initial_bank,
                self.current_bank,
            ),
            "max_drawdown": calculate_max_drawdown(
                self.bank_history
            ),
            "completed_signals": self.completed_signals,
            "target_signals": 100,
            "progress_percent": self.progress_percent,
            "status": status,
            "status_text": status_text,
        }