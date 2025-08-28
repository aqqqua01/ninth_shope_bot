#!/usr/bin/env python3
"""
Simple Crypto Top-Up Telegram Bot
Простой бот для пополнения через криптовалюту
"""

import os
import json
import logging
import hashlib
import hmac
import asyncio
import base64
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
WEBAPP_URL = os.getenv('WEBAPP_URL')

# Курс USDT к рублю (можно обновлять вручную)
USDT_RATE = float(os.getenv('USDT_RATE', '95.0'))  # 1 USDT = 95 RUB по умолчанию

# Комиссия в процентах
COMMISSION_PERCENT = float(os.getenv('COMMISSION_PERCENT', '15.0'))  # 15% по умолчанию

# Хранилище для курса (можно изменять через команды)
current_usdt_rate = USDT_RATE

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
    Парсит и валидирует сумму для пополнения
    """
    try:
        # Заменяем запятую на точку
        amount_str = amount_str.replace(',', '.')
        amount = Decimal(amount_str)
        
        if amount < 100:
            raise ValueError("Минимальная сумма: 100 РУБ")
        
        # Округляем до 2 знаков после запятой
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Некорректная сумма: {e}")


def calculate_total_with_commission(base_amount: Decimal) -> Decimal:
    """
    Вычисляет итоговую сумму к оплате с комиссией
    """
    commission_multiplier = Decimal('1') + (Decimal(str(COMMISSION_PERCENT)) / Decimal('100'))
    total = base_amount * commission_multiplier
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_usdt_amount(rub_amount: Decimal) -> Decimal:
    """
    Конвертирует рубли в USDT по текущему курсу
    """
    global current_usdt_rate
    usdt_amount = rub_amount / Decimal(str(current_usdt_rate))
    return usdt_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        f"💰 Быстрое пополнение через криптовалюту!\n\n"
        f"📝 Просто укажи сумму - мы конвертируем в USDT\n"
        f"🔐 Способ оплаты: Криптовалюта\n"
        f"⚡ После заявки с тобой свяжется оператор\n\n"
        f"👇 Нажми кнопку для оформления:"
    )
    
    # Создаем клавиатуру с WebApp кнопкой если URL настроен
    if WEBAPP_URL:
        keyboard = [
            [KeyboardButton(
                "💰 Оформить пополнение", 
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
        "/admin - Информация для администратора\n"
        "/setrate - Изменить курс USDT (только админ)\n\n"
        f"💡 <b>Как оформить заказ:</b>\n"
        f"1. Нажми кнопку 'Оформить пополнение'\n"
        f"2. Укажи логин и сумму в рублях\n"
        f"3. Система покажет сумму к оплате с комиссией {COMMISSION_PERCENT}%\n"
        f"4. Подтверди заказ\n"
        f"5. Ожидай принятия заказа оператором\n"
        f"6. После принятия - получишь реквизиты для оплаты\n"
        f"7. После оплаты заказ будет завершен\n\n"
        f"💰 <b>Способ оплаты:</b> Криптовалюта (USDT)\n"
        f"💱 <b>Текущий курс:</b> 1 USDT = {current_usdt_rate} РУБ\n"
        f"📈 <b>Комиссия:</b> {COMMISSION_PERCENT}%\n"
        f"💵 <b>Минимальная сумма:</b> 100 РУБ"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /cancel"""
    await update.message.reply_text(
        "❌ Операция отменена.\n"
        "Для создания новой заявки используй команду /start"
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


async def set_rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /setrate для изменения курса USDT"""
    global current_usdt_rate
    
    # Проверяем что это администратор
    if str(update.effective_user.id) != ADMIN_CHAT_ID.lstrip('-'):
        await update.message.reply_text("❌ Эта команда доступна только администратору.")
        return
    
    if not context.args:
        await update.message.reply_text(
            f"💱 <b>Текущий курс USDT:</b> 1 USDT = {current_usdt_rate} РУБ\n"
            f"📈 <b>Комиссия:</b> {COMMISSION_PERCENT}%\n\n"
            f"Для изменения курса используйте:\n"
            f"<code>/setrate 95.5</code>",
            parse_mode='HTML'
        )
        return
    
    try:
        new_rate = float(context.args[0])
        if new_rate <= 0:
            raise ValueError("Курс должен быть больше 0")
        
        old_rate = current_usdt_rate
        current_usdt_rate = new_rate
        
        await update.message.reply_text(
            f"✅ <b>Курс USDT обновлен!</b>\n\n"
            f"📉 Старый курс: 1 USDT = {old_rate} РУБ\n"
            f"📈 Новый курс: 1 USDT = {current_usdt_rate} РУБ\n\n"
            f"💡 Изменения применятся для новых заявок.",
            parse_mode='HTML'
        )
        
        logger.info(f"Администратор {update.effective_user.id} изменил курс USDT с {old_rate} на {current_usdt_rate}")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Неверный формат курса.\n"
            "Используйте: <code>/setrate 95.5</code>",
            parse_mode='HTML'
        )


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик данных от WebApp"""
    try:
        # Получаем информацию о пользователе сразу в начале
        user = update.effective_user
        
        # Логируем сырые данные для отладки
        raw_data = update.message.web_app_data.data
        logger.info(f"Получены сырые WebApp данные от пользователя {user.id}: {raw_data}")
        
        # Парсим JSON данные
        data = json.loads(update.message.web_app_data.data)
        logger.info(f"Получены WebApp данные от {user.full_name}: {data}")
        
        # Валидируем данные
        login = data.get('login', '').strip()
        if not login:
            await update.message.reply_text("❌ Логин не может быть пустым. Попробуйте еще раз.")
            return

        # Валидируем и пересчитываем сумму на сервере
        try:
            base_amount = parse_amount(str(data.get('amount', 0)))
            total_rub = calculate_total_with_commission(base_amount)
            total_usdt = calculate_usdt_amount(total_rub)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return
        
        # Формируем сообщение о том что заявка в обработке
        user_message = (
            f"🔄 <b>Заявка в обработке</b>\n\n"
            f"👤 Логин: <code>{login}</code>\n"
            f"💰 Сумма: {base_amount} РУБ\n"
            f"💳 К оплате: <b>{total_rub} РУБ</b> (с комиссией {COMMISSION_PERCENT}%)\n"
            f"💎 Эквивалент: <b>{total_usdt} USDT</b>\n\n"
            f"⏳ <b>Ваша заявка рассматривается</b>\n"
            f"📱 Ожидайте подтверждения от оператора\n\n"
            f"🕐 Время обработки: до 30 минут"
        )
        
        await update.message.reply_text(
            user_message, 
            parse_mode='HTML'
        )
        
        # Формируем сообщение для админа
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Создаем кнопки для управления заявкой  
        # Используем base64 для кодирования логина чтобы избежать проблем с символами
        encoded_login = base64.b64encode(login.encode()).decode()
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Принять заказ", 
                    callback_data=f"accept_{user.id}_{update.effective_chat.id}_{total_rub}_{encoded_login}"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отклонить", 
                    callback_data=f"reject_{user.id}_{update.effective_chat.id}_{total_rub}_{encoded_login}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_message = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ НА ПОПОЛНЕНИЕ</b>\n\n"
            f"⏰ Время: {timestamp}\n"
            f"👤 Пользователь: {user.full_name} (@{user.username or 'без username'})\n"
            f"🆔 User ID: <code>{user.id}</code>\n"
            f"💬 Chat ID: <code>{update.effective_chat.id}</code>\n\n"
            f"📋 <b>Данные заказа:</b>\n"
            f"👤 Логин: <code>{login}</code>\n"
            f"💰 Исходная сумма: {base_amount} РУБ\n"
            f"💳 К оплате: <b>{total_rub} РУБ</b> (комиссия {COMMISSION_PERCENT}%)\n"
            f"💎 Эквивалент: <b>{total_usdt} USDT</b>\n"
            f"💱 Курс: 1 USDT = {current_usdt_rate} РУБ\n\n"
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
        
        logger.info(f"Создан новый заказ от пользователя {user.id} (логин: {login}): {base_amount} РУБ -> {total_rub} РУБ ({COMMISSION_PERCENT}%) = {total_usdt} USDT")
        
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


async def handle_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Принять заказ'"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим данные из callback_data
        parts = query.data.split('_')
        if len(parts) >= 5:
            _, user_id, chat_id, amount, encoded_login = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            # Декодируем логин
            try:
                login = base64.b64decode(encoded_login.encode()).decode()
            except:
                login = "неизвестен"
        else:
            # Старый формат без логина
            _, user_id, chat_id, amount = query.data.split('_', 3)
            login = "неизвестен"
        
        # Отправляем уведомление пользователю о принятии заказа
        accept_message = (
            f"✅ <b>Заказ принят!</b>\n\n"
            f"👤 Логин: <code>{login}</code>\n"
            f"💳 К оплате: {amount} РУБ\n\n"
            f"🔐 <b>С вами свяжется оператор</b>\n"
            f"💎 Он предоставит реквизиты для оплаты через криптовалюту\n\n"
            f"⏳ Ожидайте связи в ближайшее время"
        )
        
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=accept_message,
            parse_mode='HTML'
        )
        
        # Создаем кнопку "Оплачено" для админа
        paid_keyboard = [
            [
                InlineKeyboardButton(
                    "💰 Оплачено", 
                    callback_data=f"paid_{user_id}_{chat_id}_{amount}_{encoded_login}"
                )
            ]
        ]
        paid_reply_markup = InlineKeyboardMarkup(paid_keyboard)
        
        # Обновляем сообщение админа
        await query.edit_message_text(
            text=f"{query.message.text}\n\n✅ <b>СТАТУС: ЗАКАЗ ПРИНЯТ</b>\n💡 Ожидается оплата",
            parse_mode='HTML',
            reply_markup=paid_reply_markup
        )
        
        logger.info(f"Заказ принят для пользователя {user_id} (логин: {login})")
        
    except Exception as e:
        logger.error(f"Ошибка при принятии заказа: {e}")
        await query.edit_message_text(
            text=f"{query.message.text}\n\n❌ <b>ОШИБКА при принятии заказа</b>",
            parse_mode='HTML'
        )


