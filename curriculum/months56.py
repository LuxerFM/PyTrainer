"""Місяці 5–6 — спеціалізація під гроші: боти, автоматизація, AI-інтеграції.

Тут з'являються перші задачі «як на роботі»: повторні спроби при збоях,
одночасне виконання замість послідовного, розбір команд бота й витягування
даних із відповіді AI.

Частина пунктів лишається задачами-позначками: вони потребують сторонніх
бібліотек (`aiogram`, `openpyxl`, `selenium`) і справжньої мережі, тому їх
робимо разом із реальним проєктом, а не в тренажері.
"""

from .network import TASK_AI_CLIENT
from .schema import Month, code, hint, solution, stub, task, topic

TASK_RETRY = task(
    id="m5-errors",
    title="Обробка помилок: повторна спроба з паузою",
    level="Складно",
    minutes=20,
    cheatsheet="exceptions",
    statement="""
        <p>У реальному житті мережа зникає, чужий API відповідає «зайнятий», а
        база на секунду блокується. Професіонал не здається після першої
        помилки — він <b>пробує ще раз</b>, і кожна пауза довша за попередню.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>with_retry(action, attempts=3, delay=0.5, sleep=time.sleep)</code>:</p>
        <ul>
        <li>викликає <code>action()</code> і повертає результат;</li>
        <li>якщо <code>action()</code> підняла помилку — чекає <code>delay</code>
        секунд і пробує знову, <b>подвоюючи</b> паузу: 0.5 → 1.0 → 2.0;</li>
        <li> якщо всі <code>attempts</code> спроби невдалі — піднімає
        <b>останню</b> помилку далі (не свою, а ту саму);</li>
        <li>після останньої спроби <b>не</b> чекає даремно.</li>
        </ul>
        <h4>Навіщо тут параметр sleep</h4>
        <p>Це прийом, який використовують у справжніх тестах: щоб не чекати
        насправді, функція отримує «свій» <code>sleep</code>. У перевірках нам
        передадуть підставний — він лише записує, скільки ми «поспали».
        Завдяки цьому задача проходить за долі секунди.</p>
        <pre>calls = []
def flaky():
    calls.append(1)
    if len(calls) &lt; 3:
        raise ConnectionError("немає зв'язку")
    return "дані"

with_retry(flaky, sleep=записати)   → "дані"
# спроб: 3, паузи: [0.5, 1.0]</pre>
        <p class="warn">Заготовка просто викликає <code>action()</code> один
        раз — тому не проходить жодну перевірку, крім найпростішої.</p>
    """,
    starter='''import time


def with_retry(action, attempts=3, delay=0.5, sleep=time.sleep):
    """Пробує action() до attempts разів із паузами, що подвоюються."""
    return action()
''',
    checks=[
        code("пробує ще раз і повертає результат",
             'calls = []\n'
             'def flaky():\n'
             '    calls.append(1)\n'
             '    if len(calls) < 3:\n'
             '        raise ConnectionError("немає зв\'язку")\n'
             '    return "дані"\n'
             'pauses = []\n'
             'assert with_retry(flaky, sleep=pauses.append) == "дані"\n'
             'assert len(calls) == 3, f"спроб: {len(calls)}"'),
        code("пауза подвоюється",
             'assert pauses == [0.5, 1.0], f"паузи: {pauses}"'),
        code("успіх з першого разу без пауз",
             'def fine():\n'
             '    return 7\n'
             'pauses2 = []\n'
             'assert with_retry(fine, sleep=pauses2.append) == 7\n'
             'assert pauses2 == []'),
        code("після всіх спроб помилка йде далі",
             'def always():\n'
             '    raise ValueError("завжди погано")\n'
             'try:\n'
             '    with_retry(always, attempts=2, delay=0.01, sleep=lambda d: None)\n'
             'except ValueError as error:\n'
             '    assert str(error) == "завжди погано", str(error)\n'
             'else:\n'
             '    raise AssertionError("помилку треба підняти далі")'),
        code("робить рівно attempts спроб",
             'count = []\n'
             'def bad():\n'
             '    count.append(1)\n'
             '    raise TimeoutError("тихо")\n'
             'try:\n'
             '    with_retry(bad, attempts=4, delay=0.01, sleep=lambda d: None)\n'
             'except TimeoutError:\n'
             '    pass\n'
             'assert len(count) == 4, f"спроб: {len(count)}"'),
        code("піднімає САМЕ останню помилку",
             'seen = []\n'
             'def two():\n'
             '    seen.append(1)\n'
             '    raise RuntimeError("перша" if len(seen) == 1 else "друга")\n'
             'try:\n'
             '    with_retry(two, attempts=2, delay=0.01, sleep=lambda d: None)\n'
             'except RuntimeError as error:\n'
             '    assert str(error) == "друга", str(error)'),
    ],
    hints=[
        hint("як побудувати цикл",
             "Тобі потрібен цикл на attempts кроків і try/except усередині. "
             "Якщо виклик вдався — return результату одразу. Якщо ні — "
             "запам'ятай помилку й чекай перед наступною спробою."),
        hint("що робити з помилкою, яку зловив",
             "Змінна помилки живе лише всередині except, тому збережи її в "
             "окрему змінну поза циклом — інакше після циклу нічого буде "
             "піднімати через raise."),
        hint("як не чекати даремно",
             "Пауза потрібна лише МІЖ спробами. Тобто остання невдала спроба "
             "не має спати — після неї ми вже просто піднімаємо помилку. "
             "Перевірка дивиться на список пауз: для трьох спроб їх рівно дві."),
        solution('''import time


def with_retry(action, attempts=3, delay=0.5, sleep=time.sleep):
    """Пробує action() до attempts разів із паузами, що подвоюються."""
    last_error = None
    for attempt in range(attempts):
        try:
            return action()
        except Exception as error:       # будь-який збій має право на повтор
            last_error = error
            if attempt < attempts - 1:
                sleep(delay)
                delay *= 2
    raise last_error'''),
    ],
)


