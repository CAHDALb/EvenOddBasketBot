EVENODDBASKETBOT 15.0 — УСТАНОВКА НОВОГО САЙТА

1. Скопируйте все файлы из архива в корень проекта с заменой.
2. Файл .env не заменяйте.
3. Убедитесь, что на Render сохранена переменная DATABASE_URL.
4. Необязательно: добавьте DASHBOARD_TIMEZONE=Europe/Moscow.
5. Выполните:

   git add .
   git commit -m "Add live dashboard v15"
   git push

6. Дождитесь успешного Deploy. При запуске бот автоматически добавит
   столбец finished_datetime без удаления старых данных.
7. Откройте публичный URL Render. Данные обновляются автоматически.

API:
- /api/dashboard — реальные данные панели в JSON
- /api/health — проверка web-сервера
- /health — проверка Render

ВАЖНО:
- Токен Telegram и DATABASE_URL в архив не включены.
- Старые данные PostgreSQL и SQLite не удаляются.
- Для старых результатов, у которых ещё нет finished_datetime, график
  использует дату создания сигнала.
