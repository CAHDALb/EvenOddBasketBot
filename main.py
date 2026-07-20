import time
from analytics import (
    build_signal_passport,
    get_recent_statistics,
    get_risk_indicator,
)
from statistics import print_total_statistics
from config import CHECK_INTERVAL
from parser import get_matches
from strategy import check_strategy
from telegram_sender import send_telegram, send_signal
from storage import load_sent_matches, save_sent_matches
from database import add_signal
from sqlite_database import create_tables as create_sqlite_tables
from postgres_database import create_tables as create_postgres_tables
from results import check_all_waiting_signals
import threading
from web_server import run_web_server
from notifications import create_start_message, create_error_message
from telegram_bot import run_telegram_bot
from telegram_users import ensure_admin_user
from config import ADMIN_TELEGRAM_IDS

print("MAIN.PY ЗАГРУЖЕН")

def main():
    """
    Главный цикл программы.
    """

    # Загружаем уже отправленные матчи
    sent_matches = load_sent_matches()

    print("Бот запущен...")
    print("Render heartbeat: основной цикл main() запущен")

    # Создаём таблицы SQLite и PostgreSQL, если их ещё нет
    create_sqlite_tables()
    create_postgres_tables()

    # Первоначально добавляем владельца из ADMIN_TELEGRAM_IDS.
    # Уже существующие тарифы при перезапуске не перезаписываются.
    for admin_id in ADMIN_TELEGRAM_IDS:
        ensure_admin_user(admin_id)

    send_telegram(create_start_message())

    while True:

        print("\nПроверка матчей...")
        print("Heartbeat: бот продолжает работать")

        # Получаем список матчей
        try:
            matches = get_matches()
        except Exception as error:
            print("Ошибка при получении матчей:", error)

            # Отправляем сообщение об ошибке в Telegram
            send_telegram(create_error_message(error))

            print("Ждём следующую проверку...")
            time.sleep(CHECK_INTERVAL)
            continue

        # Проверяем каждый матч
        for match in matches:

            match_id = match["id"]

            if not match_id:
                continue

            if match_id in sent_matches:
                continue

            if check_strategy(match):

                # =====================================================
                # ОТЛАДКА
                # Показываем информацию о найденном сигнале
                # =====================================================
                print("=" * 60)
                print("🏀 НАЙДЕН СИГНАЛ")
                print("ID       :", match["id"])
                print("Страна   :", match["country"])
                print("Лига     :", match["league"])
                print("Команды  :", match["home_name"], "-", match["away_name"])
                print("Четверть :", match["quarter"])
                print("Q1       :", match["q1_total"])
                print("Q2       :", match["q2_total"])
                print("Q3       :", match["q3_total"])
                print("=" * 60)

                # =====================================================
                # Получаем данные матча
                # =====================================================
                home = match["home_name"]
                away = match["away_name"]

                q1 = match["q1_total"]
                q2 = match["q2_total"]
                q3 = match["q3_total"]

                stage = "🏀 4-я четверть"

                match_url = match["match_url"]

                # =====================================================
                # Получаем историческую аналитику по сигналу
                # =====================================================
                passport = build_signal_passport(match)

                country_stats = passport["country"]
                league_stats = passport["league"]
                type_stats = passport["match_type"]

                # =====================================================
                # Получаем последние результаты всей стратегии
                # =====================================================
                recent_stats = get_recent_statistics(limit=10)
                risk = get_risk_indicator(recent_stats)

                # Если результатов ещё нет
                if recent_stats["total"] == 0:
                    recent_history_text = "Пока нет завершённых сигналов."
                    recent_summary_text = "WIN: 0 | LOSE: 0"
                    streak_text = "Текущая серия: отсутствует"

                else:
                    recent_history_text = recent_stats["history_line"]

                    recent_summary_text = (
                        f"WIN: {recent_stats['wins']} из {recent_stats['total']}\n"
                        f"Проходимость: {recent_stats['win_rate']:.2f}%"
                    )

                    streak = recent_stats["streak"]

                    if streak["result"] == "win":
                        streak_name = "WIN 🟢"
                    elif streak["result"] == "lose":
                        streak_name = "LOSE 🔴"
                    else:
                        streak_name = "отсутствует"

                    streak_text = (
                        f"Текущая серия: "
                        f"{streak['length']} {streak_name}"
                    )

                type_names = {
                    "men": "👨 Мужские",
                    "women": "👩 Женские",
                    "youth": "👦 Молодёжные",
                }

                match_type_name = type_names.get(
                    type_stats["value"],
                    type_stats["value"],
                )

                # =====================================================
                # Формируем сообщение для Telegram
                # =====================================================
                message = (
                    "🚨 СИГНАЛ ПО СТРАТЕГИИ 🚨\n\n"

                    f"🌍 {match.get('country')}\n"
                    f"🏆 {match.get('league')}\n"
                    f"📂 {match_type_name}\n\n"

                    f"🏀 {home} - {away}\n\n"

                    f"{stage}\n\n"

                    f"Q1 = {q1}\n"
                    f"Q2 = {q2}\n"
                    f"Q3 = {q3}\n\n"

                    "✅ Все три четверти имеют одинаковую чётность.\n\n"

                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "📈 ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ\n\n"

                    f"{recent_history_text}\n\n"
                    f"{recent_summary_text}\n"
                    f"{streak_text}\n\n"

                    f"{risk['icon']} {risk['title']}\n"
                    f"{risk['message']}\n\n"

                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "📊 ИСТОРИЯ СТРАТЕГИИ\n\n"

                    f"🌍 Страна: {country_stats['value']}\n"
                    f"Сигналов: {country_stats['total']}\n"
                    f"Проходимость: {country_stats['win_rate']:.2f}%\n"
                    f"ROI: {country_stats['roi']:+.2f}\n\n"

                    f"🏆 Лига: {league_stats['value']}\n"
                    f"Сигналов: {league_stats['total']}\n"
                    f"Проходимость: {league_stats['win_rate']:.2f}%\n"
                    f"ROI: {league_stats['roi']:+.2f}\n\n"

                    f"📂 Категория: {match_type_name}\n"
                    f"Сигналов: {type_stats['total']}\n"
                    f"Проходимость: {type_stats['win_rate']:.2f}%\n"
                    f"ROI: {type_stats['roi']:+.2f}\n\n"

                    "━━━━━━━━━━━━━━━━━━━━\n"
                    "📚 SIGNAL SCORE\n\n"
                    "Пока не рассчитан.\n"
                    "Идёт накопление статистики.\n\n"

                    f"🆔 ID: {match['id']}\n"
                    f"🔗 {match_url}"
                )

                # Сначала запоминаем матч, чтобы при перезапуске не отправить его повторно
                # =====================================================
                # Сохраняем сигнал в базу
                # =====================================================
                saved = add_signal(match)

                if not saved:
                    print("Сигнал не удалось сохранить в базу.")
                    continue

                # =====================================================
                # Отправляем сообщение в Telegram
                # =====================================================
                result = send_signal(message)

                if result.get("ok"):

                    print(
                        "Сигнал отправлен. Получателей:",
                        result.get("sent", 0),
                    )

                    # Только после успешной отправки считаем,
                    # что матч уже обработан
                    sent_matches.add(match_id)
                    save_sent_matches(sent_matches)

                else:

                    print("Ошибка Telegram:")
                    print(result)
        # =====================================================
        # Проверяем результаты ранее найденных сигналов
        # =====================================================
        print("\nПроверяем результаты завершённых матчей...")
        check_all_waiting_signals()

        # Показываем текущее состояние базы в логах
        print_total_statistics()

        print(f"\nСледующая проверка через {CHECK_INTERVAL} секунд...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":

    try:
        # Запускаем маленький web-сервер для Render
        web_thread = threading.Thread(target=run_web_server)
        web_thread.daemon = True
        web_thread.start()

        # Запускаем обработчик Telegram-команд (/start, /status)
        telegram_thread = threading.Thread(target=run_telegram_bot)
        telegram_thread.daemon = True
        telegram_thread.start()

        # Запускаем основного бота
        main()

    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")