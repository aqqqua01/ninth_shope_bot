#!/bin/bash

echo "Starting Steam Top-Up Bot..."

# Перевіряємо чи існує .env файл
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy env.example to .env and configure it."
    exit 1
fi

# Перевіряємо чи існує venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Активуємо venv та встановлюємо залежності
source venv/bin/activate
pip install -r requirements.txt

# Запускаємо бота
echo "Bot starting..."
cd bot
python bot.py
