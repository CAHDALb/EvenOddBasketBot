"""
Модели управления виртуальным банком.
"""

BANK_MODELS = {
    "conservative": {
        "title": "Консервативная",
        "stake_percent": 0.25,
        "description": "Минимальный риск и меньшая просадка.",
    },
    "balanced": {
        "title": "Сбалансированная",
        "stake_percent": 0.50,
        "description": "Баланс между ростом банка и риском.",
    },
    "aggressive": {
        "title": "Агрессивная",
        "stake_percent": 1.00,
        "description": "Повышенный риск ради более быстрого роста.",
    },
}


def get_bank_model(model_name):
    """
    Возвращает настройки выбранной модели банка.
    """

    if model_name not in BANK_MODELS:
        raise ValueError(
            f"Неизвестная модель банка: {model_name}"
        )

    return BANK_MODELS[model_name]