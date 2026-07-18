import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

from financial import VirtualFund, BANK_MODELS


print("=" * 60)
print("Financial Engine")
print("=" * 60)

print("Доступные модели:")

for model_name, model in BANK_MODELS.items():
    print(
        model_name,
        "→",
        model["title"],
        f'({model["stake_percent"]:.2f}%)'
    )

print("-" * 60)

fund = VirtualFund(
    model_name="balanced",
    completed_signals=10,
    initial_bank=100_000,
)

status = fund.get_status()

for key, value in status.items():
    print(f"{key}: {value}")

print("=" * 60)