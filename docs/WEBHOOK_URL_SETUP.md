# 🔗 WEBHOOK_URL Setup Guide

## Що таке WEBHOOK_URL?

**WEBHOOK_URL** - це публічна адреса, на яку Crypto Pay надсилає сповіщення про платежі.

```
Crypto Pay API → WEBHOOK_URL → Ваш бот → Повідомлення адміну
```

---

## 🚀 Варіанти отримання WEBHOOK_URL

### 1️⃣ ngrok (Найпростіший для розробки)

#### Крок 1: Реєстрація
1. Йдіть на https://ngrok.com/
2. Sign Up безкоштовно
3. Завантажте ngrok або використовуйте наш `ngrok.exe`

#### Крок 2: Запуск
```powershell
# Запустіть бота
cd bot
python bot.py

# В новому терміналі
.\ngrok.exe http 8003
```

#### Крок 3: Отримаєте результат:
```
Forwarding    https://abc123.ngrok.io -> http://localhost:8003
```

#### Крок 4: Налаштуйте .env:
```env
WEBHOOK_URL=https://abc123.ngrok.io
WEBHOOK_PORT=8003
```

**✅ Плюси:** швидко, безкоштовно  
**❌ Мінуси:** URL змінюється щоразу

---

### 2️⃣ Cloudflare Tunnel (Безкоштовно + Стабільно)

#### Встановлення:
```powershell
# Завантажте cloudflared з:
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Запустіть тунель
cloudflared tunnel --url http://localhost:8003
```

#### Результат:
```
https://random-words.trycloudflare.com
```

**✅ Плюси:** безкоштовно, швидко  
**❌ Мінуси:** URL довгий, змінюється

---

### 3️⃣ VPS/Сервер (Продакшен)

#### Приклади провайдерів:
- **DigitalOcean:** $5/місяць
- **Vultr:** $2.5/місяць  
- **Hetzner:** €3/місяць
- **Amazon Lightsail:** $3.5/місяць

#### Налаштування:
```bash
# На сервері Ubuntu
git clone https://github.com/aqqqua01/ninth_shope_bot.git
cd ninth_shope_bot
pip install -r requirements.txt

# Налаштуйте .env
nano .env

# Додайте:
WEBHOOK_URL=https://yourdomain.com
# або
WEBHOOK_URL=https://123.456.789.0:8003
```

**✅ Плюси:** стабільний URL, швидкість  
**❌ Мінуси:** платний

---

### 4️⃣ Render.com (Безкоштовно)

#### Крок 1: Push код на GitHub ✅ (вже зроблено)

#### Крок 2: Підключіть до Render
1. Йдіть на https://render.com/
2. Sign Up через GitHub
3. New → Web Service
4. Connect Repository: `ninth_shope_bot`

#### Крок 3: Налаштування:
```
Name: ninth-shope-bot
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python bot/bot.py
```

#### Крок 4: Environment Variables:
```
BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_chat_id
WEBHOOK_URL=https://ninth-shope-bot.onrender.com
WEBAPP_URL=https://aqqqua01.github.io/ninth_shope_bot/
```

**✅ Плюси:** безкоштовно, автодеплой з GitHub  
**❌ Мінуси:** засинає через 15 хв бездіяльності

---

## 🔧 Тестування WEBHOOK_URL

### Перевірте доступність:
```bash
curl https://your-webhook-url.com/webhook/health
# Повинно повернути: {"status": "ok"}
```

### Тест через Postman/браузер:
```
GET https://your-webhook-url.com/webhook/health
```

---

## ⚡ Швидкий старт для тестування

### Використовуйте готовий скрипт:
```powershell
.\start_webhook_with_ngrok.bat
```

### Або вручну:
```powershell
# Термінал 1: Бот
cd bot && python bot.py

# Термінал 2: ngrok  
.\ngrok.exe http 8003

# Скопіюйте HTTPS URL в .env як WEBHOOK_URL
```

---

## 🎯 Рекомендації

### Для розробки:
✅ **ngrok** - найшвидший старт

### Для тестування:
✅ **Cloudflare Tunnel** - стабільніший за ngrok

### Для продакшену:
✅ **VPS сервер** - максимальна надійність  
✅ **Render.com** - безкоштовний варіант

---

## 🚨 Важливо!

1. **HTTPS обов'язково** - Crypto Pay працює тільки з HTTPS
2. **Порт 8003** - за замовчуванням для webhook сервера  
3. **Доступність 24/7** - для автоматичних платежів

---

## 📋 Приклад готового .env:

```env
# Основні налаштування
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_CHAT_ID=123456789
WEBAPP_URL=https://aqqqua01.github.io/ninth_shope_bot/

# Для webhook (оберіть один варіант)
WEBHOOK_URL=https://abc123.ngrok.io          # ngrok
# WEBHOOK_URL=https://yourdomain.com         # власний домен  
# WEBHOOK_URL=https://yourapp.onrender.com   # Render.com

WEBHOOK_PORT=8003

# Опціонально для криптоплатежів
CRYPTO_PAY_API_TOKEN=your_crypto_pay_token
CRYPTO_PAY_TESTNET=true
```

✅ **Готово для автоматичних криптоплатежів!**

