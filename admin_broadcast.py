"""
===========================================================
EvenOddBasketBot

Файл:
admin_broadcast.py

Назначение:
Черновики административной рассылки:
- публикация или обычный Telegram-опрос;
- предпросмотр;
- выбор аудитории;
- отправка с обычным или закреплённым сообщением;
- итоговый отчёт администратору.

Черновики хранятся в памяти процесса. После перезапуска Render
незавершённый черновик исчезнет, но база пользователей не пострадает.
===========================================================
"""

from copy import deepcopy
from threading import Lock, Thread
import time

from telegram_keyboards import create_admin_keyboard
from telegram_sender import copy_message, pin_chat_message, send_to_chat
from telegram_users import get_broadcast_recipients


_sessions = {}
_sessions_lock = Lock()


STAGE_AWAITING_POST = "awaiting_post"
STAGE_AWAITING_POLL = "awaiting_poll"
STAGE_AUDIENCE = "audience"
STAGE_DELIVERY = "delivery"
STAGE_CONFIRM = "confirm"


def start_draft(admin_id, content_kind):
    """Создаёт новый черновик публикации или опроса."""

    if content_kind not in {"post", "poll"}:
        raise ValueError("Неизвестный тип рассылки.")

    stage = STAGE_AWAITING_POLL if content_kind == "poll" else STAGE_AWAITING_POST

    with _sessions_lock:
        _sessions[int(admin_id)] = {
            "admin_id": int(admin_id),
            "content_kind": content_kind,
            "stage": stage,
            "source_chat_id": None,
            "source_message_id": None,
            "audience": None,
            "pin": False,
        }

    return get_session(admin_id)


def get_session(admin_id):
    """Возвращает копию текущего черновика администратора."""

    with _sessions_lock:
        session = _sessions.get(int(admin_id))
        return deepcopy(session) if session else None


def cancel_draft(admin_id):
    """Удаляет незавершённый черновик."""

    with _sessions_lock:
        return _sessions.pop(int(admin_id), None) is not None


def capture_content(admin_id, message):
    """Сохраняет ID сообщения, которое затем будет копироваться."""

    admin_id = int(admin_id)
    session = get_session(admin_id)

    if not session:
        return False, "Черновик рассылки не найден."

    if session["stage"] not in {STAGE_AWAITING_POST, STAGE_AWAITING_POLL}:
        return False, "Сейчас бот не ожидает содержимое публикации."

    if session["stage"] == STAGE_AWAITING_POLL and not message.get("poll"):
        return False, "Отправьте именно Telegram-опрос с помощью кнопки ниже."

    if session["stage"] == STAGE_AWAITING_POST and not _is_copyable_message(message):
        return False, "Этот тип сообщения пока нельзя использовать в рассылке."

    chat = message.get("chat") or {}
    message_id = message.get("message_id")

    if chat.get("id") is None or message_id is None:
        return False, "Telegram не передал ID сообщения. Попробуйте ещё раз."

    with _sessions_lock:
        current = _sessions.get(admin_id)

        if not current:
            return False, "Черновик рассылки уже закрыт."

        current["source_chat_id"] = int(chat["id"])
        current["source_message_id"] = int(message_id)
        current["stage"] = STAGE_AUDIENCE

    return True, None


def set_audience(admin_id, audience):
    """Сохраняет выбранную аудиторию."""

    if audience not in {"all", "premium", "free"}:
        raise ValueError("Неизвестная аудитория рассылки.")

    with _sessions_lock:
        session = _sessions.get(int(admin_id))

        if not session:
            return None

        session["audience"] = audience
        session["stage"] = STAGE_DELIVERY

    return get_session(admin_id)


def set_delivery_mode(admin_id, pin):
    """Выбирает обычную отправку или отправку с закреплением."""

    with _sessions_lock:
        session = _sessions.get(int(admin_id))

        if not session:
            return None

        session["pin"] = bool(pin)
        session["stage"] = STAGE_CONFIRM

    return get_session(admin_id)


def start_broadcast(admin_id):
    """Закрывает черновик и запускает рассылку в отдельном потоке."""

    with _sessions_lock:
        session = _sessions.get(int(admin_id))

        if not session or session.get("stage") != STAGE_CONFIRM:
            return False

        job = deepcopy(session)
        _sessions.pop(int(admin_id), None)

    thread = Thread(target=_broadcast_worker, args=(job,), daemon=True)
    thread.start()
    return True


def audience_title(audience):
    """Красивое название аудитории."""

    return {
        "all": "все активные пользователи",
        "premium": "только PREMIUM",
        "free": "только FREE",
    }.get(audience, "не выбрана")


def content_title(content_kind):
    """Красивое название типа публикации."""

    return "Telegram-опрос" if content_kind == "poll" else "публикация"


def _broadcast_worker(job):
    """Копирует публикацию получателям и отправляет итоговый отчёт."""

    admin_id = int(job["admin_id"])

    try:
        recipients = get_broadcast_recipients(job["audience"])
    except Exception as error:
        send_to_chat(
            admin_id,
            "❌ РАССЫЛКА НЕ ЗАПУЩЕНА\n\n"
            f"Не удалось получить пользователей из базы:\n{error}",
            reply_markup=create_admin_keyboard(),
        )
        return

    send_to_chat(
        admin_id,
        "⏳ РАССЫЛКА ЗАПУЩЕНА\n\n"
        f"Аудитория: {audience_title(job['audience'])}\n"
        f"Получателей: {len(recipients)}\n\n"
        "Бот сообщит результат после завершения.",
        reply_markup=create_admin_keyboard(),
    )

    sent = 0
    failed = 0
    pinned = 0
    pin_failed = 0

    for recipient in recipients:
        telegram_id = int(recipient["telegram_id"])
        result = copy_message(
            chat_id=telegram_id,
            from_chat_id=job["source_chat_id"],
            message_id=job["source_message_id"],
        )

        if result.get("ok"):
            sent += 1

            if job.get("pin"):
                sent_message_id = (result.get("result") or {}).get("message_id")

                if sent_message_id is not None:
                    pin_result = pin_chat_message(telegram_id, sent_message_id)

                    if pin_result.get("ok"):
                        pinned += 1
                    else:
                        pin_failed += 1
                else:
                    pin_failed += 1
        else:
            failed += 1
            print("Ошибка административной рассылки:", telegram_id, result)

        # Без платной массовой рассылки держим безопасную скорость.
        time.sleep(0.06)

    lines = [
        "✅ РАССЫЛКА ЗАВЕРШЕНА",
        "",
        f"Аудитория: {audience_title(job['audience'])}",
        f"Всего получателей: {len(recipients)}",
        f"Доставлено: {sent}",
        f"Ошибок отправки: {failed}",
    ]

    if job.get("pin"):
        lines.extend(
            [
                f"Закреплено: {pinned}",
                f"Ошибок закрепления: {pin_failed}",
            ]
        )

    send_to_chat(
        admin_id,
        "\n".join(lines),
        reply_markup=create_admin_keyboard(),
    )


def _is_copyable_message(message):
    """Проверяет основные типы сообщений, поддерживаемые copyMessage."""

    copyable_fields = {
        "text",
        "photo",
        "video",
        "animation",
        "audio",
        "document",
        "voice",
        "video_note",
        "sticker",
        "poll",
        "location",
        "venue",
        "contact",
        "dice",
    }

    return any(field in message for field in copyable_fields)
