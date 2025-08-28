#!/usr/bin/env python3
"""
Простий HTTP сервер для WebApp
Запускає локальний сервер на порту 8000 для папки webapp
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Порт для сервера
PORT = 8000

# Шлях до папки webapp
WEBAPP_DIR = Path(__file__).parent / "webapp"

class WebAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBAPP_DIR, **kwargs)
    
    def end_headers(self):
        # Додаємо CORS заголовки для Telegram WebApp
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    print(f"🌐 Запуск HTTP сервера для WebApp...")
    print(f"📁 Директорія: {WEBAPP_DIR}")
    print(f"🔗 Локальний URL: http://localhost:{PORT}")
    print(f"📱 Для Telegram потрібен HTTPS URL від ngrok!")
    print(f"⚡ Запусти ngrok в іншому терміналі: ngrok http {PORT}")
    print(f"❌ Для зупинки: Ctrl+C")
    print("-" * 50)
    
    # Перевіряємо чи існує папка webapp
    if not WEBAPP_DIR.exists():
        print(f"❌ Помилка: папка {WEBAPP_DIR} не знайдена!")
        return
    
    # Перевіряємо чи існує index.html
    index_file = WEBAPP_DIR / "index.html"
    if not index_file.exists():
        print(f"❌ Помилка: файл {index_file} не знайдений!")
        return
    
    try:
        with socketserver.TCPServer(("", PORT), WebAppHandler) as httpd:
            print(f"✅ Сервер запущено на http://localhost:{PORT}")
            print(f"📄 Доступні файли в {WEBAPP_DIR}:")
            for file in WEBAPP_DIR.iterdir():
                if file.is_file():
                    print(f"   - {file.name}")
            print()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Сервер зупинено")
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Порт {PORT} вже використовується!")
            print(f"💡 Спробуй інший порт або зупини процес на порту {PORT}")
        else:
            print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    main()
