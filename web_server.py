"""
Мини-сервер для Render.
Нужен только чтобы Render видел открытый порт.
"""

import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class HealthHandler(BaseHTTPRequestHandler):

    # Отключаем лишние логи HTTP
    def log_message(self, format, *args):
        return

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def run_web_server():
    port = int(os.getenv("PORT", "10000"))

    server = HTTPServer(("0.0.0.0", port), HealthHandler)

    print(f"Web server запущен на порту {port}")

    server.serve_forever()