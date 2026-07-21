"""
===========================================================
EvenOddBasketBot

Файл:
web_server.py

Назначение:
Публичный HTTP-сервер Render:
- web-интерфейс Mission Control;
- JSON API с реальной статистикой;
- статические файлы и health check.
===========================================================
"""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from dashboard import build_dashboard_html, build_error_html
from dashboard_data import build_dashboard_payload


PROJECT_DIR = Path(__file__).resolve().parent
STATIC_DIR = (PROJECT_DIR / "dashboard_static").resolve()


class DashboardHandler(BaseHTTPRequestHandler):
    """Обрабатывает браузер, API и проверки Render."""

    server_version = "EvenOddBasketBot/15.1"

    def log_message(self, format_string, *args):
        """Сохраняет компактный лог сервера."""

        print("WEB:", format_string % args)

    def do_HEAD(self):
        request_path = urlparse(self.path).path
        if request_path in {"/", "/health", "/api/health"}:
            self._send_bytes(200, b"", "text/plain; charset=utf-8", "no-store")
        else:
            self._send_bytes(404, b"", "text/plain; charset=utf-8", "no-store")

    def do_GET(self):
        request_path = urlparse(self.path).path

        if request_path.startswith("/static/"):
            self._serve_static(request_path.removeprefix("/static/"))
            return

        if request_path == "/favicon.ico":
            self._serve_static("brand/favicon.png")
            return

        if request_path in {"/health", "/api/health"}:
            self._send_json({"ok": True, "service": "EvenOddBasketBot"})
            return

        if request_path == "/api/dashboard":
            try:
                self._send_json(build_dashboard_payload())
            except Exception as error:
                print("Ошибка API Dashboard:", error)
                self._send_json(
                    {
                        "error": "dashboard_unavailable",
                        "message": "Не удалось сформировать статистику",
                    },
                    status_code=500,
                )
            return

        if request_path not in {"/", "/index.html"}:
            self._send_bytes(
                404,
                b"Not found",
                "text/plain; charset=utf-8",
                "no-store",
            )
            return

        try:
            html = build_dashboard_html()
            status_code = 200
        except Exception as error:
            html = build_error_html(error)
            status_code = 500

        self._send_bytes(
            status_code,
            html.encode("utf-8"),
            "text/html; charset=utf-8",
            "no-store",
        )

    def _serve_static(self, relative_path: str):
        """Безопасно отдаёт файл только внутри dashboard_static."""

        clean_relative = unquote(relative_path).lstrip("/")
        file_path = (STATIC_DIR / clean_relative).resolve()

        if file_path != STATIC_DIR and STATIC_DIR not in file_path.parents:
            self._send_bytes(403, b"Forbidden", "text/plain", "no-store")
            return
        if not file_path.is_file():
            self._send_bytes(404, b"Not found", "text/plain", "no-store")
            return

        content_type, _ = mimetypes.guess_type(file_path.name)
        content_type = content_type or "application/octet-stream"
        cache = "public, max-age=86400" if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} else "public, max-age=900"
        self._send_bytes(200, file_path.read_bytes(), content_type, cache)

    def _send_json(self, payload, status_code=200):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(status_code, body, "application/json; charset=utf-8", "no-store")

    def _send_bytes(self, status_code, body, content_type, cache_control):
        try:
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache_control)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
            self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
            self.end_headers()
            if body:
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            pass


def run_web_server():
    """Запускает многопоточный web-сервер на порту Render."""

    port = int(os.getenv("PORT", "10000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    server.daemon_threads = True
    print(f"EvenOddBasketBot Live Dashboard запущен на порту {port}")
    server.serve_forever()
