@echo off
echo 🔗 Запуск Webhook сервера з ngrok
echo.

echo 1️⃣ Запускаємо бота...
start "Telegram Bot" cmd /k "cd /d %~dp0 && cd bot && python bot.py"

echo.
echo 2️⃣ Очікуємо 5 секунд для запуску бота...
timeout /t 5

echo.
echo 3️⃣ Запускаємо ngrok тунель...
echo 📋 Скопіюйте HTTPS URL та додайте в .env файл як WEBHOOK_URL
echo.
ngrok.exe http 8003

pause

