ШАГ 1. СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ EVENODDBASKETBOT

Новые файлы:
- telegram_users.py
- telegram_bot.py

Заменить в проекте:
- main.py
- telegram_sender.py
- postgres_database.py
- config.py

requirements.txt не изменился.

Переменные Render:
- BOT_TOKEN — уже есть
- DATABASE_URL — уже есть
- CHAT_IDS — можно оставить как есть

Дополнительно можно создать:
- ADMIN_TELEGRAM_IDS = ваш Telegram ID
- FREE_DAILY_SIGNAL_LIMIT = 2
- TELEGRAM_POLL_TIMEOUT = 25

После запуска:
1. PostgreSQL сам создаст таблицу telegram_users.
2. ID из CHAT_IDS или ADMIN_TELEGRAM_IDS станет администратором.
3. Любой пользователь пишет боту /start.
4. Пользователь автоматически регистрируется с тарифом FREE.
5. FREE получает максимум 2 новых сигнала в сутки.
6. ADMIN получает все новые сигналы.

Команды первого этапа:
/start
/status
/myid
