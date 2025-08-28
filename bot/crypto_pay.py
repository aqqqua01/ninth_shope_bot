#!/usr/bin/env python3
"""
Crypto Pay API Integration
Интеграция с Crypto Pay API для автоматических криптоплатежей
"""

import os
import json
import logging
import hashlib
import hmac
from typing import Dict, List, Optional
import aiohttp
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class CryptoPayAPI:
    """Класс для работы с Crypto Pay API"""
    
    def __init__(self, api_token: str, testnet: bool = False):
        self.api_token = api_token
        self.base_url = "https://testnet-pay.crypt.bot/api" if testnet else "https://pay.crypt.bot/api"
        self.headers = {
            "Crypto-Pay-API-Token": api_token,
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Выполняет HTTP запрос к API"""
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, headers=self.headers, params=data) as response:
                        result = await response.json()
                else:
                    async with session.post(url, headers=self.headers, json=data) as response:
                        result = await response.json()
                
                if result.get("ok"):
                    return result.get("result", {})
                else:
                    logger.error(f"Crypto Pay API error: {result.get('error')}")
                    raise Exception(f"API Error: {result.get('error')}")
                    
            except Exception as e:
                logger.error(f"Request to {url} failed: {e}")
                raise
    
    async def get_me(self) -> Dict:
        """Получает информацию о приложении"""
        return await self._make_request("GET", "getMe")
    
    async def get_exchange_rates(self) -> List[Dict]:
        """Получает курсы обмена криптовалют"""
        return await self._make_request("GET", "getExchangeRates")
    
    async def get_currencies(self) -> List[Dict]:
        """Получает список поддерживаемых валют"""
        return await self._make_request("GET", "getCurrencies")
    
    async def create_invoice(self, 
                           currency_type: str = "fiat",
                           fiat: str = "RUB", 
                           amount: str = "100",
                           accepted_assets: str = "USDT,TON,BTC,ETH",
                           description: str = "Steam пополнение",
                           payload: str = "",
                           expires_in: int = 3600) -> Dict:
        """Создает инвойс для оплаты"""
        
        data = {
            "currency_type": currency_type,
            "fiat": fiat,
            "amount": amount,
            "accepted_assets": accepted_assets,
            "description": description,
            "expires_in": expires_in
        }
        
        if payload:
            data["payload"] = payload
            
        return await self._make_request("POST", "createInvoice", data)
    
    async def get_invoices(self, invoice_ids: Optional[List[int]] = None) -> List[Dict]:
        """Получает список инвойсов"""
        data = {}
        if invoice_ids:
            data["invoice_ids"] = ",".join(map(str, invoice_ids))
        
        return await self._make_request("GET", "getInvoices", data)
    
    def verify_webhook_signature(self, body: str, signature: str) -> bool:
        """Проверяет подпись webhook"""
        try:
            secret = hashlib.sha256(self.api_token.encode()).digest()
            calculated_signature = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
            return calculated_signature == signature
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False


class CurrencyConverter:
    """Конвертер валют через Crypto Pay API"""
    
    def __init__(self, crypto_pay: CryptoPayAPI):
        self.crypto_pay = crypto_pay
        self._rates_cache = {}
        self._cache_timestamp = 0
    
    async def get_rates_from_rub(self) -> Dict[str, Decimal]:
        """Получает курсы криптовалют к рублю"""
        try:
            rates = await self.crypto_pay.get_exchange_rates()
            rub_rates = {}
            
            for rate in rates:
                if rate.get("target") == "RUB" and rate.get("is_valid"):
                    asset = rate.get("source")
                    rate_value = Decimal(str(rate.get("rate", "0")))
                    if rate_value > 0:
                        # Обратный курс: 1 RUB = X crypto
                        rub_rates[asset] = Decimal("1") / rate_value
            
            logger.info(f"Loaded exchange rates: {rub_rates}")
            return rub_rates
            
        except Exception as e:
            logger.error(f"Failed to get exchange rates: {e}")
            return {}
    
    async def convert_rub_to_crypto(self, rub_amount: Decimal) -> Dict[str, str]:
        """Конвертирует рубли в криптовалюты"""
        rates = await self.get_rates_from_rub()
        conversions = {}
        
        for asset, rate in rates.items():
            crypto_amount = rub_amount * rate
            # Округляем до разумного количества знаков
            if asset in ["BTC", "ETH"]:
                # Для дорогих валют больше знаков после запятой
                formatted = crypto_amount.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
            elif asset in ["USDT", "USDC"]:
                # Для стейблкоинов 2 знака
                formatted = crypto_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # Для остальных 4 знака
                formatted = crypto_amount.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            
            conversions[asset] = str(formatted)
        
        return conversions


# Глобальные переменные для инициализации
crypto_pay_api = None
currency_converter = None

def init_crypto_pay(api_token: str, testnet: bool = False):
    """Инициализация Crypto Pay API"""
    global crypto_pay_api, currency_converter
    
    if not api_token:
        logger.warning("CRYPTO_PAY_API_TOKEN не установлен")
        return None
    
    crypto_pay_api = CryptoPayAPI(api_token, testnet)
    currency_converter = CurrencyConverter(crypto_pay_api)
    
    logger.info("Crypto Pay API инициализирован")
    return crypto_pay_api
