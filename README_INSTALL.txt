EvenOddBasketBot — список пользователей в /users

Что изменено:
1. /users показывает общую статистику и список пользователей.
2. Для каждого пользователя выводятся имя, username, Telegram ID, тариф и блокировка.
3. Добавлена пагинация по 10 пользователей:
   /users
   /users 2
4. Сохранена защита: администратор не может снять права ADMIN у самого себя,
   но может перевести другого администратора на FREE.

Какие файлы заменить в проекте:
- admin_commands.py
- telegram_users.py

После замены:
1. git add admin_commands.py telegram_users.py
2. git commit -m "Show users list in admin panel"
3. git push
4. Дождаться нового Deploy на Render.
5. В Telegram отправить /users

ВАЖНО:
На Render в переменной ADMIN_TELEGRAM_IDS должен остаться только ID владельца.
Если переменная не создана, проверь CHAT_IDS. Иначе ID друга снова получит ADMIN
при следующем перезапуске сервера.
