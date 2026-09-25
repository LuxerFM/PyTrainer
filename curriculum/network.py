"""Мережеві задачі: HTTP, JSON, парсинг HTML і вивантаження даних у CSV.

Усі вони працюють із **локальним** тестовим сервером (`fake_api.py`), який
задача приносить із собою. Це принципово:

* не потрібен інтернет — навчання не залежить від чужого Wi-Fi;
* дані завжди ті самі, тому перевірки стабільні;
* але HTTP справжній: реальні коди відповідей, реальний JSON, реальні помилки.

Інтерфейс ми беремо зі стандартної бібліотеки (`urllib`), а не з `requests`,
щоб тренажер лишався без сторонніх залежностей. У підказках показано, як той
самий код виглядає з `requests` — у справжньому проєкті писатимуть саме так.
"""

from .fixtures import FAKE_API
from .schema import code, hint, solution, task

# Спільний для всіх мережевих задач: тестовий «інтернет»
API_FILES = {"fake_api.py": FAKE_API}


TASK_HTTP = task(
    id="m3-http",
    title="HTTP-запит своїми руками",
    level="Середньо",
    minutes=15,
    cheatsheet="modules",
    statement="""
        <p>Будь-яка робота з інтернетом починається з GET-запиту: ти питаєш у
        сервера дані, сервер відповідає кодом (200 — усе гаразд) і тілом
        відповіді. Сьогодні це найпопулярніша задача фрілансера після ботів.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>fetch_json(url)</code>, яка робить GET-запит і
        <b>повертає розібраний JSON</b> — звичайний словник Python.</p>
        <p class="warn">У задачі є файл <code>fake_api.py</code> — це справжній
        HTTP-сервер, піднятий на <code>127.0.0.1</code>. Інтернет не потрібен:
        адреса вже в <code>BASE_URL</code>, дані завжди однакові.</p>
        <h4>З чого складається запит</h4>
        <pre>with urllib.request.urlopen(url) as response:
    text = response.read().decode("utf-8")   # байти → рядок
data = json.loads(text)                      # рядок → словник</pre>
        <p>У тренажері лише три адреси:</p>
        <pre>/rates     курси валют
/products  список товарів
/shop      HTML-сторінка</pre>
        <p class="warn">Не забудь <code>.decode("utf-8")</code>: мережа віддає
        байти, а <code>json.loads()</code> хоче рядок. Саме на цьому спотикаються
        найчастіше.</p>
    """,
    starter="""import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    \"\"\"Повертає розібраний JSON (словник) із цієї адреси.\"\"\"
    # твій код
""",
    checks=[
        code("повертає словник, а не текст",
             'assert isinstance(fetch_json(BASE_URL + "/rates"), dict)'),
        code("читає курси з відповіді",
             'assert fetch_json(BASE_URL + "/rates")["rates"]["USD"] == 41.5'),
        code("працює і з іншою адресою",
             'assert len(fetch_json(BASE_URL + "/products")["products"]) == 3'),
        code("не робить адресу хардкодом",
             "import inspect\n"
             "assert 'http://' not in inspect.getsource(fetch_json), "
             '"адресу бери з параметра url, а не з голови"'),
    ],
    hints=[
        hint("де шукати",
             "У модулі urllib.request є функція urlopen(). Вона повертає "
             "об'єкт-відповідь, у якого треба спитати .read() — це байти."),
        hint("яка конструкція",
             "Два кроки: спершу байти в рядок (decode), потім рядок у словник "
             "(json.loads).\n"
             "with urllib.request.urlopen(url) as response:\n"
             "    text = response.read().decode('utf-8')\n"
             "return json.loads(text)"),
        hint("а як у справжньому проєкті",
             "З бібліотекою requests той самий код коротший:\n"
             "import requests\n"
             "data = requests.get(url, timeout=5).json()\n"
             "Тут ми обійшлися стандартною бібліотекою, щоб не ставити "
             "залежностей, але ідея та сама."),
        solution('''import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        text = response.read().decode("utf-8")
    return json.loads(text)'''),
    ],
    files=API_FILES,
)


