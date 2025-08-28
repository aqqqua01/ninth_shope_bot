#!/usr/bin/env python3
"""
Currency API Server
Сервер для получения курсов криптовалют для WebApp
"""

import os
import asyncio
import logging
from decimal import Decimal
from aiohttp import web, ClientSession
from aiohttp.web import middleware
from dotenv import load_dotenv
from bot.crypto_pay import init_crypto_pay, currency_converter

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
CRYPTO_PAY_API_TOKEN = os.getenv('CRYPTO_PAY_API_TOKEN')
CRYPTO_PAY_TESTNET = os.getenv('CRYPTO_PAY_TESTNET', 'true').lower() == 'true'
API_PORT = int(os.getenv('CURRENCY_API_PORT', '8001'))

# Инициализация Crypto Pay
if CRYPTO_PAY_API_TOKEN:
    init_crypto_pay(CRYPTO_PAY_API_TOKEN, CRYPTO_PAY_TESTNET)
    logger.info("Crypto Pay API инициализирован")
else:
    logger.warning("CRYPTO_PAY_API_TOKEN не установлен")

# CORS middleware
@middleware
async def cors_handler(request, handler):
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers.update({
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    })
    return response

async def get_crypto_rates(request):
    """Получает курсы криптовалют к рублю"""
    try:
        if not currency_converter:
            return web.json_response({
                'success': False,
                'error': 'Crypto Pay API не инициализирован'
            }, status=500)
        
        # Получаем курсы
        rates = await currency_converter.get_rates_from_rub()
        
        # Форматируем ответ
        formatted_rates = {}
        for asset, rate in rates.items():
            formatted_rates[asset] = {
                'rate': str(rate),
                'symbol': asset,
                'name': get_currency_name(asset)
            }
        
        return web.json_response({
            'success': True,
            'rates': formatted_rates
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения курсов: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def convert_rub_to_crypto(request):
    """Конвертирует рубли в криптовалюты"""
    try:
        data = await request.json()
        rub_amount = Decimal(str(data.get('amount', '0')))
        
        if rub_amount <= 0:
            return web.json_response({
                'success': False,
                'error': 'Сумма должна быть больше 0'
            }, status=400)
        
        if not currency_converter:
            return web.json_response({
                'success': False,
                'error': 'Crypto Pay API не инициализирован'
            }, status=500)
        
        # Конвертируем
        conversions = await currency_converter.convert_rub_to_crypto(rub_amount)
        
        # Форматируем для отображения
        formatted_conversions = {}
        for asset, amount in conversions.items():
            formatted_conversions[asset] = {
                'amount': amount,
                'symbol': asset,
                'name': get_currency_name(asset),
                'formatted': f"{amount} {asset}"
            }
        
        return web.json_response({
            'success': True,
            'rub_amount': str(rub_amount),
            'conversions': formatted_conversions
        })
        
    except Exception as e:
        logger.error(f"Ошибка конвертации: {e}")
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

def get_currency_name(asset: str) -> str:
    """Возвращает человекочитаемое название криптовалюты"""
    names = {
        'USDT': 'Tether',
        'TON': 'Toncoin',
        'BTC': 'Bitcoin',
        'ETH': 'Ethereum',
        'LTC': 'Litecoin',
        'BNB': 'BNB',
        'TRX': 'TRON',
        'USDC': 'USD Coin'
    }
    return names.get(asset, asset)

async def health_check(request):
    """Проверка здоровья API"""
    return web.json_response({
        'status': 'ok',
        'crypto_pay_enabled': currency_converter is not None
    })

def create_app():
    """Создает приложение aiohttp"""
    app = web.Application(middlewares=[cors_handler])
    
    # Маршруты
    app.router.add_get('/api/rates', get_crypto_rates)
    app.router.add_post('/api/convert', convert_rub_to_crypto)
    app.router.add_get('/health', health_check)
    
    return app

async def main():
    """Основная функция запуска сервера"""
    app = create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', API_PORT)
    await site.start()
    
    logger.info(f"Currency API сервер запущен на порту {API_PORT}")
    logger.info(f"Доступные эндпойнты:")
    logger.info(f"  GET  http://localhost:{API_PORT}/api/rates")
    logger.info(f"  POST http://localhost:{API_PORT}/api/convert")
    logger.info(f"  GET  http://localhost:{API_PORT}/health")
    
    # Держим сервер запущенным
    try:
        await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        logger.info("Завершение работы сервера...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
