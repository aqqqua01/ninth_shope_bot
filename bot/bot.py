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
from dotenv import load_dotenv

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

# Проверка обязательных переменных
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен!")
    exit(1)

if not ADMIN_CHAT_ID:
    logger.error("ADMIN_CHAT_ID не установлен!")
    exit(1)

if not WEBAPP_URL:
    logger.warning("WEBAPP_URL не установлен - WebApp кнопка будет скрыта")


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
        # Логируем сырые данные для отладки
        raw_data = update.message.web_app_data.data
        logger.info(f"Получены сырые WebApp данные: {raw_data}")
        
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
        logger.info(f"Получены WebApp данные: {data}")
        
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
        
        # Формируем сообщение для пользователя
        user_message = (
            f"✅ <b>Заявка на пополнение принята!</b>\n\n"
            f"🎮 Логин Steam: <code>{steam_login}</code>\n"
            f"💰 Сумма пополнения: {base_amount} {CURRENCY}\n"
            f"💳 К оплате (+15%): <b>{to_pay} {CURRENCY}</b>\n\n"
            f"💳 <b>Реквизиты для оплаты:</b>\n"
            f"<code>{PAYMENT_DETAILS}</code>\n\n"
            f"⏳ После оплаты пополнение поступит в течение 30 минут.\n"
            f"❓ Вопросы? Обращайтесь к администратору."
        )
        
        await update.message.reply_text(user_message, parse_mode='HTML')
        
        # Формируем сообщение для админа
        user = update.effective_user
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


def main() -> None:
    """Основная функция запуска бота"""
    logger.info("Запуск Steam Top-Up Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Обработчик WebApp данных
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Обработчик кнопки "Выполнено"
    application.add_handler(CallbackQueryHandler(handle_completion_callback, pattern="^completed_"))
    
    # Обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
