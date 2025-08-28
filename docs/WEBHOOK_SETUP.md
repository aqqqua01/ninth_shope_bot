# 🔗 Webhook Configuration Guide

## Overview

Webhooks allow your bot to receive **automatic notifications** when cryptocurrency payments are completed through Crypto Pay API. This enables real-time processing without manual confirmation.

## ⚡ Features

- **Automatic payment confirmation**
- **Real-time notifications to admin**
- **Secure signature verification**
- **Support for all Crypto Pay assets**

## 🛠️ Setup Steps

### 1. Get Public URL

You need a **publicly accessible URL** for webhooks:

#### Option A: ngrok (Development)
```bash
# Install ngrok from https://ngrok.com/
ngrok http 8003

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

#### Option B: Production Server
- Deploy to VPS with public IP
- Configure domain with SSL certificate
- Use ports 80/443

### 2. Configure Environment

Add to your `.env` file:
```env
# Webhook settings
WEBHOOK_PORT=8003
WEBHOOK_URL=https://your-domain.com

# Required for webhooks
CRYPTO_PAY_API_TOKEN=your_token_from_cryptobot
```

### 3. Update Crypto Pay Webhook

The bot will automatically set the webhook URL when it starts:
```
Webhook URL: https://your-domain.com/webhook/crypto-pay
```

### 4. Test Webhook

1. Start the bot:
   ```bash
   cd bot && python bot.py
   ```

2. Check logs for:
   ```
   Webhook сервер запущен на порту 8003
   Webhook установлен: https://your-domain.com/webhook/crypto-pay
   ```

3. Make a test payment through Crypto Pay

## 📋 Webhook Events

### invoice_paid Event

When a payment is completed, the webhook receives:

```json
{
  "update_type": "invoice_paid",
  "payload": {
    "invoice_id": 123456,
    "status": "paid", 
    "amount": "115.00",
    "asset": "RUB",
    "paid_amount": "1.44",
    "paid_asset": "USDT",
    "description": "Steam пополнение: user123"
  }
}
```

### Bot Actions

1. **Verifies signature** (security)
2. **Logs payment details**
3. **Sends notification to admin**:
   ```
   💰 КРИПТОПЛАТЕЖ ПОЛУЧЕН!
   
   📋 Инвойс: 123456
   💳 Сумма: 1.44 USDT  
   📝 Описание: Steam пополнение: user123
   ⏰ Время: 28.08.2025 15:30
   ```

## 🔒 Security

- **HMAC-SHA256 signature verification**
- **Webhook body validation**
- **HTTPS only in production**
- **Rate limiting protection**

## 🚨 Troubleshooting

### Webhook Not Receiving Events

1. **Check URL accessibility**:
   ```bash
   curl https://your-domain.com/webhook/health
   # Should return: {"status": "ok"}
   ```

2. **Verify webhook is set**:
   - Check bot logs for "Webhook установлен"
   - Manually check in Crypto Pay dashboard

3. **Test locally with ngrok**:
   ```bash
   # Terminal 1
   cd bot && python bot.py
   
   # Terminal 2  
   ngrok http 8003
   
   # Update WEBHOOK_URL and restart bot
   ```

### Signature Verification Fails

- **Correct API token**: Ensure `CRYPTO_PAY_API_TOKEN` matches Crypto Pay app
- **Check testnet setting**: Set `CRYPTO_PAY_TESTNET=true` for testing
- **Log webhook body**: Enable debug logging to see raw payloads

### Port Issues

```bash
# Check if port is in use
netstat -an | findstr :8003

# Kill process if needed
taskkill /F /PID <process_id>
```

## 📊 Monitoring

Check webhook health:
```bash
curl https://your-domain.com/webhook/health
```

Monitor logs for:
- `Получен платеж: invoice_123, статус: paid`
- `КРИПТОПЛАТЕЖ ПОЛУЧЕН! Инвойс: 123`
- `Webhook signature verified successfully`

## 🎯 Production Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - WEBHOOK_URL=https://your-domain.com
      - WEBHOOK_PORT=8003
    ports:
      - "8003:8003"
    restart: unless-stopped
```

### Systemd Service
```ini
[Unit]
Description=Steam Bot Webhook
After=network.target

[Service]
Type=simple
User=steambot
WorkingDirectory=/opt/steambot
ExecStart=/usr/bin/python3 bot.py
Restart=always
Environment=WEBHOOK_URL=https://your-domain.com

[Install]
WantedBy=multi-user.target
```

## 🔧 Advanced Configuration

### Custom Webhook Handlers

Add custom logic in `handle_payment_success()`:

```python
async def handle_payment_success(payload):
    # Extract user data from invoice description
    description = payload.get('description', '')
    if 'user:' in description:
        user_id = description.split('user:')[1].split()[0]
        
        # Send custom message to user
        await send_completion_message(user_id, payload)
```

### Multiple Webhook Endpoints

```python
app.router.add_post('/webhook/crypto-pay', crypto_pay_webhook)
app.router.add_post('/webhook/custom', custom_webhook)
app.router.add_get('/webhook/status', webhook_status)
```

---

✅ **Webhook система готова для автоматической обработки платежей!**