TASK_ASYNC = task(
    id="m5-async",
    title="Одночасно, а не по черзі",
    level="Складно",
    minutes=20,
    cheatsheet="modules",
    source="Ідея: asyncio.gather · документація docs.python.org",
    source_url="https://docs.python.org/3/library/asyncio-task.html",
    statement="""
        <p>Ось причина, чому боти й парсери пишуть на <code>async</code>:
        поки одна задача чекає на відповідь мережі, програма може робити
        інші. Три запити по секунді — це 1 секунда замість 3.</p>
        <h4>Що треба зробити</h4>
        <p>Написати <code>run_all(jobs)</code>, яка запускає всі завдання
        <b>одночасно</b> й повертає список результатів <b>у тому ж порядку</b>,
        у якому вони були передані.</p>
        <pre>await run_all([("перший", 0.1), ("другий", 0.1)])
→ ["перший готово", "другий готово"]</pre>
        <p>Функція <code>slow_work()</code> уже готова — її чіпати не треба.</p>
        <h4>Як зрозуміти, що це справді одночасно</h4>
        <p>Одна з перевірок <b>вимірює час</b>: чотири завдання по 0.25 с
        разом мають укластися менш ніж у 0.7 с. По черзі було б 1.0 с — тобто
        різниця помітна з першого погляду.</p>
        <pre>result = await asyncio.gather(одне, друге, третє)</pre>
        <p><code>gather</code> запускає все одразу й збирає результати в
        список. Саме тому він зберігає порядок: перший результат — від
        першого завдання, навіть якщо воно завершилось останнім.</p>
        <p class="warn">Заготовка працює правильно, але чекає на кожне завдання
        по черзі — тому повільна. Це теж реальний клас проблем: код не
        падає, він просто робить усе в 4 рази довше.</p>
    """,
    starter='''import asyncio


async def slow_work(name, seconds):
    """Імітація довгої роботи: чекає seconds і повертає «ім'я готово»."""
    await asyncio.sleep(seconds)
    return f"{name} готово"


async def run_all(jobs):
    """Запускає всі завдання ОДНОЧАСНО, повертає результати в тому ж порядку."""
    results = []
    for name, seconds in jobs:          # так воно чекає кожного по черзі
        results.append(await slow_work(name, seconds))
    return results
''',
    checks=[
        code("повертає результати",
             'assert asyncio.run(run_all([("а", 0.0), ("б", 0.0)])) == '
             '["а готово", "б готово"]'),
        code("порядок як у списку, а не за швидкістю",
             'assert asyncio.run(run_all([("повільний", 0.05), ("швидкий", 0.0)]))'
             ' == ["повільний готово", "швидкий готово"]'),
        code("порожній список завдань",
             'assert asyncio.run(run_all([])) == []'),
        code("повертає список, а не інший тип",
             'assert isinstance(asyncio.run(run_all([("а", 0.0)])), list)'),
        code("працює одночасно: 4 завдання по 0.25 с вкладаються у 0.7 с",
             'import time\n'
             'jobs = [("а", 0.25), ("б", 0.25), ("в", 0.25), ("г", 0.25)]\n'
             'start = time.perf_counter()\n'
             'asyncio.run(run_all(jobs))\n'
             'elapsed = time.perf_counter() - start\n'
             'assert elapsed < 0.7, f"витрачено {elapsed:.2f} с — схоже, по черзі"'),
    ],
    hints=[
        hint("що саме треба змінити",
             "await зупиняє функцію, поки завдання не завершиться. Щоб вони "
             "працювали разом, треба не чекати на кожне окремо, а передати "
             "їх усі одній службовій функції, яка запустить їх гуртом."),
        hint("який інструмент",
             "asyncio.gather(*coroutines) запускає всі передані корутини "
             "одночасно і повертає їхні результати списком у тому ж порядку. "
             "Корутини — це те, що повертає виклик async-функції без await."),
        hint("як зібрати список корутин",
             "slow_work(name, seconds) повертає корутину, а не результат. "
             "Тому можна зробити список таких викликів для кожного job і "
             "розпакувати його у gather через *."),
        solution('''import asyncio


async def slow_work(name, seconds):
    """Імітація довгої роботи: чекає seconds і повертає «ім'я готово»."""
    await asyncio.sleep(seconds)
    return f"{name} готово"


async def run_all(jobs):
    """Запускає всі завдання ОДНОЧАСНО, повертає результати в тому ж порядку."""
    return await asyncio.gather(
        *(slow_work(name, seconds) for name, seconds in jobs)
    )'''),
    ],
)