TASK_JSON_API = task(
    id="m3-json-api",
    title="Розбір JSON-відповіді",
    level="Легко",
    minutes=12,
    cheatsheet="json",
    statement="""
        <p>Отримати відповідь — половина роботи. Друга половина — дістати з неї
        потрібні числа. Це задача, за яку платять: «зроби, щоб воно рахувало
        курс».</p>
        <h4>Що треба зробити</h4>
        <p>У заготовці вже є готовий <code>fetch_json()</code> — користуйся ним,
        як чужим модулем: це нормально, так і працюють у команді.</p>
        <p>Напиши <code>uah_for(amount, code)</code>: скільки гривень дадуть за
        <code>amount</code> одиниць валюти <code>code</code> за курсом із
        сервера. Якщо такої валюти немає — поверни <code>None</code>
        (у реальних API так само: не вигадуй нуль, а скажи «не знаю»).</p>
        <pre>uah_for(100, "USD")  → 4150.0
uah_for(50, "EUR")   → 2260.0
uah_for(10, "GBP")   → None</pre>
        <h4>Структура відповіді</h4>
        <pre>{"rates": {"USD": 41.5, "EUR": 45.2, "PLN": 10.4}}</pre>
        <p>Тобто потрібне значення лежить у <code>data["rates"][code]</code>.
        А щоб не впасти з <code>KeyError</code> на невідомій валюті, спитай
        <code>if code not in rates</code> або скористайся
        <code>rates.get(code)</code>.</p>
        <p class="warn">Округлюй до копійок: <code>round(сума, 2)</code>.
        Гроші з 15 знаками після коми виглядають непрофесійно.</p>
    """,
    starter="""import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    \"\"\"Уже готовий помічник: читає адресу й розбирає JSON.\"\"\"
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def uah_for(amount, code):
    \"\"\"Скільки гривень дадуть за amount одиниць валюти code.\"\"\"
    # твій код
""",
    checks=[
        code("рахує за курсом долара",
             'assert round(uah_for(100, "USD"), 2) == 4150.0'),
        code("рахує за курсом євро",
             'assert round(uah_for(50, "EUR"), 2) == 2260.0'),
        code("невідома валюта не ламає функцію",
             'assert uah_for(10, "GBP") is None'),
        code("працює з дробовою сумою",
             'assert round(uah_for(1.5, "PLN"), 2) == 15.6'),
    ],
    hints=[
        hint("з чого почати",
             "Спершу отримай словник курсів: data = fetch_json(BASE_URL + "
             '"/rates"), а з нього — data["rates"]. Далі це звичайний словник '
             "«код валюти → курс»."),
        hint("як не впасти на невідомій валюті",
             "Словник уміє безпечно питати: rates.get(code) поверне None, "
             "якщо ключа немає. Саме None тут і потрібен за умовою."),
        solution('''import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def uah_for(amount, code):
    rates = fetch_json(BASE_URL + "/rates")["rates"]
    if code not in rates:
        return None
    return round(amount * rates[code], 2)'''),
    ],
    files=API_FILES,
)


TASK_HTTP_ERROR = task(
    id="m3-http-error",
    title="Коли сервер відповідає помилкою",
    level="Середньо",
    minutes=15,
    cheatsheet="exceptions",
    statement="""
        <p>Найважливіша навичка в роботі з чужими API — не падати, коли чужий
        сервер поводиться погано. Він відповідає 404 (немає такої адреси),
        500 (у нього все зламалося) або просто мовчить. Твоя програма має це
        пережити й сказати людині зрозумілу річ.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>load(url)</code>, яка повертає:</p>
        <ul>
        <li>розібраний JSON, якщо сервер відповів 200;</li>
        <li>рядок <code>"помилка 404"</code> або <code>"помилка 500"</code>,
        якщо сервер відповів помилкою.</li>
        </ul>
        <h4>Навіщо саме так</h4>
        <p>Загублений код помилки — це година здогадок при налагодженні.
        Збережений код — це пів хвилини: «ах, там 500, проблема на їхньому
        боці».</p>
        <h4>Як це виглядає</h4>
        <pre>try:
    ...запит...
except urllib.error.HTTPError as error:
    ... error.code — це 404, 500 тощо ...</pre>
        <p class="warn">urllib кидає <code>HTTPError</code> на будь-який код
        4xx і 5xx — тому без <code>try/except</code> програма просто впаде.</p>
    """,
    starter="""import json
import urllib.error
import urllib.request

from fake_api import BASE_URL


def load(url):
    \"\"\"Дані або рядок «помилка <код>», якщо сервер відповів не 200.\"\"\"
    # твій код
""",
    checks=[
        code("успішний запит повертає дані",
             'assert load(BASE_URL + "/rates")["rates"]["PLN"] == 10.4'),
        code("404 перетворюється на зрозумілий рядок",
             'assert load(BASE_URL + "/nope") == "помилка 404"'),
        code("500 теж не ламає програму",
             'assert load(BASE_URL + "/broken") == "помилка 500"'),
        code("помилка не ховає дані успішної відповіді",
             'assert isinstance(load(BASE_URL + "/products"), dict)'),
    ],
    hints=[
        hint("що саме ловити",
             "urllib.error.HTTPError — це і є відповідь із кодом 4xx/5xx. "
             "У нього є поле .code."),
        hint("яка конструкція",
             "try: запит і json.loads → return словник. except "
             "urllib.error.HTTPError as error: return f\"помилка "
             "{error.code}\"."),
        solution('''import json
import urllib.error
import urllib.request

from fake_api import BASE_URL


def load(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return f"помилка {error.code}"'''),
    ],
    files=API_FILES,
)


