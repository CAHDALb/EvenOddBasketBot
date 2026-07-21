"""
===========================================================
EvenOddBasketBot

Файл:
dashboard.py

Назначение:
Формирует HTML-страницу Mission Control
со статистикой из PostgreSQL Neon.
===========================================================
"""
from financial import VirtualFund, BANK_MODELS
from branding import BRAND_NAME, BRAND_TAGLINE, BRAND_VERSION
from config import CHECK_INTERVAL
from html import escape

from analytics import get_recent_statistics, get_risk_indicator
from statistics import (
    get_total_statistics,
    get_country_statistics,
    get_league_statistics,
    get_match_type_statistics,
)


MATCH_TYPE_NAMES = {
    "men": "👨 Мужские",
    "women": "👩 Женские",
    "youth": "👦 Молодёжные",
    "unknown": "❓ Не определено",
}


def format_roi(value):
    """
    Форматирует ROI со знаком.
    """

    return f"{float(value or 0):+.2f}"


def build_country_rows(items, limit=10):
    """
    Формирует строки таблицы по странам.
    """

    rows = []

    # Сначала показываем страны с большей выборкой
    sorted_items = sorted(
        items,
        key=lambda item: (
            item["total"],
            item["roi"],
        ),
        reverse=True,
    )

    for index, item in enumerate(sorted_items[:limit], start=1):
        rows.append(
            f"""
            <tr>
                <td>{index}</td>
                <td>{escape(str(item["country"]))}</td>
                <td>{item["total"]}</td>
                <td>{item["wins"]}</td>
                <td>{item["loses"]}</td>
                <td>{item["win_rate"]:.2f}%</td>
                <td>{format_roi(item["roi"])}</td>
            </tr>
            """
        )

    if not rows:
        rows.append(
            """
            <tr>
                <td colspan="7">Пока нет завершённых сигналов</td>
            </tr>
            """
        )

    return "".join(rows)


def build_league_rows(items, limit=10):
    """
    Формирует строки таблицы по лигам.
    """

    rows = []

    sorted_items = sorted(
        items,
        key=lambda item: (
            item["total"],
            item["roi"],
        ),
        reverse=True,
    )

    for index, item in enumerate(sorted_items[:limit], start=1):
        rows.append(
            f"""
            <tr>
                <td>{index}</td>
                <td>{escape(str(item["league"]))}</td>
                <td>{item["total"]}</td>
                <td>{item["wins"]}</td>
                <td>{item["loses"]}</td>
                <td>{item["win_rate"]:.2f}%</td>
                <td>{format_roi(item["roi"])}</td>
            </tr>
            """
        )

    if not rows:
        rows.append(
            """
            <tr>
                <td colspan="7">Пока нет завершённых сигналов</td>
            </tr>
            """
        )

    return "".join(rows)


def build_match_type_cards(items):
    """
    Формирует карточки статистики
    по мужчинам, женщинам и молодёжным матчам.
    """

    cards = []

    for item in items:
        type_name = MATCH_TYPE_NAMES.get(
            item["match_type"],
            str(item["match_type"]),
        )

        cards.append(
            f"""
            <div class="type-card">
                <h3>{escape(type_name)}</h3>
                <p><strong>Сигналов:</strong> {item["total"]}</p>
                <p>
                    <strong>WIN / LOSE:</strong>
                    {item["wins"]} / {item["loses"]}
                </p>
                <p>
                    <strong>Проходимость:</strong>
                    {item["win_rate"]:.2f}%
                </p>
                <p>
                    <strong>ROI:</strong>
                    {format_roi(item["roi"])}
                </p>
            </div>
            """
        )

    if not cards:
        cards.append(
            """
            <div class="type-card">
                <h3>Пока нет данных</h3>
                <p>Ожидаем завершённые сигналы.</p>
            </div>
            """
        )

    return "".join(cards)

def format_money(value):
    """
    Форматирует денежную сумму.
    """

    return f"{float(value):,.0f} ₽".replace(",", " ")


