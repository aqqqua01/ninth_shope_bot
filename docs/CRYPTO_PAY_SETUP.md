# Налаштування Crypto Pay API

## 🚀 Що дає інтеграція Crypto Pay:

- **Автоматичні криптоплатежі** - USDT, TON, BTC, ETH, LTC та інші
- **Конвертація валют** - показ курсів рублів в криптовалютах
- **Миттєве підтвердження** платежів через webhook
- **Автоматизація** - без ручної перевірки платежів

## 📋 Інструкція по налаштуванню:

### 1. Отримання API токена

1. **Відкрийте @CryptoBot** в Telegram
2. **Натисніть "Crypto Pay"**
3. **Натисніть "Create App"**
4. **Введіть назву додатка** (наприклад: "Steam Top-Up Bot")
5. **Скопіюйте API Token**

### 2. Налаштування .env файла

Додайте в `.env` файл:

```env
# Crypto Pay API Configuration
CRYPTO_PAY_API_TOKEN=12345:AAxxxxxxxxxxxxxxxxxxxxx
CRYPTO_PAY_TESTNET=true

# Currency API Server
CURRENCY_API_PORT=8001
```

**Важливо:**
- Для тестування використовуйте `CRYPTO_PAY_TESTNET=true`
- Для продакшену змініть на `CRYPTO_PAY_TESTNET=false`

### 3. Тестування (Testnet)

Для тестування:
- Бот: **@CryptoTestnetBot**
- Отримати тестові монети: **@CryptoPayTestBot**

### 4. Запуск системи

#### A. Запуск Currency API сервера:
```bash
# Windows
start_currency_api.bat

# Linux/macOS
python start_currency_api.py
```

#### B. Запуск Telegram бота:
```bash
cd bot
python bot.py
```

## 🔄 Як це працює:

### 1. **Користувач вводить суму в рублях**
   - WebApp показує конвертацію в USDT, TON, BTC, ETH
   - Курси отримуються в реальному часі

### 2. **При підтвердженні заявки:**
   - Бот створює Crypto Pay інвойс
   - Користувач отримує посилання для оплати
   - Може платити будь-якою підтримуваною криптовалютою

### 3. **Після оплати:**
   - Webhook автоматично повідомляє про платіж
   - Бот автоматично позначає заявку як виконану
   - Користувач отримує підтвердження

## 💎 Підтримувані криптовалюти:

- **USDT** (Tether) - найпопулярніша стейблкоїн
- **TON** (Toncoin) - валюта Telegram
- **BTC** (Bitcoin)
- **ETH** (Ethereum)
- **LTC** (Litecoin)
- **BNB** (Binance Coin)
- **TRX** (TRON)
- **USDC** (USD Coin)

## 🔧 Налаштування webhook (для продакшену)

1. **В @CryptoBot:**
   - Йдіть до "My Apps" → ваш додаток
   - Натисніть "Webhooks..."
   - Увімкніть "Enable Webhooks"
   - Введіть URL: `https://your-domain.com/webhook/crypto-pay`

2. **В коді бота:**
   - Додайте обробник webhook
   - Перевіряйте підпис для безпеки

## 📊 API Endpoints

Currency API сервер надає:

- `GET /api/rates` - отримання курсів валют
- `POST /api/convert` - конвертація рублів в криптовалюти
- `GET /health` - перевірка стану API

## ⚠️ Важливі примітки:

1. **Безпека**: Ніколи не показуйте API токен публічно
2. **Тестування**: Спочатку протестуйте в testnet
3. **Webhook**: В продакшені обов'язково налаштуйте webhook
4. **CORS**: Currency API налаштований для локальної розробки

## 🆘 Вирішення проблем:

### WebApp не показує курси:
- Перевірте, що Currency API запущений на порту 8001
- Переконайтеся, що CRYPTO_PAY_API_TOKEN правильний

### Помилка "Crypto Pay API не инициализирован":
- Перевірте .env файл
- Переконайтеся, що токен валідний

### Не працює конвертація:
- Перевірте логи Currency API сервера
- Переконайтеся в доступності Crypto Pay API

---

**Результат:** Ваш Steam бот буде приймати криптоплатежі автоматично! 🚀
