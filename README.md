# Steam Top-Up Telegram Bot

Telegram бот для поповнення Steam гаманця через WebApp інтерфейс з GitHub Pages хостингом.

## Особливості

- 🎮 Зручний WebApp інтерфейс для введення даних
- 💰 Автоматичний розрахунок комісії (+15%)
- 🔒 Безпечна верифікація даних WebApp
- 📱 Адаптивний дизайн для мобільних пристроїв
- 🚀 Автоматичний деплой на GitHub Pages
- 🌐 Підтримка кастомних реквізитів та валют

## Архітектура

### Компоненти

1. **Telegram Bot** (`bot/`) - Python бот на базі python-telegram-bot
2. **WebApp** (`webapp/`) - HTML/JS додаток для введення даних
3. **GitHub Pages** - Хостинг для WebApp

### Workflow

1. Користувач викликає команду `/start`
2. Бот показує кнопку для відкриття WebApp
3. Користувач заповнює форму в WebApp
4. WebApp відправляє дані назад в бот
5. Бот валідує дані та відправляє підтвердження

## Швидкий старт

### 1. Клонування та налаштування

```bash
git clone <repository-url>
cd ninth_shope_bot
cp .env.example .env
```

### 2. Налаштування змінних оточення

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
WEBAPP_URL=https://username.github.io/repository-name/
CURRENCY=UAH
PAYMENT_DETAILS="Номер карти: 4441 1144 1111 1111\nОтримувач: Іван Іванов"
```

### 3. Деплой WebApp на GitHub Pages

Детальна інструкція: [docs/GITHUB_PAGES_SETUP.md](docs/GITHUB_PAGES_SETUP.md)

Коротко:
1. Зіпуште код на GitHub
2. Увімкніть GitHub Pages з GitHub Actions
3. Скопіюйте URL у WEBAPP_URL

### 4. Запуск бота

```bash
# Docker
docker-compose up -d

# Або локально
cd bot
pip install -r requirements.txt
python bot.py
```

## Конфігурація

### WebApp налаштування

Редагуйте `webapp/config.js`:

```javascript
const WEBAPP_CONFIG = {
    currency: 'UAH',
    commissionRate: 0.15,
    defaultPaymentDetails: 'Ваші реквізити...'
};
```

### Змінні оточення бота

| Змінна | Опис | Обов'язкова |
|--------|------|-------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `ADMIN_CHAT_ID` | ID чату адміністратора | ✅ |
| `WEBAPP_URL` | URL WebApp на GitHub Pages | ✅ |
| `FORWARD_CHAT_ID` | Додатковий чат для пересилання | ❌ |
| `CURRENCY` | Валюта (за замовчуванням UAH) | ❌ |
| `PAYMENT_DETAILS` | Реквізити для оплати | ❌ |

## Команди бота

- `/start` - Запуск та показ WebApp кнопки
- `/help` - Довідка по використанню
- `/cancel` - Скасування поточної операції
- `/admin` - Інформація для адміністратора

## Безпека

- ✅ Верифікація WebApp даних через HMAC-SHA256
- ✅ Серверна валідація всіх вхідних даних
- ✅ Перерахунок комісії на сервері
- ✅ Логування без чутливих даних
- ✅ HTTPS обов'язкове для WebApp

## Розробка

### Структура проєкту

```
bot/                    # Telegram бот
├── bot.py             # Основний код бота
└── requirements.txt   # Python залежності

webapp/                # WebApp
├── index.html         # Основна сторінка
└── config.js         # Конфігурація

.github/workflows/     # GitHub Actions
└── deploy.yml        # Деплой на GitHub Pages

docs/                  # Документація
└── GITHUB_PAGES_SETUP.md
```

### Локальна розробка

1. **WebApp тестування:**
   ```bash
   python start_webapp_server.py
   # Відкрийте http://localhost:8000
   ```

2. **Тестування з ngrok:**
   ```bash
   ./start_webapp_ngrok.sh
   # Або start_webapp_ngrok.bat на Windows
   ```

### Логування та моніторинг

Бот логує:
- Отримані заявки
- Помилки валідації
- Проблеми з відправкою в адмін чати
- Помилки верифікації WebApp

## Ліцензія

MIT License

## Підтримка

Для питань та підтримки створіть issue в GitHub репозиторії.