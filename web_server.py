"""
===========================================================
EvenOddBasketBot

Файл:
web_server.py

Назначение:
Запускает HTTP-сервер для Render, показывает Mission Control
и безопасно отдаёт фирменные статические файлы.
===========================================================
"""

import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from dashboard import build_dashboard_html, build_error_html


PROJECT_DIR = Path(__file__).resolve().parent
STATIC_DIR = (PROJECT_DIR / "dashboard_static").resolve()


class DashboardHandler(BaseHTTPRequestHandler):
    """Обрабатывает запросы Render и браузера."""

    def send_body(self, body):
        """Безопасно отправляет ответ браузеру."""

        try:
            self.wfile.write(body)
        except (
            BrokenPipeError,
            ConnectionAbortedError,
            ConnectionResetError,
        ):
            print("Браузер закрыл соединение до завершения ответа.")

    def do_HEAD(self):
        """Health Check Render."""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        """Показывает Mission Control или отдаёт статический файл."""

        request_path = urlparse(self.path).path

        if request_path.startswith("/static/"):
            self._serve_static(request_path.removeprefix("/static/"))
            return

        if request_path == "/favicon.ico":
            self._serve_static("brand/favicon.png")
            return

        if request_path == "/health":
            self._send_bytes(
                status_code=200,
                body=b"OK",
                content_type="text/plain; charset=utf-8",
                cache_control="no-store",
            )
            return

        try:
            html = build_dashboard_html()
            status_code = 200
        except Exception as error:
            print("Ошибка формирования Dashboard:", error)
            html = build_error_html(error)
            status_code = 500

        self._send_bytes(
            status_code=status_code,
            body=html.encode("utf-8"),
            content_type="text/html; charset=utf-8",
            cache_control="no-store",
        )

    def _serve_static(self, relative_path):
        """Отдаёт файл только из dashboard_static без path traversal."""

        clean_relative = unquote(relative_path).lstrip("/")
        file_path = (STATIC_DIR / clean_relative).resolve()

        if file_path != STATIC_DIR and STATIC_DIR not in file_path.parents:
            self.send_response(403)
            self.end_headers()
            return

        if not file_path.is_file():
            self.send_response(404)
            self.end_headers()
            return

        content_type, _ = mimetypes.guess_type(file_path.name)
        content_type = content_type or "application/octet-stream"

        self._send_bytes(
            status_code=200,
            body=file_path.read_bytes(),
            content_type=content_type,
            cache_control="public, max-age=3600",
        )

    def _send_bytes(
        self,
        status_code,
        body,
        content_type,
        cache_control=None,
    ):
        """Общий ответ для HTML, CSS, изображений и health-check."""

        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))

        if cache_control:
            self.send_header("Cache-Control", cache_control)

        self.end_headers()
        self.send_body(body)


def run_web_server():
    """Запускает web-сервер на порту Render."""

    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)

    print(f"EvenOddBasketBot Mission Control запущен на порту {port}")
    server.serve_forever()
