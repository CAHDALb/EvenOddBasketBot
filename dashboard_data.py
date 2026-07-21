"""
===========================================================
EvenOddBasketBot

Файл:
dashboard_data.py

Назначение:
Собирает единый JSON-снимок для публичной web-панели.
Основной источник — PostgreSQL Neon. При локальном запуске
возможен безопасный резервный переход на SQLite.
===========================================================
"""

from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from branding import BRAND_VERSION
from config import CHECK_INTERVAL


PROJECT_DIR = Path(__file__).resolve().parent
SQLITE_PATH = PROJECT_DIR / "evenodd.db"
DASHBOARD_TIMEZONE = os.getenv("DASHBOARD_TIMEZONE", "Europe/Moscow")
MAX_PUBLIC_SIGNALS = 100
MAX_ROI_POINTS = 240

MATCH_TYPE_ORDER = ("men", "youth", "women")
MATCH_TYPE_LABELS = {
    "men": "Мужские",
    "youth": "Молодёжные",
    "women": "Женские",
    "unknown": "Не определено",
}


def _get_timezone() -> ZoneInfo:
    """Возвращает часовую зону панели без риска падения сервера."""

    try:
        return ZoneInfo(DASHBOARD_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _as_datetime(value: Any) -> datetime:
    """Приводит PostgreSQL/SQLite значение даты к aware datetime."""

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
    elif value:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            parsed = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    else:
        parsed = datetime.now(timezone.utc)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def _normalise_row(row: dict[str, Any], tz: ZoneInfo) -> dict[str, Any]:
    """Нормализует одну строку сигнала из любой поддерживаемой БД."""

    signal_dt = _as_datetime(row.get("signal_datetime"))
    finished_raw = row.get("finished_datetime")
    finished_dt = _as_datetime(finished_raw) if finished_raw else None

    return {
        "id": str(row.get("id") or ""),
        "strategy": row.get("strategy") or "odd_total",
        "match_type": row.get("match_type") or "unknown",
        "country": row.get("country") or "Неизвестная страна",
        "league": row.get("league") or "Неизвестная лига",
        "home": row.get("home") or "Команда 1",
        "away": row.get("away") or "Команда 2",
        "signal_datetime": signal_dt.astimezone(tz),
        "finished_datetime": (
            finished_dt.astimezone(tz) if finished_dt else None
        ),
        "prediction": (row.get("prediction") or "odd").lower(),
        "status": (row.get("status") or "waiting").lower(),
        "result": (row.get("result") or "").lower() or None,
        "roi": float(row.get("roi") or 0),
        "final_total": row.get("final_total"),
        "match_url": row.get("match_url") or "",
    }


def _fetch_postgres_rows() -> list[dict[str, Any]]:
    """Читает сигналы из Neon/PostgreSQL."""

    # Ленивый импорт позволяет локально открыть панель через SQLite,
    # даже если PostgreSQL-зависимость ещё не установлена.
    from postgres_database import get_connection as get_postgres_connection

    query_with_finished = """
        SELECT
            id, strategy, match_type, country, league,
            home, away, signal_datetime, finished_datetime,
            prediction, status, result, roi, final_total, match_url
        FROM signals
        ORDER BY signal_datetime ASC, id ASC
    """

    query_legacy = """
        SELECT
            id, strategy, match_type, country, league,
            home, away, signal_datetime,
            prediction, status, result, roi, final_total, match_url
        FROM signals
        ORDER BY signal_datetime ASC, id ASC
    """

    with get_postgres_connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(query_with_finished)
                columns = [description.name for description in cursor.description]
            except Exception:
                connection.rollback()
                cursor.execute(query_legacy)
                columns = [description.name for description in cursor.description]

            rows = cursor.fetchall()

    return [dict(zip(columns, row)) for row in rows]


def _fetch_sqlite_rows() -> list[dict[str, Any]]:
    """Читает локальный резерв SQLite, если он существует."""

    if not SQLITE_PATH.is_file():
        raise RuntimeError("Резервная SQLite не найдена")

    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(signals)").fetchall()
        }
        finished_column = (
            "finished_datetime" if "finished_datetime" in columns else "NULL"
        )
        rows = connection.execute(
            f"""
            SELECT
                id, strategy, match_type, country, league,
                home, away, signal_datetime,
                {finished_column} AS finished_datetime,
                prediction, status, result, roi, final_total, match_url
            FROM signals
            ORDER BY signal_datetime ASC, id ASC
            """
        ).fetchall()
    finally:
        connection.close()

    return [dict(row) for row in rows]