TASK_PARSER = task(
    id="m3-parser",
    title="Парсер HTML: ціни зі сторінки",
    level="Середньо",
    minutes=20,
    cheatsheet="strings",
    source="Ідея: BeautifulSoup-парсинг · документація docs.python.org",
    source_url="https://docs.python.org/3/library/html.parser.html",
    statement="""
        <p>Сайт не віддає JSON — він віддає HTML. Дістати з нього ціни й назви
        і є «парсинг», одна з найпопулярніших послуг на фрілансі.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>parse_shop(html)</code>, яка повертає список словників
        <code>{"name": ..., "price": ...}</code> — по одному на товар.</p>
        <pre>&lt;div class="product"&gt;
  &lt;h3 class="name"&gt;Яблуко&lt;/h3&gt;
  &lt;span class="price"&gt;12.5&lt;/span&gt;
&lt;/div&gt;</pre>
        <h4>Як брати</h4>
        <p>У заготовці є готовий <code>fetch_text()</code>, який повертає HTML
        рядком. А далі — регулярні вирази з модуля <code>re</code>:</p>
        <pre>re.findall(r'class="name"&gt;([^&lt;]+)&lt;', html)</pre>
        <p>Круглі дужки у шаблоні означають «запам'ятай цю частину»:
        <code>findall</code> поверне саме те, що всередині дужок.</p>
        <p class="warn">Ціна у HTML — рядок. Щоб отримати число, потрібен
        <code>float(price)</code>.</p>
    """,
    starter="""import re
import urllib.request

from fake_api import BASE_URL


def fetch_text(url):
    \"\"\"Уже готовий помічник: повертає HTML як рядок.\"\"\"
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read().decode("utf-8")


def parse_shop(html):
    \"\"\"Список [{"name": ..., "price": ...}] зі сторінки магазину.\"\"\"
    # твій код
""",
    checks=[
        code("дістає всі три товари",
             'assert len(parse_shop(fetch_text(BASE_URL + "/shop"))) == 3'),
        code("правильно розбирає перший товар",
             'assert parse_shop(fetch_text(BASE_URL + "/shop"))[0] == '
             '{"name": "Яблуко", "price": 12.5}'),
        code("ціна — число, не рядок",
             'data = parse_shop(fetch_text(BASE_URL + "/shop"))\n'
             'assert isinstance(data[0]["price"], float)'),
        code("порожня сторінка дає порожній список",
             'assert parse_shop("<html></html>") == []'),
    ],
    hints=[
        hint("що шукати в HTML",
             "Назви лежать між `class=\"name\">` і `<`, а ціни — між "
             "`class=\"price\">` і `<`. Два окремі findall дадуть два списки, "
             "які треба зібрати парами (zip)."),
        hint("як зібрати пари",
             "zip(names, prices) проходить обома списками одночасно: на "
             "кожному кроці name і price одного товару. Далі збирай словники "
             "у список."),
        hint("а як у справжньому проєкті",
             "З бібліотекою BeautifulSoup це виглядає так:\n"
             "soup = BeautifulSoup(html, \"html.parser\")\n"
             "for card in soup.find_all(\"div\", class_=\"product\"):\n"
             "    name = card.find(\"h3\").text\n"
             "Регулярні вирази працюють, але ламаються на складній верстці — "
             "тому в реальних задачах беруть саме парсер."),
        solution('''import re
import urllib.request

from fake_api import BASE_URL


def fetch_text(url):
    """Уже готовий помічник: повертає HTML як рядок."""
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read().decode("utf-8")


def parse_shop(html):
    names = re.findall(r'class="name">([^<]+)<', html)
    prices = re.findall(r'class="price">([\\d.]+)<', html)
    return [
        {"name": name, "price": float(price)}
        for name, price in zip(names, prices)
    ]'''),
    ],
    files=API_FILES,
)


