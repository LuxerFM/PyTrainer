"""Допоміжні файли, які задача приносить із собою.

Головний із них — `fake_api.py`: крихітний HTTP-сервер на 127.0.0.1, який
піднімається всередині процесу розв'язку.

Навіщо це потрібно: задачі про мережі не мають залежати від справжнього
інтернету. Інакше навчання ламається через чужий Wi-Fi, а перевірки стають
нестабільними (сьогодні курс НБУ один, завтра інший). Локальний сервер дає
справжній HTTP, справжній JSON і справжні коди відповідей — але завжди ті самі
дані. Це той самий підхід, який використовують у тестах справжніх проєктів.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# fake_api.py — тестовий «інтернет» для задач про мережі
# --------------------------------------------------------------------------

FAKE_API = '''"""Тестовий інтернет: маленький HTTP-сервер на 127.0.0.1.

Справжній інтернет для навчання не потрібен — сервер уже піднято, і він
віддає ті самі дані щоразу. Адреса лежить у BASE_URL.

Доступи:
    GET  /rates        курси валют:   {"rates": {"USD": 41.5, ...}}
    GET  /products     список товарів: {"products": [{"name": ..., "price": ...}]}
    GET  /shop         сторінка з HTML (для парсера)
    GET  /broken       сервер відповідає помилкою 500
    POST /v1/chat      як справжній AI-API: потрібен заголовок Authorization
    будь-що інше       404
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RATES = {"USD": 41.5, "EUR": 45.2, "PLN": 10.4}

PRODUCTS = [
    {"name": "Яблуко", "price": 12.5},
    {"name": "Ноутбук", "price": 34000.0},
    {"name": "Кава", "price": 85.0},
]

SHOP_HTML = """<html><body>
<h1>Магазин</h1>
<div class=\\"product\\"><h3 class=\\"name\\">Яблуко</h3><span class=\\"price\\">12.5</span></div>
<div class=\\"product\\"><h3 class=\\"name\\">Ноутбук</h3><span class=\\"price\\">34000.0</span></div>
<div class=\\"product\\"><h3 class=\\"name\\">Кава</h3><span class=\\"price\\">85.0</span></div>
</body></html>"""


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload, content_type="application/json"):
        body = payload if isinstance(payload, str) else json.dumps(payload)
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):                                   # noqa: N802
        if self.path.startswith("/rates"):
            self._send(200, {"rates": RATES})
        elif self.path.startswith("/products"):
            self._send(200, {"products": PRODUCTS})
        elif self.path.startswith("/shop"):
            self._send(200, SHOP_HTML, "text/html")
        elif self.path.startswith("/broken"):
            self._send(500, {"error": "щось зламалося на сервері"})
        else:
            self._send(404, {"error": "немає такої адреси"})

    def do_POST(self):                                  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        if not self.path.startswith("/v1/chat"):
            self._send(404, {"error": "немає такої адреси"})
            return
        # Як справжній API: заголовок мусить бути, і в ньому мусить бути ключ.
        token = (self.headers.get("Authorization") or "").replace("Bearer", "").strip()
        if not token:
            self._send(401, {"error": "потрібен непорожній ключ у заголовку Authorization"})
            return
        try:
            request = json.loads(raw)
            prompt = request["messages"][-1]["content"]
        except (ValueError, KeyError, IndexError):
            self._send(400, {"error": "не схоже на запит до чату"})
            return
        # «Модель»: відповідає так, щоб результат можна було перевірити
        self._send(200, {
            "model": request.get("model", "fake-1"),
            "choices": [{"message": {"role": "assistant",
                                     "content": "Відповідь на: " + str(prompt)}}],
        })

    def log_message(self, *args):                       # тихо, без спаму
        pass


def start():
    """Піднімає сервер у фоновому потоці й повертає його адресу."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d" % server.server_port


BASE_URL = start()
'''


# --------------------------------------------------------------------------
# calculator.py — модуль, до якого треба написати тести
# --------------------------------------------------------------------------

CALCULATOR = '''"""Крихітний модуль, до якого треба написати тести.

Він навмисно невеличкий: писати тести до великого коду — окрема навичка,
а тут важливо відчути сам процес.
"""


def divide(first, second):
    """Ділить одне число на інше."""
    return first / second


def average(numbers):
    """Середнє арифметичне списку."""
    if not numbers:
        raise ValueError("Порожній список не має середнього")
    return sum(numbers) / len(numbers)


def to_int(text, default=0):
    """Перетворює рядок у число, а якщо не виходить — повертає default."""
    try:
        return int(text)
    except (TypeError, ValueError):
        return default
'''


# --------------------------------------------------------------------------
# prices.csv — «чужий» файл із даними, який треба почистити
# --------------------------------------------------------------------------

DIRTY_PRICES_CSV = """name,price,currency
Яблуко,12.5,UAH
Ноутбук,34000,UAH
Кава,85,UAH
Невідомо,,UAH
Знижка,-10,UAH
"""


__all__ = ["FAKE_API", "CALCULATOR", "DIRTY_PRICES_CSV"]
