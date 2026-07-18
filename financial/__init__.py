"""
Financial Engine для EvenOddBasketBot.

Модули:
- virtual_fund.py — состояние виртуального фонда;
- bank_models.py — модели размера ставки;
- risk_manager.py — ограничения риска;
- fund_statistics.py — финансовые показатели.
"""

from .virtual_fund import VirtualFund
from .bank_models import BANK_MODELS