TASK_BOT_PARSE = task(
    id="m5-bot-parse",
    title="Серце бота: розбір команд",
    level="Середньо",
    minutes=18,
    cheatsheet="strings",
    source="Ідея: команди ботів у Telegram · core.telegram.org/bots",
    source_url="https://core.telegram.org/bots/features#commands",
    statement="""
        <p>Будь-який Telegram-бот починається з розбору повідомлення. Це не
        нудна деталь: саме тут народжується вся логіка бота, і саме тут легко
        зробити код, який потім важко розширювати.</p>
        <h4>Що треба зробити</h4>
        <p><code>parse_command(text)</code> — розбирає повідомлення людини:</p>
        <ul>
        <li>команда починається з <code>/</code> і приводиться до нижнього
        регістру (люди пишуть <code>/Старт</code> і <code>/START</code>);</li>
        <li>усе після команди — список аргументів;</li>
        <li>зайві пробіли, на початку й усередині, не мають значення;</li>
        <li>звичайне повідомлення без <code>/</code> → <code>None</code>.</li>
        </ul>
        <pre>parse_command("/старт")             → ("/старт", [])
parse_command("/замов 2 піци")      → ("/замов", ["2", "піци"])
parse_command("   /СТАРТ  ")        → ("/старт", [])
parse_command("привіт")             → None</pre>
        <h4>І друга функція — «маршрутизатор»</h4>
        <p><code>dispatch(text, handlers)</code> бере словник
        <code>{"команда": функція}</code> і викликає потрібну функцію з
        аргументами:</p>
        <pre>handlers = {"/сума": lambda a, b: int(a) + int(b)}
dispatch("/сума 2 3", handlers)      → 5
dispatch("/невідомо", handlers)      → None
dispatch("привіт", handlers)         → None
</pre>
        <p>Такий поділ — <b>розбір</b> і <b>обробка</b> окремо — і є професійний
        підхід: щоб додати нову команду, ти просто дописуєш рядок у словник.</p>
    """,
    starter='''def parse_command(text):
    """Повертає (команда, список аргументів) або None для звичайного тексту."""
    # твій код


def dispatch(text, handlers):
    """Викликає потрібний обробник із словника або повертає None."""
    # твій код
''',
    checks=[
        code("команда без аргументів",
             'assert parse_command("/старт") == ("/старт", [])'),
        code("команда з аргументами",
             'assert parse_command("/замов 2 піци") == ("/замов", ["2", "піци"])'),
        code("звичайний текст — це не команда",
             'assert parse_command("привіт") is None'),
        code("регістр і зайві пробіли",
             'assert parse_command("   /СТАРТ  ") == ("/старт", [])'),
        code("кілька пробілів між аргументами",
             'assert parse_command("/пошук   дві   піци") == '
             '("/пошук", ["дві", "піци"])'),
        code("порожній текст",
             'assert parse_command("") is None and parse_command("   ") is None'),
        code("dispatch викликає обробник",
             'assert dispatch("/сума 2 3", {"/сума": lambda a, b: int(a) + int(b)}) == 5'),
        code("dispatch без аргументів",
             'counter = []\n'
             'assert dispatch("/раз", {"/раз": lambda: counter.append(1) or "ок"}) == "ок"'),
        code("невідома команда і звичайний текст",
             'assert dispatch("/нема", {"/є": lambda: 1}) is None\n'
             'assert dispatch("привіт", {"/є": lambda: 1}) is None'),
    ],
    hints=[
        hint("як розібрати рядок",
             "text.split() без аргументів сам прибирає зайві пробіли й робить "
             "список слів. Перше слово — команда, решта — аргументи."),
        hint("як перевірити, що це команда",
             "Команда починається з \"/\". Для порожнього тексту list[0] "
             "впаде з IndexError, тому спершу перевір, що список не "
             "порожній."),
        hint("як зробити dispatch",
             "Спершу розбери текст своєю ж parse_command. Якщо вона повернула "
             "None — повертай None. Якщо команди немає серед ключів словника "
             "handlers — теж None. Інакше виклич обробник і передай йому "
             "розпаковані аргументи через *."),
        solution('''def parse_command(text):
    """Повертає (команда, список аргументів) або None для звичайного тексту."""
    parts = text.split()
    if not parts or not parts[0].startswith("/"):
        return None
    return parts[0].lower(), parts[1:]


def dispatch(text, handlers):
    """Викликає потрібний обробник із словника або повертає None."""
    parsed = parse_command(text)
    if parsed is None:
        return None
    command, args = parsed
    handler = handlers.get(command)
    if handler is None:
        return None
    return handler(*args)'''),
    ],
)


