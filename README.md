# Steam Top-Up Telegram Bot 🎮

Telegram бот для пополнения Steam кошелька через Telegram WebApp с автоматическим расчетом комиссии и уведомлениями администратора.

## ✨ Возможности

- **Telegram WebApp** - удобная форма для ввода данных прямо в Telegram
- **Автоматический расчет** - комиссия +15% рассчитывается автоматически
- **Безопасность** - проверка подлинности данных WebApp через криптографические подписи
- **Админ панель** - получение всех заявок с полной информацией о пользователе
- **Локализация** - весь интерфейс на русском языке
- **Валидация** - серверная проверка всех данных

## 📁 Структура проекта

```
steam_topup_webapp_bot/
├── bot/                    # Backend бота
│   ├── bot.py             # Основной файл бота
│   └── requirements.txt   # Зависимости Python
├── webapp/                # Frontend WebApp
│   └── index.html         # HTML форма с JavaScript
├── env.example           # Пример конфигурации
├── requirements.txt      # Зависимости проекта
└── README.md            # Документация
```

## 🚀 Быстрый старт

### 1. Создание Telegram бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Сохраните полученный токен бота

### 2. Получение ADMIN_CHAT_ID

1. Запустите бота после настройки
2. Отправьте команду `/admin` в чат с ботом
3. Скопируйте Chat ID из ответа

### 3. Установка и настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd steam_topup_webapp_bot

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt

# Создайте .env файл
cp env.example .env
```

### 4. Настройка .env файла

Отредактируйте `.env` файл:

```env
# Telegram Bot Configuration
BOT_TOKEN=1234567890:AAAA-BBBB-CCCC-DDDD

# Admin Configuration  
ADMIN_CHAT_ID=123456789
FORWARD_CHAT_ID=987654321

# Payment Configuration
PAYMENT_DETAILS=Номер карты: 4441 1144 1111 1111\nПолучатель: Иван Иванов\nБанк: ПриватБанк
CURRENCY=UAH

# WebApp Configuration
WEBAPP_URL=https://your-webapp-url.com
```

### 5. Запуск бота

```bash
cd bot
python bot.py
```

## 🌐 Развертывание WebApp

WebApp должен быть доступен по HTTPS. Варианты хостинга:

### Vercel (рекомендуется)

1. Создайте аккаунт на [Vercel](https://vercel.com)
2. Подключите GitHub репозиторий
3. Укажите папку `webapp` как корневую директорию
4. Разверните проект
5. Скопируйте полученный URL в `WEBAPP_URL`

### GitHub Pages

1. Перейдите в Settings → Pages вашего репозитория
2. Выберите источник: Deploy from a branch
3. Выберите ветку и папку `/webapp`
4. Сохраните и получите URL

### Netlify

1. Зарегистрируйтесь на [Netlify](https://netlify.com)
2. Подключите GitHub репозиторий
3. Укажите папку `webapp` для публикации
4. Разверните и получите URL

## 🐳 Docker развертывание

### Dockerfile для бота

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY bot/ ./bot/
COPY .env .

CMD ["python", "bot/bot.py"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  steam-bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_CHAT_ID=${ADMIN_CHAT_ID}
      - FORWARD_CHAT_ID=${FORWARD_CHAT_ID}
      - PAYMENT_DETAILS=${PAYMENT_DETAILS}
      - CURRENCY=${CURRENCY}
      - WEBAPP_URL=${WEBAPP_URL}
    restart: unless-stopped
```

### Запуск через Docker

```bash
docker-compose up -d
```

## 🔧 Systemd сервис (Linux)

Создайте файл `/etc/systemd/system/steam-bot.service`:

```ini
[Unit]
Description=Steam Top-Up Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/steam_topup_webapp_bot
Environment=PATH=/home/ubuntu/steam_topup_webapp_bot/venv/bin
ExecStart=/home/ubuntu/steam_topup_webapp_bot/venv/bin/python bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable steam-bot
sudo systemctl start steam-bot
sudo systemctl status steam-bot
```

## 📋 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и отображение кнопки WebApp |
| `/help` | Справка по использованию |
| `/cancel` | Отмена текущей операции |
| `/admin` | Получение User ID и Chat ID (для настройки) |

## 💡 Как использовать

1. **Пользователь** отправляет `/start`
2. **Пользователь** нажимает "🎮 Оформить пополнение"
3. **Открывается WebApp** с формой:
   - Логин Steam (обязательно)
   - Сумма пополнения (поддержка "." и ",")
   - Автоматический расчет +15%
   - Реквизиты для оплаты
4. **Пользователь** заполняет форму и нажимает "Подтвердить"
5. **Бот отправляет**:
   - Пользователю: подтверждение с суммой и реквизитами
   - Админу: полную информацию о заявке

## 🔒 Безопасность

- ✅ Проверка подлинности WebApp данных через HMAC
- ✅ Серверная валидация всех входных данных
- ✅ Пересчет сумм на сервере (не доверяем клиенту)
- ✅ Логирование без секретных данных
- ✅ HTTPS обязателен для WebApp

## 🧪 Тестирование

### Чек-лист для тестирования

- [ ] `/start` показывает кнопку WebApp
- [ ] WebApp открывается в Telegram
- [ ] Автоматический расчет +15% работает
- [ ] Валидация формы работает корректно
- [ ] Серверная проверка пересчитывает суммы
- [ ] Пользователь получает подтверждение
- [ ] Админ получает полную информацию о заявке
- [ ] `/cancel` и `/admin` работают в любой момент
- [ ] Все тексты на русском языке
- [ ] Валюта отображается согласно настройкам
- [ ] Проверка подписи WebApp отклоняет поддельные данные

### Модульные тесты

```python
# Тест парсинга суммы
def test_parse_amount():
    assert parse_amount("100") == Decimal("100.00")
    assert parse_amount("100,50") == Decimal("100.50")
    assert parse_amount("100.75") == Decimal("100.75")

# Тест расчета комиссии
def test_calculate_total():
    assert calculate_total(Decimal("100")) == Decimal("115.00")
    assert calculate_total(Decimal("50.50")) == Decimal("58.08")
```

## 📊 Мониторинг и логи

Бот ведет структурированные логи:

```
2024-01-15 10:30:00 - INFO - Запуск Steam Top-Up Bot...
2024-01-15 10:30:15 - INFO - Получены WebApp данные: {...}
2024-01-15 10:30:16 - INFO - Обработана заявка от пользователя 123456: steamuser, 100.00 UAH
```

## ⚠️ Важные замечания

1. **WEBAPP_URL** должен использовать HTTPS
2. **BOT_TOKEN** никогда не должен попадать в логи
3. **Комиссия** всегда пересчитывается на сервере
4. **Валюта** настраивается через переменную окружения
5. **Реквизиты** должны быть настроены перед запуском

## 🆘 Устранение неполадок

### WebApp не открывается
- Проверьте правильность WEBAPP_URL в .env
- Убедитесь что URL использует HTTPS
- Проверьте доступность хостинга WebApp

### Бот не отвечает
- Проверьте правильность BOT_TOKEN
- Убедитесь что бот запущен
- Проверьте логи на наличие ошибок

### Админ не получает уведомления
- Проверьте правильность ADMIN_CHAT_ID
- Убедитесь что бот может отправлять сообщения в админ чат

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Убедитесь в правильности всех переменных окружения
3. Проверьте доступность WebApp по HTTPS
4. Создайте issue в репозитории с подробным описанием проблемы

## 📝 Лицензия

MIT License - смотрите файл LICENSE для подробностей.
