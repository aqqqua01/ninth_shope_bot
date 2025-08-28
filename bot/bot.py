#!/usr/bin/env python3
"""
Steam Top-Up Telegram Bot
Обрабатывает пополнения Steam через Telegram WebApp
"""

import os
import json
import logging
import hashlib
import hmac
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import parse_qsl

from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from aiohttp import web
import asyncio
from dotenv import load_dotenv
from crypto_pay import init_crypto_pay, crypto_pay_api, currency_converter

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
FORWARD_CHAT_ID = os.getenv('FORWARD_CHAT_ID')
PAYMENT_DETAILS = os.getenv('PAYMENT_DETAILS', 'Реквизиты не настроены')
CURRENCY = os.getenv('CURRENCY', 'РУБ')
WEBAPP_URL = os.getenv('WEBAPP_URL')
CRYPTO_PAY_API_TOKEN = os.getenv('CRYPTO_PAY_API_TOKEN')
CRYPTO_PAY_TESTNET = os.getenv('CRYPTO_PAY_TESTNET', 'true').lower() == 'true'
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8003'))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Публичный URL для webhook'ов

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен!")
    exit(1)

if not ADMIN_CHAT_ID:
    logger.error("ADMIN_CHAT_ID не установлен!")
    exit(1)

if not WEBAPP_URL:
    logger.warning("WEBAPP_URL не установлен - WebApp кнопка будет скрыта")

# Инициализация Crypto Pay API
# Глобальные переменные
telegram_app = None

if CRYPTO_PAY_API_TOKEN:
    try:
        init_crypto_pay(CRYPTO_PAY_API_TOKEN, CRYPTO_PAY_TESTNET)
        logger.info("Crypto Pay API инициализирован успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации Crypto Pay API: {e}")
else:
    logger.warning("CRYPTO_PAY_API_TOKEN не установлен - криптоплатежи отключены")