async def handle_paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Оплачено'"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим данные из callback_data
        parts = query.data.split('_')
        if len(parts) >= 5:
            _, user_id, chat_id, amount, encoded_login = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            # Декодируем логин
            try:
                login = base64.b64decode(encoded_login.encode()).decode()
            except:
                login = "неизвестен"
        else:
            # Старый формат без логина
            _, user_id, chat_id, amount = query.data.split('_', 3)
            login = "неизвестен"
        
        # Отправляем уведомление пользователю о завершении
        completion_message = (
            f"🎉 <b>Платеж подтвержден!</b>\n\n"
            f"👤 Логин: <code>{login}</code>\n"
            f"💳 Оплачено: {amount} РУБ\n\n"
            f"✅ <b>Заказ выполнен успешно!</b>\n"
            f"💡 Спасибо за использование нашего сервиса!\n"
            f"❓ Если возникли вопросы, обращайтесь к администратору."
        )
        
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=completion_message,
            parse_mode='HTML'
        )
        
        # Обновляем сообщение админа (убираем кнопки)
        await query.edit_message_text(
            text=f"{query.message.text}\n\n💰 <b>СТАТУС: ОПЛАЧЕНО И ВЫПОЛНЕНО</b>",
            parse_mode='HTML'
        )
        
        logger.info(f"Заказ завершен для пользователя {user_id} (логин: {login})")
        
    except Exception as e:
        logger.error(f"Ошибка при завершении заказа: {e}")
        await query.edit_message_text(
            text=f"{query.message.text}\n\n❌ <b>ОШИБКА при завершении заказа</b>",
            parse_mode='HTML'
        )





