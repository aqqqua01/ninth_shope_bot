@echo off
title Steam WebApp Server + ngrok

echo ================================
echo   Steam WebApp Server + ngrok
echo ================================
echo.

REM Перевіряємо чи встановлений ngrok
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ ngrok не встановлений!
    echo.
    echo 📥 Завантаж ngrok з https://ngrok.com/download
    echo 📋 Або встанови через chocolatey: choco install ngrok
    echo 📦 Або через winget: winget install ngrok.ngrok
    echo.
    pause
    exit /b 1
)

echo ✅ ngrok знайдено
echo.

REM Запускаємо HTTP сервер у фоні
echo 🌐 Запуск HTTP сервера на порту 8000...
start "WebApp Server" cmd /k "python start_webapp_server.py"

REM Очікуємо 2 секунди щоб сервер встиг запуститись
timeout /t 2 /nobreak >nul

echo ⚡ Запуск ngrok...
echo 🔗 Скопіюй HTTPS URL і встав у .env файл як WEBAPP_URL
echo.

REM Запускаємо ngrok
ngrok http 8000