def build_fund_cards(funds):
    """
    Формирует карточки виртуальных фондов.
    """

    cards = []

    for fund in funds:
        status = fund.get_status()

        cards.append(
            f"""
            <div class="fund-card">
                <div class="fund-header">
                    <h3>{escape(status["model_title"])}</h3>
                    <span class="fund-percent">
                        Ставка: {status["stake_percent"]:.2f}%
                    </span>
                </div>

                <p class="fund-description">
                    {escape(status["description"])}
                </p>

                <div class="fund-values">
                    <p>
                        <strong>Начальный банк:</strong>
                        {format_money(status["initial_bank"])}
                    </p>

                    <p>
                        <strong>Текущий банк:</strong>
                        {format_money(status["current_bank"])}
                    </p>

                    <p>
                        <strong>Прибыль:</strong>
                        {format_money(status["profit"])}
                    </p>
                </div>

                <div class="progress-info">
                    <span>
                        Прогресс:
                        {status["completed_signals"]}
                        /
                        {status["target_signals"]}
                    </span>

                    <span>
                        {status["progress_percent"]:.0f}%
                    </span>
                </div>

                <div class="progress-bar">
                    <div
                        class="progress-fill"
                        style="
                            width:
                            {status["progress_percent"]:.2f}%;
                        "
                    ></div>
                </div>

                <div class="fund-status">
                    🔒 {escape(status["status_text"])}
                </div>
            </div>
            """
        )

    return "".join(cards)

def build_dashboard_html():
    """Загружает статистику и возвращает фирменную HTML-страницу."""

    total = get_total_statistics()
    countries = get_country_statistics()
    leagues = get_league_statistics()
    match_types = get_match_type_statistics()

    completed_signals = total["wins"] + total["loses"]

    funds = [
        VirtualFund(
            model_name=model_name,
            completed_signals=completed_signals,
            initial_bank=100_000,
        )
        for model_name in BANK_MODELS
    ]

    recent = get_recent_statistics(limit=10)
    risk = get_risk_indicator(recent)
    history_line = recent["history_line"] or "Пока нет результатов"
    streak = recent["streak"]

    if streak["result"] == "win":
        streak_text = f'{streak["length"]} WIN 🟢'
    elif streak["result"] == "lose":
        streak_text = f'{streak["length"]} LOSE 🔴'
    else:
        streak_text = "Нет завершённых сигналов"

    country_rows = build_country_rows(countries)
    league_rows = build_league_rows(leagues)
    match_type_cards = build_match_type_cards(match_types)
    fund_cards = build_fund_cards(funds)

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#031126">
    <meta name="description" content="EvenOddBasketBot — LIVE-баскетбольная аналитика и прозрачная статистика сигналов.">
    <meta http-equiv="refresh" content="{CHECK_INTERVAL}">

    <title>{BRAND_NAME} — Mission Control</title>

    <link rel="icon" type="image/png" href="/static/brand/favicon.png">
    <link rel="stylesheet" href="/static/styles.css">
</head>

