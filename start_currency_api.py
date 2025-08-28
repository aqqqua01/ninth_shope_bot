#!/usr/bin/env python3
"""
Скрипт для запуска Currency API сервера
"""

import subprocess
import sys
import os

def main():
    """Запускает Currency API сервер"""
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Создайте .env файл с переменными:")
        print("   CRYPTO_PAY_API_TOKEN=your_token_here")
        print("   CRYPTO_PAY_TESTNET=true")
        return
    
    print("🚀 Запуск Currency API сервера...")
    print("📍 API будет доступен по адресу: http://localhost:8001")
    print("🔄 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        # Запускаем сервер
        subprocess.run([sys.executable, "currency_api_server.py"])
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main()
