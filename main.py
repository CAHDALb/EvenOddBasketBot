import time
from statistics import print_total_statistics
from config import CHECK_INTERVAL
from parser import get_matches
from strategy import check_strategy
from telegram_sender import send_telegram
from storage import load_sent_matches, save_sent_matches
from database import add_signal
from sqlite_database import create_tables
from results import check_all_waiting_signals
import threading
from web_server import run_web_server
from notifications import create_start_message, create_error_message

print("MAIN.PY ЗАГРУЖЕН")

def main():
    """
    Главный цикл программы.
    """

    # Загружаем уже отправленные матчи
    sent_matches = load_sent_matches()

    print("Бот запущен...")
    print("Render heartbeat: основной цикл main() запущен")

    # Создаём таблицы SQLite, если их ещё нет
    create_tables()

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
                # Формируем сообщение для Telegram
                # =====================================================
                message = (
                    "🚨 СИГНАЛ ПО СТРАТЕГИИ 🚨\n\n"
                    f"🌍 {match.get('country')}\n"
                    f"🏆 {match.get('league')}\n\n"
                    f"🏀 {home} - {away}\n\n"
                    f"{stage}\n\n"
                    f"Q1 = {q1}\n"
                    f"Q2 = {q2}\n"
                    f"Q3 = {q3}\n\n"
                    "✅ Все три четверти имеют одинаковую четность.\n\n"
                    f"🆔 ID: {match['id']}\n"
                    f"🔗 {match_url}"
                )

                # Сначала запоминаем матч, чтобы при перезапуске не отправить его повторно
                sent_matches.add(match_id)
                save_sent_matches(sent_matches)

                # Сохраняем сигнал в базу
                add_signal(match)

                # Только после сохранения отправляем сообщение
                result = send_telegram(message)

                if result.get("ok"):
                    print("Сообщение отправлено.")
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

        # Запускаем основного бота
        main()

    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")