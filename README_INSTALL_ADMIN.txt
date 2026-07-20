EVENODDBASKETBOT — УСТАНОВКА АДМИН-ПАНЕЛИ

1. Скопируйте в проект новые/обновлённые файлы:
   - admin_commands.py
   - telegram_bot.py
   - telegram_users.py
   - папку docs

2. Запустите локальную проверку:
   python -m py_compile admin_commands.py telegram_bot.py telegram_users.py

3. Отправьте изменения на GitHub:
   git add .
   git commit -m "Add Telegram admin panel v0.7"
   git push

4. После обновления Render проверьте в Telegram:
   /users

5. Друг должен открыть бота и отправить:
   /start

6. После регистрации друг появится в /users и сможет получать до 2 FREE-сигналов в день.