TASK_CSV_PROJECT = task(
    id="m3-csv",
    title="Проєкт: дані з API → CSV",
    level="Середньо",
    minutes=25,
    cheatsheet="csv",
    statement="""
        <p>Це вже повноцінна робота, за яку платять: узяти дані з чужого API й
        покласти у файл, який клієнт відкриє в Excel. Такі замовлення
        трапляються постійно.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>save_report(path="prices.csv")</code>, яка бере товари
        з адреси <code>/products</code> і записує CSV з двома стовпцями:</p>
        <pre>name,price
Яблуко,12.5
Ноутбук,34000.0
Кава,85.0</pre>
        <ul>
        <li>перший рядок — <b>заголовки</b> (без них Excel покаже кашу);</li>
        <li>функція нічого не повертає, вона створює файл.</li>
        </ul>
        <h4>Важливі дрібниці</h4>
        <pre>with open(path, "w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["name", "price"])</pre>
        <p><code>csv.writer</code> сам подбає про коми й лапки всередині назв —
        не збирай рядок вручну через <code>f"{name},{price}"</code>. Це
        класична помилка, яка ламає файл, щойно в назві з'явиться кома.</p>
        <p><code>newline=""</code> потрібен, щоб на Windows не з'являлися
        порожні рядки.</p>
    """,
    starter="""import csv
import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    \"\"\"Уже готовий помічник: читає адресу й розбирає JSON.\"\"\"
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def save_report(path="prices.csv"):
    \"\"\"Записує товари з /products у CSV-файл.\"\"\"
    # твій код
""",
    checks=[
        code("створює файл із заголовками",
             'save_report()\n'
             'import csv as _csv\n'
             'rows = list(_csv.reader(open("prices.csv", encoding="utf-8")))\n'
             'assert rows[0] == ["name", "price"], f"перший рядок: {rows[0]}"'),
        code("у файлі всі товари з API",
             'assert len(rows) == 4, f"рядків у файлі: {len(rows)}"'),
        code("дані не переплутані місцями",
             'assert rows[1] == ["Яблуко", "12.5"], f"другий рядок: {rows[1]}"'),
        code("працює і з власним іменем файлу",
             'save_report("звіт.csv")\n'
             'assert len(list(_csv.reader(open("звіт.csv", encoding="utf-8")))) == 4'),
    ],
    hints=[
        hint("порядок дій",
             "1) узяти дані: fetch_json(BASE_URL + \"/products\")[\"products\"]. "
             "2) відкрити файл на запис із encoding=\"utf-8\". 3) csv.writer → "
             "writerow для заголовків, потім для кожного товару."),
        hint("звідки брати назву й ціну",
             "Кожен елемент — словник {\"name\": ..., \"price\": ...}. "
             "Тому writerow([product[\"name\"], product[\"price\"]])."),
        solution('''import csv
import json
import urllib.request

from fake_api import BASE_URL


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def save_report(path="prices.csv"):
    products = fetch_json(BASE_URL + "/products")["products"]
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "price"])
        for product in products:
            writer.writerow([product["name"], product["price"]])'''),
    ],
    files=API_FILES,
)


