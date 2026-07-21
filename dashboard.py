"""
===========================================================
EvenOddBasketBot

Файл:
dashboard.py

Назначение:
Отдаёт HTML-каркас публичной Mission Control панели.
Все реальные значения загружаются через /api/dashboard.
===========================================================
"""

from html import escape
from pathlib import Path

from branding import BRAND_NAME, BRAND_VERSION
from config import CHECK_INTERVAL


PROJECT_DIR = Path(__file__).resolve().parent
INDEX_PATH = PROJECT_DIR / "dashboard_static" / "index.html"


def build_dashboard_html() -> str:
    """Читает статический шаблон и подставляет безопасную конфигурацию."""

    template = INDEX_PATH.read_text(encoding="utf-8")
    return (
        template
        .replace("{{VERSION}}", escape(str(BRAND_VERSION)))
        .replace("{{REFRESH_SECONDS}}", str(max(15, min(CHECK_INTERVAL, 300))))
    )


def build_error_html(error: Exception) -> str:
    """Минимальная аварийная страница без раскрытия секретов сервера."""

    print("Dashboard HTML error:", error)
    return f"""
    <!doctype html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{escape(BRAND_NAME)} — временно недоступно</title>
        <style>
            body {{ margin:0; min-height:100vh; display:grid; place-items:center;
                   background:#020815; color:#f5f8ff; font-family:system-ui,sans-serif; }}
            main {{ width:min(560px, calc(100% - 32px)); padding:32px; border:1px solid #15506b;
                    border-radius:18px; background:#06152a; box-shadow:0 30px 80px #0008; }}
            h1 {{ margin-top:0; }} p {{ color:#9fb0c5; line-height:1.65; }}
            a {{ color:#19d8e7; }}
        </style>
    </head>
    <body><main><h1>🏀 {escape(BRAND_NAME)}</h1><p>Панель временно не смогла загрузиться. Обновите страницу через несколько секунд.</p><a href="/">Повторить</a></main></body>
    </html>
    """