def _load_rows() -> tuple[list[dict[str, Any]], str, bool, str]:
    """Загружает данные с безопасным резервным источником."""

    postgres_error = None

    if os.getenv("DATABASE_URL"):
        try:
            return _fetch_postgres_rows(), "PostgreSQL Neon", True, ""
        except Exception as error:  # Логируем только на сервере.
            postgres_error = error
            print("Dashboard: PostgreSQL недоступен:", error)

    try:
        return _fetch_sqlite_rows(), "SQLite backup", True, ""
    except Exception as sqlite_error:
        print("Dashboard: SQLite недоступна:", sqlite_error)

    message = "Нет подключения к базе данных"
    if not os.getenv("DATABASE_URL"):
        message = "DATABASE_URL не настроен"
    elif postgres_error:
        message = "База данных временно недоступна"

    return [], "Нет источника", False, message


def _finished_time(item: dict[str, Any]) -> datetime:
    """Дата результата; для старых записей — дата создания сигнала."""

    return item["finished_datetime"] or item["signal_datetime"]


def _percent(wins: int, loses: int) -> float:
    total = wins + loses
    return wins / total * 100 if total else 0.0


def _group_stats(
    finished: list[dict[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}

    for item in finished:
        key = str(item.get(field) or "Не определено")
        bucket = groups.setdefault(
            key,
            {"key": key, "total": 0, "wins": 0, "loses": 0, "roi": 0.0},
        )
        bucket["total"] += 1
        bucket["wins"] += int(item["result"] == "win")
        bucket["loses"] += int(item["result"] == "lose")
        bucket["roi"] += item["roi"]

    result = []
    for bucket in groups.values():
        bucket["win_rate"] = _percent(bucket["wins"], bucket["loses"])
        bucket["roi"] = round(bucket["roi"], 2)
        result.append(bucket)

    result.sort(key=lambda item: (item["total"], item["roi"]), reverse=True)
    return result


def _match_type_stats(finished: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped = {item["key"]: item for item in _group_stats(finished, "match_type")}
    cards = []

    for match_type in MATCH_TYPE_ORDER:
        source = grouped.get(
            match_type,
            {
                "key": match_type,
                "total": 0,
                "wins": 0,
                "loses": 0,
                "win_rate": 0.0,
                "roi": 0.0,
            },
        )
        cards.append(
            {
                **source,
                "label": MATCH_TYPE_LABELS[match_type],
            }
        )

    unknown = grouped.get("unknown")
    if unknown and unknown["total"]:
        cards.append({**unknown, "label": MATCH_TYPE_LABELS["unknown"]})

    return cards


def _downsample(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Уменьшает длинную историю, сохраняя начало и последний результат."""

    if len(items) <= limit:
        return items

    step = (len(items) - 1) / (limit - 1)
    indexes = {round(index * step) for index in range(limit)}
    indexes.add(len(items) - 1)
    return [items[index] for index in sorted(indexes)]


def _public_signal(item: dict[str, Any]) -> dict[str, Any]:
    event_time = _finished_time(item) if item["status"] == "finished" else item["signal_datetime"]

    return {
        "id": item["id"],
        "datetime": event_time.isoformat(),
        "signal_datetime": item["signal_datetime"].isoformat(),
        "home": item["home"],
        "away": item["away"],
        "match": f'{item["home"]} — {item["away"]}',
        "country": item["country"],
        "league": item["league"],
        "match_type": item["match_type"],
        "match_type_label": MATCH_TYPE_LABELS.get(
            item["match_type"],
            MATCH_TYPE_LABELS["unknown"],
        ),
        "prediction": item["prediction"],
        "status": item["status"],
        "result": item["result"],
        "roi": round(item["roi"], 2),
        "final_total": item["final_total"],
        "match_url": item["match_url"],
    }


def _risk_snapshot(recent_finished: list[dict[str, Any]]) -> dict[str, str]:
    sample = recent_finished[:10]
    wins = sum(item["result"] == "win" for item in sample)
    total = len(sample)

    if total < 10:
        return {
            "level": "neutral",
            "title": "Недостаточно данных",
            "message": f"В короткой выборке пока {total} завершённых сигналов из 10.",
        }
    if wins <= 4:
        return {
            "level": "danger",
            "title": "Повышенная осторожность",
            "message": f"Последняя форма: {wins} WIN из 10 сигналов.",
        }
    if wins <= 6:
        return {
            "level": "warning",
            "title": "Умеренная форма",
            "message": f"Последняя форма: {wins} WIN из 10 сигналов.",
        }
    return {
        "level": "positive",
        "title": "Положительная форма",
        "message": f"Последняя форма: {wins} WIN из 10 сигналов.",
    }


def _current_streak(recent_finished: list[dict[str, Any]]) -> dict[str, Any]:
    if not recent_finished:
        return {"result": None, "length": 0}

    result = recent_finished[0]["result"]
    length = 0
    for item in recent_finished:
        if item["result"] != result:
            break
        length += 1

    return {"result": result, "length": length}


def build_dashboard_payload() -> dict[str, Any]:
    """Возвращает полный снимок публичной панели."""

    tz = _get_timezone()
    raw_rows, source, online, source_message = _load_rows()
    rows = [_normalise_row(row, tz) for row in raw_rows]

    finished = [
        item
        for item in rows
        if item["status"] == "finished" and item["result"] in {"win", "lose"}
    ]
    finished.sort(key=_finished_time)
    recent_finished = list(reversed(finished))
    waiting = [item for item in rows if item["status"] == "waiting"]
    waiting.sort(key=lambda item: item["signal_datetime"], reverse=True)

    wins = sum(item["result"] == "win" for item in finished)
    loses = sum(item["result"] == "lose" for item in finished)
    roi = round(sum(item["roi"] for item in finished), 2)

    cumulative = 0.0
    roi_history = []
    for index, item in enumerate(finished, start=1):
        cumulative += item["roi"]
        roi_history.append(
            {
                "index": index,
                "datetime": _finished_time(item).isoformat(),
                "roi": round(cumulative, 2),
                "result": item["result"],
            }
        )
    roi_history = _downsample(roi_history, MAX_ROI_POINTS)

    today = datetime.now(tz).date()
    first_day = today - timedelta(days=29)
    daily_map = {first_day + timedelta(days=offset): 0.0 for offset in range(30)}
    for item in finished:
        day = _finished_time(item).date()
        if day in daily_map:
            daily_map[day] += item["roi"]

    bank_daily = [
        {
            "date": day.isoformat(),
            "value": round(value, 2),
        }
        for day, value in daily_map.items()
    ]

    all_signals_desc = sorted(
        rows,
        key=lambda item: item["signal_datetime"],
        reverse=True,
    )

    countries = _group_stats(finished, "country")[:25]
    leagues = _group_stats(finished, "league")[:25]
    match_types = _match_type_stats(finished)
    win_rate = _percent(wins, loses)
    streak = _current_streak(recent_finished)

    return {
        "generated_at": datetime.now(tz).isoformat(),
        "timezone": str(tz),
        "refresh_seconds": max(15, min(CHECK_INTERVAL, 300)),
        "version": BRAND_VERSION,
        "system": {
            "online": online,
            "source": source,
            "message": source_message,
        },
        "summary": {
            "total": len(rows),
            "waiting": len(waiting),
            "finished": wins + loses,
            "wins": wins,
            "loses": loses,
            "win_rate": round(win_rate, 2),
            "roi": roi,
        },
        "strategy": {
            "name": "Чётность общего тотала Q4",
            "sample": wins + loses,
            "wins": wins,
            "loses": loses,
            "win_rate": round(win_rate, 2),
            "roi": roi,
            "streak": streak,
        },
        "roi_history": roi_history,
        "bank_daily": bank_daily,
        "recent_signals": [
            _public_signal(item) for item in recent_finished[:10]
        ],
        "signals": [
            _public_signal(item) for item in all_signals_desc[:MAX_PUBLIC_SIGNALS]
        ],
        "waiting_signals": [
            _public_signal(item) for item in waiting[:50]
        ],
        "match_types": match_types,
        "countries": countries,
        "leagues": leagues,
        "risk": _risk_snapshot(recent_finished),
    }