def verify_webapp_data(init_data: str, bot_token: str) -> bool:
    """
    Проверяет подлинность данных WebApp согласно документации Telegram
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        data_check_string_parts = []
        
        for key, value in sorted(parsed_data.items()):
            if key != 'hash':
                data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == parsed_data.get('hash')
    except Exception as e:
        logger.error(f"Ошибка при проверке WebApp данных: {e}")
        return False


def parse_amount(amount_str: str) -> Decimal:
    """
    Парсит и валидирует сумму пополнения
    """
    try:
        # Заменяем запятую на точку
        amount_str = amount_str.replace(',', '.')
        amount = Decimal(amount_str)
        
        if amount < 100:
            raise ValueError("Минимальная сумма: 100 рублей")
        
        # Округляем до 2 знаков после запятой
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Некорректная сумма: {e}")


def calculate_total(base_amount: Decimal) -> Decimal:
    """
    Вычисляет итоговую сумму к оплате с комиссией +15%
    """
    total = base_amount * Decimal('1.15')
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"Я помогу тебе пополнить Steam кошелек.\n"
        f"Нажми кнопку ниже, чтобы оформить пополнение:"
    )
    
    # Создаем клавиатуру с WebApp кнопкой если URL настроен
    if WEBAPP_URL:
        keyboard = [
            [KeyboardButton(
                "🎮 Оформить пополнение", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    else:
        welcome_message += "\n⚠️ WebApp не настроен, обратитесь к администратору."
        reply_markup = None
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "🤖 <b>Команды бота:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n"
        "/cancel - Отменить текущую операцию\n"
        "/admin - Информация для администратора\n\n"
        "💡 <b>Как пополнить Steam:</b>\n"
        "1. Нажми кнопку 'Оформить пополнение'\n"
        "2. Заполни форму в открывшемся окне\n"
        "3. Проверь данные и подтверди заказ\n"
        "4. Переведи указанную сумму по реквизитам\n"
        "5. Ожидай пополнения (обычно до 30 минут)\n\n"
        f"💰 Валюта: {CURRENCY}\n"
        f"💵 Минимальная сумма: 100 {CURRENCY}"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /cancel"""
    await update.message.reply_text(
        "❌ Текущая операция отменена.\n"
        "Если хочешь начать заново, воспользуйся командой /start"
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /admin"""
    user = update.effective_user
    chat = update.effective_chat
    
    admin_info = (
        f"👤 <b>Информация о пользователе:</b>\n"
        f"User ID: <code>{user.id}</code>\n"
        f"Username: @{user.username or 'не указан'}\n"
        f"Имя: {user.full_name}\n\n"
        f"💬 <b>Информация о чате:</b>\n"
        f"Chat ID: <code>{chat.id}</code>\n"
        f"Тип чата: {chat.type}"
    )
    
    await update.message.reply_text(admin_info, parse_mode='HTML')


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик данных от WebApp"""
    try:
        # Получаем информацию о пользователе сразу в начале
        user = update.effective_user
        
        # Логируем сырые данные для отладки
        raw_data = update.message.web_app_data.data
        logger.info(f"Получены сырые WebApp данные от пользователя {user.id}: {raw_data}")
        
        # ВРЕМЕННО: пропускаем верификацию для тестирования
        # TODO: включить верификацию в продакшене
        # if not verify_webapp_data(update.message.web_app_data.data, BOT_TOKEN):
        #     logger.warning(f"Получены недействительные WebApp данные от пользователя {update.effective_user.id}")
        #     await update.message.reply_text(
        #         "❌ Ошибка проверки данных. Попробуйте еще раз."
        #     )
        #     return
        
        # Парсим JSON данные
        data = json.loads(update.message.web_app_data.data)
        logger.info(f"Получены WebApp данные от {user.full_name}: {data}")
        
        # Валидируем данные
        steam_login = data.get('steam_login', '').strip()
        if not steam_login:
            await update.message.reply_text(
                "❌ Логин Steam не может быть пустым. Попробуйте еще раз."
            )
            return
        
        # Валидируем и пересчитываем сумму на сервере
        try:
            base_amount = parse_amount(str(data.get('base_amount', 0)))
            to_pay = calculate_total(base_amount)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return
        
        # Формируем сообщение для пользователя с кнопками выбора оплаты
        user_message = (
            f"✅ <b>Заявка на пополнение принята!</b>\n\n"
            f"🎮 Логин Steam: <code>{steam_login}</code>\n"
            f"💰 Сумма пополнения: {base_amount} {CURRENCY}\n"
            f"💳 К оплате: <b>{to_pay} {CURRENCY}</b>\n\n"
            f"💎 <b>Выберите способ оплаты:</b>\n"
            f"• Криптовалютой (USDT, TON, BTC, ETH, LTC, BNB)\n"
            f"• Традиционным переводом\n\n"
            f"⏳ После оплаты пополнение поступит в течение 30 минут.\n"
            f"❓ Вопросы? Обращайтесь к администратору."
        )
        
        # Создаем кнопки для выбора способа оплаты
        user_keyboard = [
            [
                InlineKeyboardButton("💰 Оплатить криптовалютой", callback_data=f"crypto_pay_{user.id}_{steam_login}_{base_amount}_{to_pay}")
            ],
            [
                InlineKeyboardButton("💳 Традиционная оплата", callback_data=f"manual_pay_{user.id}")
            ]
        ]
        user_reply_markup = InlineKeyboardMarkup(user_keyboard)
        
        await update.message.reply_text(
            user_message, 
            parse_mode='HTML',
            reply_markup=user_reply_markup
        )
        
        # Формируем сообщение для админа
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Создаем кнопку "Выполнено"
        keyboard = [
            [InlineKeyboardButton(
                "✅ Выполнено", 
                callback_data=f"completed_{user.id}_{update.effective_chat.id}_{base_amount}_{steam_login}"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_message = (
            f"🔔 <b>НОВАЯ ЗАЯВКА НА ПОПОЛНЕНИЕ</b>\n\n"
            f"⏰ Время: {timestamp}\n"
            f"👤 Пользователь: {user.full_name} (@{user.username or 'без username'})\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"💬 Chat ID: <code>{update.effective_chat.id}</code>\n\n"
            f"📋 <b>Данные заявки:</b>\n"
            f"🎮 Логин Steam: <code>{steam_login}</code>\n"
            f"💰 Сумма пополнения: {base_amount} {CURRENCY}\n"
            f"💳 К оплате: <b>{to_pay} {CURRENCY}</b>\n\n"
            f"📊 <b>Техническая информация:</b>\n"
            f"<code>{json.dumps(data, ensure_ascii=False, indent=2)}</code>"
        )
        
        # Отправляем в админ чат
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=admin_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Ошибка отправки в админ чат: {e}")
        
        # Отправляем в дополнительный чат если настроен
        if FORWARD_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=FORWARD_CHAT_ID,
                    text=admin_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Ошибка отправки в дополнительный чат: {e}")
        
        logger.info(f"Обработана заявка от пользователя {user.id}: {steam_login}, {base_amount} {CURRENCY}")
        
    except json.JSONDecodeError:
        logger.error("Ошибка парсинга JSON данных от WebApp")
        await update.message.reply_text(
            "❌ Ошибка обработки данных. Попробуйте еще раз."
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке WebApp данных: {e}")
        await update.message.reply_text(
            "❌ Упс, что-то пошло не так. Попробуйте еще раз или обратитесь к администратору."
        )


async def handle_completion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Выполнено'"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим данные из callback_data
        _, user_id, chat_id, amount, steam_login = query.data.split('_', 4)
        
        # Отправляем уведомление пользователю
        completion_message = (
            f"✅ <b>Пополнение выполнено!</b>\n\n"
            f"🎮 Логин Steam: <code>{steam_login}</code>\n"
            f"💰 Сумма: {amount} {CURRENCY}\n\n"
            f"💡 Пополнение должно поступить на ваш аккаунт в течение нескольких минут.\n"
            f"❓ Если возникли вопросы, обращайтесь к администратору."
        )
        
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=completion_message,
            parse_mode='HTML'
        )
        
        # Обновляем сообщение админа
        await query.edit_message_text(
            text=f"{query.message.text}\n\n✅ <b>СТАТУС: ВЫПОЛНЕНО</b>",
            parse_mode='HTML'
        )
        
        logger.info(f"Отправлено уведомление о выполнении пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке завершения: {e}")
        await query.edit_message_text(
            text=f"{query.message.text}\n\n❌ <b>ОШИБКА при отправке уведомления</b>",
            parse_mode='HTML'
        )


async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных сообщений"""
    await update.message.reply_text(
        "🤔 Я не понимаю это сообщение.\n"
        "Воспользуйтесь командой /help для получения справки."
    )


# ======================== WEBHOOK HANDLERS ========================

async def crypto_pay_webhook(request):
    """Обрабатывает webhook от Crypto Pay"""
    try:
        # Получаем данные
        body = await request.text()
        headers = request.headers
        
        # Проверяем подпись
        signature = headers.get('crypto-pay-api-signature')
        if not signature:
            logger.warning("Webhook без подписи")
            return web.json_response({'error': 'No signature'}, status=400)
            
        # Верифицируем подпись
        if crypto_pay_api and not crypto_pay_api.verify_webhook_signature(body, signature):
            logger.warning("Неверная подпись webhook")
            return web.json_response({'error': 'Invalid signature'}, status=400)
        
        # Парсим данные
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            logger.error("Ошибка парсинга JSON webhook")
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        
        update_type = data.get('update_type')
        payload = data.get('payload', {})
        
        if update_type == 'invoice_paid':
            await handle_payment_success(payload)
        else:
            logger.info(f"Неизвестный тип webhook: {update_type}")
        
        return web.json_response({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return web.json_response({'error': 'Internal error'}, status=500)

async def handle_payment_success(payload):
    """Обрабатывает успешный платеж"""
    try:
        invoice_id = payload.get('invoice_id')
        status = payload.get('status')
        amount = payload.get('amount')
        asset = payload.get('asset')
        paid_amount = payload.get('paid_amount')
        
        # Можно извлечь user_id из описания инвойса
        description = payload.get('description', '')
        
        logger.info(f"Получен платеж: {invoice_id}, статус: {status}, сумма: {paid_amount} {asset}")
        
        if ADMIN_CHAT_ID and status == 'paid':
            message = (
                "💰 <b>КРИПТОПЛАТЕЖ ПОЛУЧЕН!</b>\n\n"
                f"📋 Инвойс: <code>{invoice_id}</code>\n"
                f"💳 Сумма: {paid_amount} {asset}\n"
                f"📝 Описание: {description}\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            
            # Получаем application из глобальной переменной
            bot_app = globals().get('telegram_app')
            if bot_app:
                await bot_app.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=message,
                    parse_mode='HTML'
                )
        
    except Exception as e:
        logger.error(f"Ошибка обработки успешного платежа: {e}")

def create_webhook_app():
    """Создает webhook приложение"""
    app = web.Application()
    
    # Добавляем маршруты
    app.router.add_post('/webhook/crypto-pay', crypto_pay_webhook)
    app.router.add_get('/webhook/health', lambda r: web.json_response({'status': 'ok'}))
    
    return app

async def run_webhook_server():
    """Запускает webhook сервер"""
    if not WEBHOOK_URL:
        logger.info("WEBHOOK_URL не установлен - webhook сервер не запускается")
        return
        
    webhook_app = create_webhook_app()
    
    try:
        runner = web.AppRunner(webhook_app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', WEBHOOK_PORT)
        await site.start()
        
        logger.info(f"Webhook сервер запущен на порту {WEBHOOK_PORT}")
        logger.info(f"Webhook URL: {WEBHOOK_URL}/webhook/crypto-pay")
        
        # Настраиваем webhook в Crypto Pay
        if crypto_pay_api:
            webhook_url = f"{WEBHOOK_URL}/webhook/crypto-pay"
            try:
                await crypto_pay_api.set_webhook(webhook_url)
                logger.info(f"Webhook установлен: {webhook_url}")
            except Exception as e:
                logger.error(f"Ошибка установки webhook: {e}")
        
        # Держим сервер живым
        while True:
            await asyncio.sleep(3600)  # Спим 1 час
            
    except Exception as e:
        logger.error(f"Ошибка webhook сервера: {e}")

async def handle_crypto_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор криптооплаты"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим данные из callback
        parts = query.data.split('_')
        if len(parts) < 6:
            await query.edit_message_text("❌ Ошибка в данных заказа.")
            return
            
        user_id = int(parts[2])
        steam_login = parts[3]
        base_amount = float(parts[4])
        to_pay = float(parts[5])
        
        if not crypto_pay_api:
            await query.edit_message_text(
                "❌ Криптоплатежи временно недоступны.\n"
                "Воспользуйтесь традиционной оплатой.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Традиционная оплата", callback_data=f"manual_pay_{user_id}")
                ]])
            )
            return
        
        # Создаем инвойс в Crypto Pay
        description = f"Steam пополнение: {steam_login}"
        
        try:
            invoice_data = await crypto_pay_api.create_invoice(
                currency_type="fiat",
                fiat="RUB",
                amount=str(to_pay),
                accepted_assets="USDT,TON,BTC,ETH,LTC,BNB",
                description=description,
                payload=f"user:{user_id}"
            )
            
            if invoice_data and 'result' in invoice_data:
                invoice = invoice_data['result']
                invoice_id = invoice['invoice_id']
                pay_url = invoice['pay_url']
                
                crypto_message = (
                    f"💰 <b>Инвойс для криптооплаты создан!</b>\n\n"
                    f"🎮 Логин Steam: <code>{steam_login}</code>\n"
                    f"💰 Сумма: <b>{to_pay} {CURRENCY}</b>\n\n"
                    f"💎 <b>Доступные криптовалюты:</b>\n"
                    f"• USDT, TON, BTC, ETH, LTC, BNB\n\n"
                    f"📋 ID инвойса: <code>{invoice_id}</code>\n\n"
                    f"👆 Нажмите кнопку ниже для оплаты:"
                )
                
                keyboard = [
                    [InlineKeyboardButton("💰 Перейти к оплате", url=pay_url)],
                    [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_payment_{user_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    crypto_message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                
                logger.info(f"Создан криптоинвойс {invoice_id} для пользователя {user_id}")
                
            else:
                raise Exception("Неверный ответ API")
                
        except Exception as e:
            logger.error(f"Ошибка создания инвойса: {e}")
            await query.edit_message_text(
                "❌ Ошибка создания криптоинвойса.\n"
                "Попробуйте позже или выберите традиционную оплату.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💳 Традиционная оплата", callback_data=f"manual_pay_{user_id}")
                ]])
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки криптооплаты: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")

async def handle_manual_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор традиционной оплаты"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Показываем реквизиты для ручной оплаты
        manual_message = (
            f"💳 <b>Традиционная оплата</b>\n\n"
            f"📝 <b>Реквизиты для оплаты:</b>\n"
            f"<code>{PAYMENT_DETAILS}</code>\n\n"
            f"⏳ После оплаты пополнение поступит в течение 30 минут.\n"
            f"❓ Вопросы? Обращайтесь к администратору.\n\n"
            f"💰 Или выберите криптооплату:"
        )
        
        user_id = query.data.split('_')[2]
        keyboard = [
            [InlineKeyboardButton("🔙 Назад к способам оплаты", callback_data=f"back_to_payment_{user_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            manual_message,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки ручной оплаты: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте еще раз.")

async def handle_cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает отмену платежа"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ <b>Платеж отменен</b>\n\n"
        "Вы можете создать новую заявку, отправив /start",
        parse_mode='HTML'
    )

async def handle_back_to_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возвращает к выбору способа оплаты"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.data.split('_')[3]
    
    # Возвращаем исходное сообщение с выбором способа оплаты
    payment_message = (
        f"💎 <b>Выберите способ оплаты:</b>\n\n"
        f"• Криптовалютой (USDT, TON, BTC, ETH, LTC, BNB)\n"
        f"• Традиционным переводом\n\n"
        f"⏳ После оплаты пополнение поступит в течение 30 минут.\n"
        f"❓ Вопросы? Обращайтесь к администратору."
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Оплатить криптовалютой", callback_data=f"crypto_pay_reselect_{user_id}")],
        [InlineKeyboardButton("💳 Традиционная оплата", callback_data=f"manual_pay_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        payment_message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def main_async():
    """Асинхронная главная функция"""
    global telegram_app
    
    logger.info("Запуск Steam Top-Up Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    telegram_app = application  # Сохраняем для использования в webhook'ах
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Обработчик WebApp данных
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Обработчик кнопки "Выполнено"
    application.add_handler(CallbackQueryHandler(handle_completion_callback, pattern="^completed_"))
    
    # Обработчики способов оплаты
    application.add_handler(CallbackQueryHandler(handle_crypto_payment, pattern="^crypto_pay_"))
    application.add_handler(CallbackQueryHandler(handle_manual_payment, pattern="^manual_pay_"))
    application.add_handler(CallbackQueryHandler(handle_cancel_payment, pattern="^cancel_payment_"))
    application.add_handler(CallbackQueryHandler(handle_back_to_payment, pattern="^back_to_payment_"))
    
    # Обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запускаем webhook сервер параллельно, если настроен
    tasks = []
    
    if WEBHOOK_URL:
        logger.info("Запуск webhook сервера...")
        tasks.append(asyncio.create_task(run_webhook_server()))
    
    # Запускаем бота
    async with application:
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        # Ждем завершения всех задач
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Получен сигнал остановки")
        
        await application.updater.stop()
        await application.stop()

def main() -> None:
    """Основная функция запуска бота"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
        raise


if __name__ == '__main__':
    main()
