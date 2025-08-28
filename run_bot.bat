@echo off
echo Starting Steam Top-Up Bot...

REM Перевіряємо чи існує .env файл
if not exist .env (
    echo Error: .env file not found!
    echo Please copy env.example to .env and configure it.
    pause
    exit /b 1
)

REM Перевіряємо чи існує venv
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активуємо venv та встановлюємо залежності
call venv\Scripts\activate
pip install -r requirements.txt

REM Запускаємо бота
echo Bot starting...
cd bot
python bot.py

pause
