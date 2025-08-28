FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо requirements
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код бота
COPY bot/ ./bot/

# Створюємо директорію для логів
RUN mkdir -p logs

# Встановлюємо користувача для безпеки
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Запускаємо бота
CMD ["python", "bot/bot.py"]