TASK_AI_PROMPT = task(
    id="m5-ai-prompt",
    title="Дістати дані з відповіді AI",
    level="Складно",
    minutes=22,
    cheatsheet="json",
    source="Ідея: структуровані відповіді моделей · docs.python.org (json)",
    source_url="https://docs.python.org/3/library/json.html#json.JSONDecoder",
    statement="""
        <p>AI відповідає <b>текстом</b>, а програмі потрібні дані. Типова
        ситуація: попросив модель віддати JSON — вона його віддала, але
        загорнула в пояснення, у потрійні лапки, а іноді обірвала.</p>
        <h4>Що треба зробити</h4>
        <p>Напиши <code>extract_json(text)</code>, яка дістає з тексту
        <b>перший повний JSON-об'єкт</b> і повертає його як словник. Якщо
        об'єкта немає або він не закінчений — <code>None</code> (у реальній
        програмі тут буде повторний запит до моделі).</p>
        <pre>extract_json('{"число": 7}')                     → {"число": 7}
extract_json('Ось результат: {"число": 7}. Гарного дня!')
                                                 → {"число": 7}
extract_json('```json\\n{"a": [1, 2]}\\n```')     → {"a": [1, 2]}
extract_json('{"a": {"b": 2}}')                  → {"a": {"b": 2}}
extract_json('{"a": 1')                          → None (не закінчено)
extract_json('не знаю, вибач')                   → None</pre>
        <h4>Чому наївний підхід не працює</h4>
        <p>Спокуса — вирізати регулярним виразом: <code>re.search(r"\\{.*\\}", text)</code>.
        Але <code>.*</code> жадібний і захопить <b>останню</b> дужку в тексті, а
        вкладений об'єкт зламає підрахунок. Тому або рахуємо глибину дужок
        вручну, або користуємось тим, що вже вміє сам модуль json.</p>
        <pre>json.JSONDecoder().raw_decode(fragment)</pre>
        <p><code>raw_decode</code> читає <b>рівно один</b> JSON-об'єкт з початку
        рядка і каже, де він закінчився, — зайвий текст йому не заважає. Це
        найкоротший правильний розв'язок.</p>
    """,
    starter='''import json


def extract_json(text):
    """Перший повний JSON-об\'єкт із тексту або None."""
    # твій код
''',
    checks=[
        code("чистий JSON",
             'assert extract_json(\'{"число": 7}\') == {"число": 7}'),
        code("JSON усередині пояснень",
             'assert extract_json(\'Ось результат: {"число": 7}. Гарного дня!\')'
             ' == {"число": 7}'),
        code("JSON у подвійних лапках-огорожі",
             'assert extract_json(\'```json\\n{"a": [1, 2]}\\n```\') == {"a": [1, 2]}'),
        code("вкладені об'єкти",
             'assert extract_json(\'до: {"a": {"b": 2}} після\') == {"a": {"b": 2}}'),
        code("обірваний JSON",
             'assert extract_json(\'{"a": 1\') is None'),
        code("тексту без JSON",
             'assert extract_json("не знаю, вибач") is None'),
        code("дужки всередині рядка не плутають",
             'assert extract_json(\'{"текст": "дужки } і {"}\') == '
             '{"текст": "дужки } і {"}'),
        code("повертає саме словник",
             'assert extract_json("число 7 без дужок") is None'),
    ],
    hints=[
        hint("з чого почати",
             "JSON-об'єкт завжди починається з {. Знайди позицію першої такої "
             "дужки — далі працюєш лише з частиною рядка від неї."),
        hint("як обрізати в правильному місці",
             "Треба знайти парну закривну дужку. Рахуй глибину: { збільшує, } "
             "зменшує. Коли глибина повернулась до нуля — об'єкт закінчився. "
             "Ускладнення: дужки всередині рядків не рахуються."),
        hint("коротший шлях",
             "Модуль json уміє читати один об'єкт із початку рядка: "
             "json.JSONDecoder().raw_decode(fragment) повертає пару "
             "(об'єкт, скільки символів прочитано). Якщо фрагмент починається "
             "з { і він обірваний — буде ValueError, його треба зловити."),
        solution('''import json


def extract_json(text):
    """Перший повний JSON-об'єкт із тексту або None."""
    start = text.find("{")
    if start == -1:
        return None
    try:
        data, _ = json.JSONDecoder().raw_decode(text[start:])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None'''),
    ],
)