async def handle_reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки 'Отклонить'"""
    query = update.callback_query
    await query.answer()
    
    try:
        # Парсим данные из callback_data
        parts = query.data.split('_')
        if len(parts) >= 5:
            _, user_id, chat_id, amount, encoded_login = parts[0], parts[1], parts[2], parts[3], parts[4]
            
            # Декодируем логин
            try:
                login = base64.b64decode(encoded_login.encode()).decode()
            except:
                login = "неизвестен"
        else:
            # Старый формат без логина
            _, user_id, chat_id, amount = query.data.split('_', 3)
            login = "неизвестен"
        
        # Отправляем уведомление пользователю
        reject_message = (
            f"❌ <b>Заказ отклонен</b>\n\n"
            f"👤 Логин: <code>{login}</code>\n"
            f"💳 Сумма: {amount} РУБ\n\n"
            f"😔 К сожалению, ваш заказ не может быть обработан.\n"
            f"📞 Если у вас есть вопросы, обратитесь к администратору.\n\n"
            f"🔄 Вы можете попробовать создать новый заказ через /start"
        )
        
        await context.bot.send_message(
            chat_id=int(chat_id),
            text=reject_message,
            parse_mode='HTML'
        )
        
        # Обновляем сообщение админа
        await query.edit_message_text(
            text=f"{query.message.text}\n\n❌ <b>СТАТУС: ЗАКАЗ ОТКЛОНЕН</b>",
            parse_mode='HTML'
        )
        
        logger.info(f"Заказ пользователя {user_id} (логин: {login}) отклонен")
        
    except Exception as e:
        logger.error(f"Ошибка при отклонении заказа: {e}")
        await query.edit_message_text(
            text=f"{query.message.text}\n\n❌ <b>ОШИБКА при отклонении заказа</b>",
            parse_mode='HTML'
        )


async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик неизвестных сообщений"""
    await update.message.reply_text(
        "🤔 Я не понимаю это сообщение.\n"
        "Воспользуйтесь командой /help для получения справки."
    )




async def main_async():
    """Асинхронная главная функция"""
    logger.info("Запуск Crypto Top-Up Bot...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("setrate", set_rate_command))
    
    # Обработчик WebApp данных
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Обработчики кнопок управления заявками
    application.add_handler(CallbackQueryHandler(handle_accept_callback, pattern="^accept_"))
    application.add_handler(CallbackQueryHandler(handle_paid_callback, pattern="^paid_"))
    application.add_handler(CallbackQueryHandler(handle_reject_callback, pattern="^reject_"))
    
    # Обработчик всех остальных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Бот запущен и готов к работе!")
    logger.info(f"Текущий курс USDT: 1 USDT = {current_usdt_rate} РУБ")
    logger.info(f"Комиссия: {COMMISSION_PERCENT}%")
    
    # Запускаем бота
    async with application:
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
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
