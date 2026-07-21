"""
===========================================================
EvenOddBasketBot

Файл:
telegram_users.py

Назначение:
Работа с пользователями Telegram в PostgreSQL Neon:
- регистрация через /start;
- хранение тарифа;
- дневной лимит FREE;
- получение списка получателей сигнала.
===========================================================
"""

from datetime import date

from config import FREE_DAILY_SIGNAL_LIMIT
from postgres_database import get_connection


def register_user(telegram_id, first_name=None, username=None, language_code=None):
    """
    Регистрирует пользователя или обновляет его имя/username.

    Новый пользователь получает тариф FREE.
    Повторный /start не создаёт вторую запись.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO telegram_users (
                    telegram_id,
                    first_name,
                    username,
                    language_code,
                    tariff,
                    signals_today,
                    last_reset,
                    is_active
                )
                VALUES (%s, %s, %s, %s, 'free', 0, CURRENT_DATE, TRUE)
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    username = EXCLUDED.username,
                    language_code = EXCLUDED.language_code,
                    is_active = TRUE,
                    updated_at = NOW()
                RETURNING
                    telegram_id,
                    first_name,
                    username,
                    tariff,
                    signals_today,
                    last_reset,
                    premium_until,
                    is_active,
                    created_at
                """,
                (
                    int(telegram_id),
                    first_name,
                    username,
                    language_code,
                ),
            )

            row = cursor.fetchone()

    return _row_to_user(row)


def ensure_admin_user(telegram_id):
    """
    Добавляет владельца бота в базу как администратора.

    Используется для первоначального переноса ADMIN_TELEGRAM_IDS.
    Если пользователь уже существует, его текущий тариф не изменяется.
    Поэтому ручной перевод ADMIN в FREE сохраняется после перезапуска.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO telegram_users (
                    telegram_id,
                    tariff,
                    signals_today,
                    last_reset,
                    is_active
                )
                VALUES (%s, 'admin', 0, CURRENT_DATE, TRUE)
                ON CONFLICT (telegram_id)
                DO NOTHING
                """,
                (int(telegram_id),),
            )


def get_user(telegram_id):
    """Возвращает одного пользователя по Telegram ID."""

    _refresh_user_limits(telegram_id)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    telegram_id,
                    first_name,
                    username,
                    tariff,
                    signals_today,
                    last_reset,
                    premium_until,
                    is_active,
                    created_at
                FROM telegram_users
                WHERE telegram_id = %s
                """,
                (int(telegram_id),),
            )

            row = cursor.fetchone()

    return _row_to_user(row) if row else None


def get_admin_users():
    """Возвращает активных администраторов."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT telegram_id
                FROM telegram_users
                WHERE tariff = 'admin'
                  AND is_active = TRUE
                ORDER BY created_at
                """
            )

            rows = cursor.fetchall()

    return [int(row[0]) for row in rows]


def get_signal_recipients():
    """
    Возвращает пользователей, которым разрешено получить новый сигнал.

    ADMIN и PREMIUM получают все сигналы.
    FREE получает не более FREE_DAILY_SIGNAL_LIMIT сигналов в сутки.
    """

    _refresh_all_limits()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    telegram_id,
                    tariff,
                    signals_today
                FROM telegram_users
                WHERE is_active = TRUE
                  AND (
                        tariff IN ('admin', 'premium')
                        OR (
                            tariff = 'free'
                            AND signals_today < %s
                        )
                  )
                ORDER BY created_at
                """,
                (FREE_DAILY_SIGNAL_LIMIT,),
            )

            rows = cursor.fetchall()

    return [
        {
            "telegram_id": int(row[0]),
            "tariff": row[1],
            "signals_today": int(row[2]),
        }
        for row in rows
    ]



def get_broadcast_recipients(audience="all"):
    """
    Возвращает активных получателей административной рассылки.

    audience:
    - all — все активные пользователи;
    - premium — только PREMIUM;
    - free — только FREE.
    """

    audience = str(audience).lower().strip()

    if audience not in {"all", "premium", "free"}:
        raise ValueError("Неизвестная аудитория рассылки.")

    _refresh_all_limits()

    conditions = ["is_active = TRUE"]
    parameters = []

    if audience in {"premium", "free"}:
        conditions.append("tariff = %s")
        parameters.append(audience)

    where_sql = " AND ".join(conditions)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT telegram_id, tariff
                FROM telegram_users
                WHERE {where_sql}
                ORDER BY created_at, telegram_id
                """,
                tuple(parameters),
            )

            rows = cursor.fetchall()

    return [
        {
            "telegram_id": int(row[0]),
            "tariff": row[1],
        }
        for row in rows
    ]

def mark_signal_sent(telegram_id):
    """
    Увеличивает дневной счётчик только для FREE-пользователя.

    ADMIN и PREMIUM не нуждаются в ограничивающем счётчике.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET
                    signals_today = signals_today + 1,
                    updated_at = NOW()
                WHERE telegram_id = %s
                  AND tariff = 'free'
                """,
                (int(telegram_id),),
            )


def deactivate_user(telegram_id):
    """
    Отключает пользователя, например когда Telegram сообщает,
    что пользователь заблокировал бота.
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET is_active = FALSE, updated_at = NOW()
                WHERE telegram_id = %s
                """,
                (int(telegram_id),),
            )



def get_user_statistics():
    """Возвращает общую статистику пользователей для команды /users."""

    _refresh_all_limits()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE tariff = 'admin') AS admin,
                    COUNT(*) FILTER (WHERE tariff = 'premium') AS premium,
                    COUNT(*) FILTER (WHERE tariff = 'free') AS free,
                    COUNT(*) FILTER (WHERE is_active = FALSE) AS blocked,
                    COUNT(*) FILTER (
                        WHERE created_at >= CURRENT_DATE
                    ) AS today,
                    COUNT(*) FILTER (
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    ) AS last_7_days,
                    COUNT(*) FILTER (
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    ) AS last_30_days
                FROM telegram_users
                """
            )

            row = cursor.fetchone()

    return {
        "total": int(row[0] or 0),
        "admin": int(row[1] or 0),
        "premium": int(row[2] or 0),
        "free": int(row[3] or 0),
        "blocked": int(row[4] or 0),
        "today": int(row[5] or 0),
        "last_7_days": int(row[6] or 0),
        "last_30_days": int(row[7] or 0),
    }