TASK_AI_CLIENT = task(
    id="m5-ai-api",
    title="AI-API: запит із тілом і заголовком",
    level="Складно",
    minutes=25,
    cheatsheet="json",
    source="Ідея: OpenAI Chat Completions API · platform.openai.com",
    source_url="https://platform.openai.com/docs/api-reference/chat",
    statement="""
        <p>Запити до AI-сервісів влаштовані однаково: ти надсилаєш
        <b>POST</b>-запит із JSON у тілі, додаєш заголовок
        <code>Authorization</code> з ключем — і отримуєш JSON у відповідь.
        Навчишся цьому — зможеш під'єднати будь-який AI до будь-якої програми.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>ask(prompt, api_key, model="fake-1")</code>: вона
        надсилає запит на <code>POST {BASE_URL}/v1/chat</code> і повертає
        <b>текст відповіді</b> з <code>choices[0]["message"]["content"]</code>.</p>
        <pre>ask("Привіт", "test-key")
→ "Відповідь на: Привіт"</pre>
        <h4>Тіло запиту</h4>
        <pre>{"model": model,
 "messages": [{"role": "user", "content": prompt}]}</pre>
        <h4>POST вручну</h4>
        <pre>request = urllib.request.Request(
    url,
    data=json.dumps(body).encode("utf-8"),
    headers={"Content-Type": "application/json",
             "Authorization": f"Bearer {api_key}"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=3) as response:
    ...</pre>
        <p class="warn">Тіло запиту — це <b>байти</b>, тому
        <code>.encode("utf-8")</code> обов'язковий. А ключ ніколи не пиши
        прямо в коді: у справжньому проєкті його беруть із змінної середовища.</p>
    """,
    starter="""import json
import urllib.request

from fake_api import BASE_URL


def ask(prompt, api_key, model="fake-1"):
    \"\"\"Надсилає PROMPT до AI-API і повертає текст відповіді.\"\"\"
    # твій код
""",
    checks=[
        code("повертає текст відповіді",
             'assert ask("Привіт", "test-key") == "Відповідь на: Привіт"'),
        code("передає власний промпт",
             'assert ask("2 + 2", "k") == "Відповідь на: 2 + 2"'),
        code("без ключа сервер відмовляє",
             'import urllib.error\n'
             'try:\n'
             '    ask("Привіт", "")\n'
             'except urllib.error.HTTPError as error:\n'
             '    assert error.code == 401, f"код {error.code}"\n'
             'else:\n'
             '    raise AssertionError("запит без Authorization має провалитись")'),
        code("модель потрапляє в запит",
             'import json as _json, urllib.request as _u\n'
             'from fake_api import BASE_URL as _base\n'
             '_body = _json.dumps({"model": "fake-9",\n'
             '                     "messages": [{"role": "user", "content": "x"}]}).encode()\n'
             '_req = _u.Request(_base + "/v1/chat", data=_body,\n'
             '                  headers={"Authorization": "Bearer k",\n'
             '                           "Content-Type": "application/json"}, method="POST")\n'
             'with _u.urlopen(_req, timeout=3) as _r:\n'
             '    assert _json.loads(_r.read().decode())["model"] == "fake-9"'),
    ],
    hints=[
        hint("що відрізняє POST від GET",
             "У GET дані лише в адресі. У POST тіло запиту передається окремо "
             "— через параметр data у urllib.request.Request, і воно мусить "
             "бути байтами."),
        hint("заголовки",
             "Сервер перевіряє два заголовки: Content-Type (що ми надіслали "
             "JSON) і Authorization (наш ключ). Ключ передають у вигляді "
             "«Bearer <ключ>»."),
        hint("як дістати текст",
             "Відповідь: {\"choices\": [{\"message\": {\"content\": \"...\"}}]}. "
             "Це словник у списку в словнику — іди по кроках і не бійся "
             "перевірити структуру через print."),
        solution('''import json
import urllib.request

from fake_api import BASE_URL


def ask(prompt, api_key, model="fake-1"):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        BASE_URL + "/v1/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        answer = json.loads(response.read().decode("utf-8"))
    return answer["choices"][0]["message"]["content"]'''),
    ],
    files=API_FILES,
)


INTERNET_TASKS = (
    TASK_HTTP,
    TASK_JSON_API,
    TASK_HTTP_ERROR,
    TASK_PARSER,
    TASK_CSV_PROJECT,
)

__all__ = [
    "INTERNET_TASKS",
    "TASK_AI_CLIENT",
    "TASK_CSV_PROJECT",
    "TASK_HTTP",
    "TASK_HTTP_ERROR",
    "TASK_JSON_API",
    "TASK_PARSER",
]
