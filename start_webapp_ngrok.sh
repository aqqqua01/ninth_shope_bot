#!/bin/bash

echo "==============================="
echo "  Steam WebApp Server + ngrok"
echo "==============================="
echo

# Перевіряємо чи встановлений ngrok
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok не встановлений!"
    echo
    echo "📥 Завантаж ngrok з https://ngrok.com/download"
    echo "📋 Або встанови через brew: brew install ngrok"
    echo "📦 Або через snap: snap install ngrok"
    echo
    exit 1
fi

echo "✅ ngrok знайдено"
echo

# Запускаємо HTTP сервер у фоні
echo "🌐 Запуск HTTP сервера на порту 8000..."
python3 start_webapp_server.py &
SERVER_PID=$!

# Очікуємо 2 секунди щоб сервер встиг запуститись
sleep 2

echo "⚡ Запуск ngrok..."
echo "🔗 Скопіюй HTTPS URL і встав у .env файл як WEBAPP_URL"
echo

# Функція для очищення при виході
cleanup() {
    echo
    echo "🛑 Зупинка сервера..."
    kill $SERVER_PID 2>/dev/null
    exit
}

# Встановлюємо обробник сигналів
trap cleanup SIGINT SIGTERM

# Запускаємо ngrok
ngrok http 8000