MONTH = Month(
    title="Місяці 5–6 · Спеціалізація під гроші",
    subtitle="Обираємо один напрям і робимо в ньому проєкт",
    topics=(
        topic(
            "Спільне для всіх напрямів",
            TASK_ASYNC,
            TASK_RETRY,
            stub("m5-deploy", "Деплой на Railway або VPS"),
        ),
        topic(
            "Варіант А · Telegram-боти (найшвидші гроші)",
            TASK_BOT_PARSE,
            stub("m5-bot-basic", "aiogram: бот, що відповідає"),
            stub("m5-bot-menu", "Кнопки, меню, стани"),
            stub("m5-bot-project", "Проєкт: бот для бізнесу (запис або замовлення)"),
        ),
        topic(
            "Варіант Б · Парсинг та автоматизація",
            stub("m5-selenium", "Selenium для сайтів із JavaScript"),
            stub("m5-excel", "openpyxl і pandas: звіти замість ручної роботи"),
            stub("m5-automation-project", "Проєкт: автоматизація реальної рутини"),
        ),
        topic(
            "Варіант В · AI-інтеграції (найгарячіше)",
            TASK_AI_CLIENT,
            TASK_AI_PROMPT,
            stub("m5-ai-stream", "Стрімінг відповідей"),
            stub("m5-ai-project", "Проєкт: бот або скрипт з AI всередині"),
        ),
    ),
)
