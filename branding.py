"""
===========================================================
EvenOddBasketBot

Файл:
branding.py

Назначение:
Единая точка фирменного стиля проекта:
- название и слоган;
- тексты профиля Telegram;
- пути к изображениям;
- юридические предупреждения;
- команды, отображаемые в меню Telegram.
===========================================================
"""

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
BRAND_DIR = PROJECT_DIR / "assets" / "brand"

BRAND_NAME = "EvenOddBasketBot"
BRAND_TAGLINE = "Basketball Signal Analytics"
BRAND_VERSION = "15.1"

BOT_SHORT_DESCRIPTION = (
    "Баскетбольная аналитика и LIVE-сигналы в реальном времени."
)

BOT_DESCRIPTION = (
    "EvenOddBasketBot анализирует LIVE-баскетбольные матчи, "
    "формирует сигналы по заданным стратегиям и ведёт прозрачную "
    "статистику результатов.\n\n"
    "🏀 LIVE-сигналы\n"
    "📊 Аналитика матчей\n"
    "📈 История результатов\n"
    "💎 FREE и PREMIUM-доступ\n\n"
    "Информационно-аналитический сервис. 18+"
)

BOT_COMMANDS = [
    {"command": "start", "description": "Регистрация и главное меню"},
    {"command": "menu", "description": "Открыть главное меню"},
    {"command": "profile", "description": "Мой профиль и тариф"},
    {"command": "about", "description": "О проекте и правила сервиса"},
    {"command": "help", "description": "Помощь по использованию"},
]

WELCOME_BANNER_PATH = BRAND_DIR / "welcome_banner.jpg"
AVATAR_PATH = BRAND_DIR / "avatar_eob.png"
FULL_LOGO_PATH = BRAND_DIR / "logo_full.jpg"

DISCLAIMER_SHORT = (
    "⚠️ Аналитическая информация, а не гарантия результата. "
    "Решение пользователь принимает самостоятельно. 18+"
)

DISCLAIMER_FULL = (
    "EvenOddBasketBot предоставляет информационно-аналитические "
    "материалы и не является букмекерской организацией.\n\n"
    "Сервис не гарантирует получение прибыли. Статистические "
    "показатели отражают прошлые результаты и не гарантируют "
    "будущую проходимость.\n\n"
    "Пользователь самостоятельно принимает решения и несёт "
    "ответственность за возможные финансовые потери. Не используйте "
    "заёмные средства и деньги, потеря которых повлияет на качество "
    "жизни. 18+"
)


def brand_header(section=None):
    """Возвращает единый заголовок сообщения Telegram."""

    if section:
        return f"🏀 {BRAND_NAME}\n{section}"

    return f"🏀 {BRAND_NAME}"