def get_users_page(page=1, page_size=10):
    """
    Возвращает одну страницу пользователей для команды /users.

    Пользователи сортируются так:
    1. ADMIN;
    2. PREMIUM;
    3. FREE;
    4. внутри тарифа — по дате регистрации.
    """

    _refresh_all_limits()

    try:
        page = int(page)
        page_size = int(page_size)
    except (TypeError, ValueError):
        page = 1
        page_size = 10

    page = max(page, 1)
    page_size = min(max(page_size, 1), 50)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM telegram_users")
            total = int(cursor.fetchone()[0] or 0)

            pages = max((total + page_size - 1) // page_size, 1)
            page = min(page, pages)
            offset = (page - 1) * page_size

            cursor.execute(
                """
                SELECT
                    telegram_id,
                    first_name,
                    username,
                    tariff,
                    signals_today,
                    last_reset,
                    premium_until,
                    is_active,
                    created_at
                FROM telegram_users
                ORDER BY
                    CASE tariff
                        WHEN 'admin' THEN 1
                        WHEN 'premium' THEN 2
                        ELSE 3
                    END,
                    created_at,
                    telegram_id
                LIMIT %s OFFSET %s
                """,
                (page_size, offset),
            )

            rows = cursor.fetchall()

    return {
        "users": [_row_to_user(row) for row in rows],
        "page": page,
        "pages": pages,
        "page_size": page_size,
        "total": total,
    }


def set_user_tariff(telegram_id, tariff, premium_until=None):
    """Меняет тариф пользователя и при необходимости срок Premium."""

    tariff = str(tariff).lower().strip()

    if tariff not in {"free", "premium", "admin"}:
        raise ValueError("Неизвестный тариф пользователя.")

    if tariff != "premium":
        premium_until = None

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET
                    tariff = %s,
                    premium_until = %s,
                    updated_at = NOW()
                WHERE telegram_id = %s
                """,
                (tariff, premium_until, int(telegram_id)),
            )

            return cursor.rowcount > 0


def set_user_active(telegram_id, is_active):
    """Блокирует пользователя или возвращает ему доступ."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET
                    is_active = %s,
                    updated_at = NOW()
                WHERE telegram_id = %s
                """,
                (bool(is_active), int(telegram_id)),
            )

            return cursor.rowcount > 0

def get_remaining_free_signals(user):
    """Считает, сколько бесплатных сигналов осталось сегодня."""

    if not user:
        return 0

    if user["tariff"] in ("admin", "premium"):
        return None

    return max(
        FREE_DAILY_SIGNAL_LIMIT - user["signals_today"],
        0,
    )


def _refresh_user_limits(telegram_id):
    """Сбрасывает дневной счётчик и проверяет окончание Premium."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET
                    signals_today = CASE
                        WHEN last_reset <> CURRENT_DATE THEN 0
                        ELSE signals_today
                    END,
                    last_reset = CASE
                        WHEN last_reset <> CURRENT_DATE THEN CURRENT_DATE
                        ELSE last_reset
                    END,
                    tariff = CASE
                        WHEN tariff = 'premium'
                         AND premium_until IS NOT NULL
                         AND premium_until <= NOW()
                        THEN 'free'
                        ELSE tariff
                    END,
                    premium_until = CASE
                        WHEN tariff = 'premium'
                         AND premium_until IS NOT NULL
                         AND premium_until <= NOW()
                        THEN NULL
                        ELSE premium_until
                    END,
                    updated_at = NOW()
                WHERE telegram_id = %s
                """,
                (int(telegram_id),),
            )


def _refresh_all_limits():
    """Обновляет дневные лимиты и истёкшие подписки сразу у всех."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE telegram_users
                SET
                    signals_today = CASE
                        WHEN last_reset <> CURRENT_DATE THEN 0
                        ELSE signals_today
                    END,
                    last_reset = CASE
                        WHEN last_reset <> CURRENT_DATE THEN CURRENT_DATE
                        ELSE last_reset
                    END,
                    tariff = CASE
                        WHEN tariff = 'premium'
                         AND premium_until IS NOT NULL
                         AND premium_until <= NOW()
                        THEN 'free'
                        ELSE tariff
                    END,
                    premium_until = CASE
                        WHEN tariff = 'premium'
                         AND premium_until IS NOT NULL
                         AND premium_until <= NOW()
                        THEN NULL
                        ELSE premium_until
                    END,
                    updated_at = NOW()
                WHERE
                    last_reset <> CURRENT_DATE
                    OR (
                        tariff = 'premium'
                        AND premium_until IS NOT NULL
                        AND premium_until <= NOW()
                    )
                """
            )


def _row_to_user(row):
    """Переводит строку PostgreSQL в понятный словарь."""

    return {
        "telegram_id": int(row[0]),
        "first_name": row[1],
        "username": row[2],
        "tariff": row[3],
        "signals_today": int(row[4]),
        "last_reset": row[5],
        "premium_until": row[6],
        "is_active": bool(row[7]),
        "created_at": row[8],
    }
