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


def build_dashboard_html():
    """
    Загружает статистику и возвращает готовую HTML-страницу.
    """

    total = get_total_statistics()
    countries = get_country_statistics()
    leagues = get_league_statistics()
    match_types = get_match_type_statistics()

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

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <!-- Обновляем статистику раз в 180 секунд -->
    <meta http-equiv="refresh" content="180">

    <title>EvenOddBasketBot Mission Control</title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #10131a;
            color: #f4f4f4;
        }}

        .container {{
            width: min(1200px, 94%);
            margin: 0 auto;
            padding: 30px 0 60px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin-bottom: 8px;
            font-size: 34px;
        }}

        .header p {{
            margin: 0;
            color: #aeb7c5;
        }}

        .status {{
            display: inline-block;
            margin-top: 14px;
            padding: 8px 14px;
            border-radius: 20px;
            background: #153b2b;
            color: #63e6a1;
            font-weight: bold;
        }}

        .cards {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(170px, 1fr));
            gap: 14px;
            margin-bottom: 26px;
        }}

        .card,
        .section,
        .type-card {{
            background: #1b202b;
            border: 1px solid #2c3442;
            border-radius: 14px;
        }}

        .card {{
            padding: 20px;
            text-align: center;
        }}

        .card .value {{
            display: block;
            margin-top: 8px;
            font-size: 30px;
            font-weight: bold;
        }}

        .card .label {{
            color: #aeb7c5;
        }}

        .section {{
            padding: 22px;
            margin-bottom: 24px;
        }}

        .section h2 {{
            margin-top: 0;
        }}

        .recent-line {{
            font-size: 31px;
            letter-spacing: 5px;
            overflow-wrap: anywhere;
        }}

        .risk {{
            margin-top: 16px;
            padding: 14px;
            background: #222938;
            border-radius: 10px;
        }}

        .type-grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
        }}

        .type-card {{
            padding: 18px;
        }}

        .type-card h3 {{
            margin-top: 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 760px;
        }}

        th,
        td {{
            padding: 11px;
            border-bottom: 1px solid #303847;
            text-align: left;
        }}

        th {{
            color: #aeb7c5;
        }}

        .table-wrapper {{
            overflow-x: auto;
        }}

        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #7f8998;
            font-size: 14px;
        }}

        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 27px;
            }}

            .container {{
                width: 96%;
            }}

            .section {{
                padding: 16px;
            }}

            .recent-line {{
                font-size: 25px;
            }}
        }}
    </style>
</head>

<body>
    <div class="container">

        <header class="header">
            <h1>🏀 EvenOddBasketBot</h1>
            <p>Mission Control v0.1</p>
            <div class="status">● Система работает</div>
        </header>

        <section class="cards">
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

            <div class="recent-line">
                {history_line}
            </div>

            <p>
                <strong>WIN:</strong> {recent["wins"]}
                из {recent["total"]}
            </p>

            <p>
                <strong>Проходимость:</strong>
                {recent["win_rate"]:.2f}%
            </p>

            <p>
                <strong>Текущая серия:</strong>
                {streak_text}
            </p>

            <div class="risk">
                <strong>
                    {risk["icon"]} {escape(risk["title"])}
                </strong>

                <p>{escape(risk["message"])}</p>
            </div>
        </section>

        <section class="section">
            <h2>📂 Типы матчей</h2>

            <div class="type-grid">
                {match_type_cards}
            </div>
        </section>

        <section class="section">
            <h2>🌍 Статистика по странам</h2>

            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Страна</th>
                            <th>Сигналов</th>
                            <th>WIN</th>
                            <th>LOSE</th>
                            <th>Проходимость</th>
                            <th>ROI</th>
                        </tr>
                    </thead>

                    <tbody>
                        {country_rows}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="section">
            <h2>🏆 Статистика по лигам</h2>

            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Лига</th>
                            <th>Сигналов</th>
                            <th>WIN</th>
                            <th>LOSE</th>
                            <th>Проходимость</th>
                            <th>ROI</th>
                        </tr>
                    </thead>

                    <tbody>
                        {league_rows}
                    </tbody>
                </table>
            </div>
        </section>

        <footer class="footer">
            Статистика загружается из PostgreSQL Neon.
            Страница обновляется каждые 180 секунд.
        </footer>

    </div>
</body>
</html>
"""


def build_error_html(error):
    """
    Страница, отображаемая при ошибке чтения базы.
    """

    return f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >
    <title>EvenOddBasketBot — ошибка</title>
</head>

<body style="
    background:#10131a;
    color:white;
    font-family:Arial;
    padding:40px;
">
    <h1>🏀 EvenOddBasketBot</h1>
    <h2>Не удалось загрузить статистику</h2>
    <p>{escape(str(error))}</p>
</body>
</html>
"""