<body>
    <div class="container">
        <nav class="brand-nav">
            <div class="brand-lockup">
                <img class="brand-mark" src="/static/brand/favicon.png" alt="EOB">
                <div>
                    <h1 class="brand-name">
                        Even<span class="odd">Odd</span>Basket<span class="bot">Bot</span>
                    </h1>
                    <p class="brand-tagline">{BRAND_TAGLINE}</p>
                </div>
            </div>
            <div class="status">System online</div>
        </nav>

        <header class="hero">
            <img
                src="/static/brand/hero_banner.jpg"
                alt="EvenOddBasketBot Basketball Signal Analytics"
            >
            <div class="hero-caption">
                <strong>Mission Control v{BRAND_VERSION}</strong>
                <span>Алгоритмическая аналитика LIVE-баскетбола</span>
            </div>
        </header>

        <section class="cards" aria-label="Основная статистика">
            <div class="card">
                <span class="label">Всего сигналов</span>
                <span class="value">{total["total"]}</span>
            </div>
            <div class="card">
                <span class="label">Ожидают</span>
                <span class="value">{total["waiting"]}</span>
            </div>
            <div class="card">
                <span class="label">WIN</span>
                <span class="value">{total["wins"]}</span>
            </div>
            <div class="card">
                <span class="label">LOSE</span>
                <span class="value">{total["loses"]}</span>
            </div>
            <div class="card">
                <span class="label">Проходимость</span>
                <span class="value">{total["win_rate"]:.2f}%</span>
            </div>
            <div class="card">
                <span class="label">ROI</span>
                <span class="value">{format_roi(total["roi"])}</span>
            </div>
        </section>

        <section class="section">
            <h2>📈 Последние результаты</h2>
            <div class="recent-line">{history_line}</div>
            <p><strong>WIN:</strong> {recent["wins"]} из {recent["total"]}</p>
            <p><strong>Проходимость:</strong> {recent["win_rate"]:.2f}%</p>
            <p><strong>Текущая серия:</strong> {streak_text}</p>

            <div class="risk">
                <strong>{risk["icon"]} {escape(risk["title"])}</strong>
                <p>{escape(risk["message"])}</p>
            </div>
        </section>

        <section class="section">
            <h2>📂 Типы матчей</h2>
            <div class="type-grid">{match_type_cards}</div>
        </section>

        <section class="section">
            <h2>💼 EvenOdd Strategy Fund</h2>
            <p class="section-description">
                Стартовый виртуальный капитал каждой модели: 100 000 ₽.
                Фонды автоматически активируются после накопления
                100 завершённых сигналов.
            </p>
            <div class="fund-grid">{fund_cards}</div>
        </section>

        <section class="section">
            <h2>🌍 Статистика по странам</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>№</th><th>Страна</th><th>Сигналов</th>
                            <th>WIN</th><th>LOSE</th>
                            <th>Проходимость</th><th>ROI</th>
                        </tr>
                    </thead>
                    <tbody>{country_rows}</tbody>
                </table>
            </div>
        </section>

        <section class="section">
            <h2>🏆 Статистика по лигам</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>№</th><th>Лига</th><th>Сигналов</th>
                            <th>WIN</th><th>LOSE</th>
                            <th>Проходимость</th><th>ROI</th>
                        </tr>
                    </thead>
                    <tbody>{league_rows}</tbody>
                </table>
            </div>
        </section>

        <aside class="legal">
            <strong>⚠️ Ответственное использование</strong><br>
            EvenOddBasketBot предоставляет информационно-аналитические
            материалы, не гарантирует прибыль и не является букмекерской
            организацией. Прошлые результаты не гарантируют будущую
            проходимость. Пользователь принимает решения самостоятельно. 18+.
        </aside>

        <footer class="footer">
            {BRAND_NAME} • {BRAND_TAGLINE}<br>
            Данные загружаются из PostgreSQL Neon. Страница обновляется
            каждые {CHECK_INTERVAL} секунд.
        </footer>
    </div>
</body>
</html>
"""


def build_error_html(error):
    """Фирменная страница, отображаемая при ошибке чтения базы."""

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#031126">
    <title>{BRAND_NAME} — ошибка</title>
    <link rel="icon" type="image/png" href="/static/brand/favicon.png">
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <nav class="brand-nav">
            <div class="brand-lockup">
                <img class="brand-mark" src="/static/brand/favicon.png" alt="EOB">
                <div>
                    <h1 class="brand-name">Even<span class="odd">Odd</span>Basket<span class="bot">Bot</span></h1>
                    <p class="brand-tagline">{BRAND_TAGLINE}</p>
                </div>
            </div>
        </nav>
        <section class="section">
            <h2>Не удалось загрузить статистику</h2>
            <p>{escape(str(error))}</p>
        </section>
    </div>
</body>
</html>
"""
