"""
===========================================================
EvenOddBasketBot

Файл:
web_server.py

Назначение:
Запускает HTTP-сервер для Render
и показывает Mission Control.
===========================================================
"""
from pathlib import Path
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from dashboard import build_dashboard_html, build_error_html

PROJECT_DIR = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_DIR / "dashboard_static"

class DashboardHandler(BaseHTTPRequestHandler):
    """
    Обрабатывает запросы Render и браузера.
    """

    def send_body(self, body):
        """
        Безопасно отправляет ответ браузеру.

        Иногда браузер закрывает соединение раньше,
        чем сервер успевает отправить все данные.
        Это не должно выводить большой traceback.
        """

        try:
            self.wfile.write(body)

        except (
                BrokenPipeError,
                ConnectionAbortedError,
                ConnectionResetError,
        ):
            print(
                "Браузер закрыл соединение "
                "до завершения отправки ответа."
            )

    def do_HEAD(self):
        """
        Health Check Render.
        """

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )
        self.end_headers()

    def do_GET(self):
        """
        Показывает Mission Control.
        """
        # Отдаём CSS-файл Dashboard
        if self.path == "/static/styles.css":
            css_path = STATIC_DIR / "styles.css"

            try:
                body = css_path.read_bytes()

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "text/css; charset=utf-8",
                )
                self.send_header(
                    "Content-Length",
                    str(len(body)),
                )
                self.send_header(
                    "Cache-Control",
                    "no-store",
                )
                self.end_headers()
                self.send_body(body)

            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

            return
        # Браузер автоматически запрашивает иконку сайта.
        # Пока отдельной иконки нет, возвращаем пустой ответ.
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        # Отдельный простой адрес проверки состояния
        if self.path == "/health":
            body = "OK".encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.send_body(body)
            return

        try:
            html = build_dashboard_html()
            status_code = 200

        except Exception as error:
            print("Ошибка формирования Dashboard:", error)

            html = build_error_html(error)
            status_code = 500

        body = html.encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.send_header(
            "Cache-Control",
            "no-store",
        )
        self.end_headers()

        self.send_body(body)


def run_web_server():
    """
    Запускает web-сервер на порту Render.
    """

    port = int(os.getenv("PORT", "10000"))

    server = HTTPServer(
        ("0.0.0.0", port),
        DashboardHandler,
    )

    print(f"Mission Control запущен на порту {port}")

    server.serve_forever()