"""Задачі «налагодь код»: треба знайти й виправити помилки в готовому коді.

Це найближче до справжньої роботи, що є в тренажері. Замовник не дає порожній
файл — він дає код, який «чомусь не працює». Уміння швидко знайти причину й
виправити її — половина зарплати програміста.

Тому тут заготовка — це **зламаний код**, а не порожня функція. Рішення
завжди починається з упорядкованого процесу: подивитись, що має бути →
запустити → побачити, що вийшло насправді → звузити місце до одного рядка.

Баги в цих задачах не «синтаксичні»: код запускається без помилок і
повертає якесь значення. Воно просто **не те** — саме так виглядають 90%
реальних багів.
"""

from .fixtures import DIRTY_PRICES_CSV
from .schema import code, hint, solution, task

BROKEN_AVERAGE = '''def average(numbers):
    """Середнє арифметичне списку чисел."""
    total = 0
    for index in range(len(numbers) - 1):
        total += numbers[index]
    return total // len(numbers)


if __name__ == "__main__":
    print(average([1, 2, 3, 4]))    # очікували 2.5
    print(average([10]))            # очікували 10.0
'''

BROKEN_GRADES = '''def best_student(grades):
    """Ім'я учня з найвищим балом ("" для порожнього словника)."""
    best_name = ""
    best_score = 101
    for name, score in grades.items():
        if score > best_score:
            best_name = name
            best_score = score
    return best_name


def mark(score):
    """95 → "відмінно", 60 → "зараховано", 59 → "не зараховано"."""
    if score > 60:
        return "зараховано"
    elif score >= 90:
        return "відмінно"
    return "не зараховано"


if __name__ == "__main__":
    print(mark(95))                 # очікували "відмінно"
    print(mark(60))                 # очікували "зараховано"
'''

BROKEN_TOTALS = '''import csv


def total_by_currency(path):
    """Суми цін за кожною валютою: {"UAH": 34087.5}."""
    totals = {}
    with open(path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            totals[row["currency"]] = row["price"]
    return totals


if __name__ == "__main__":
    print(total_by_currency("prices.csv"))   # очікували {'UAH': 34087.5}
'''

TASK_DEBUG_AVERAGE = task(
    id="m4-debug-average",
    title="Налагодь: середнє арифметичне",
    level="Середньо",
    minutes=15,
    cheatsheet="lists",
    statement="""
        <p>Ось функція, яка «майже працює». Вона запускається без помилок і
        повертає число — просто не те, яке потрібне. Саме так виглядає
        більшість багів у справжньому коді.</p>
        <h4>Що функція мусить робити</h4>
        <pre>average([1, 2, 3, 4])  → 2.5       (10 / 4)
average([10])          → 10.0
average([2, 4])        → 3.0</pre>
        <p>Зараз у ній <b>дві</b> помилки, і жодна з них не синтаксична.</p>
        <h4>Як шукати баг — за порядком</h4>
        <ol>
        <li>Подивись, що функція має повернути (умова вище).</li>
        <li>Запусти заготовку звичайним «Запустити» — подивись на вивід у
        консолі. Там є коментарі з очікуваними числами.</li>
        <li>Уяви, що робить кожен рядок, із конкретними числами з прикладу.</li>
        <li>Виправ <b>один</b> рядок — і знову запусти. Так баг ніколи не
        «загубиться за іншими виправленнями».</li>
        </ol>
        <p class="warn">Питання-підказка до циклу: скільки разів він
        виконується для списку з чотирьох чисел — і чи потрапляє туди
        останнє?</p>
    """,
    starter=BROKEN_AVERAGE,
    checks=[
        code("середнє з чотирьох чисел",
             "assert average([1, 2, 3, 4]) == 2.5"),
        code("середнє з одного числа",
             "assert average([10]) == 10.0"),
        code("результат — число з комою",
             "assert isinstance(average([1, 2]), float)"),
        code("середнє з двох чисел",
             "assert average([2, 4]) == 3.0"),
        code("працює з від'ємними числами",
             "assert average([-2, 2]) == 0.0"),
    ],
    hints=[
        hint("дивлячись на цикл",
             "for index in range(len(numbers) - 1) — спробуй руками: для "
             "списку [1, 2, 3, 4] len(numbers) - 1 це 3, а range(3) дає 0, 1, "
             "2. Чи додається четверте число?"),
        hint("дивлячись на return",
             "Оператор // залишає лише цілу частину: 9 // 2 дає 4, а не 4.5. "
             "Для середнього потрібне звичайне ділення /."),
        solution('''def average(numbers):
    """Середнє арифметичне списку чисел."""
    total = 0
    for number in numbers:
        total += number
    return total / len(numbers)'''),
    ],
)


TASK_DEBUG_GRADES = task(
    id="m4-debug-grades",
    title="Налагодь: оцінки й порядок умов",
    level="Середньо",
    minutes=18,
    cheatsheet="conditions",
    statement="""
        <p>Тут зламані дві функції, і помилки в них різні за характером: одна
        в <b>початковому значенні</b>, друга — у <b>порядку умов</b>.
        Друга трапляється навіть у досвідчених людей.</p>
        <h4>Що мусить робити код</h4>
        <pre>mark(95)  → "відмінно"
mark(90)  → "відмінно"
mark(60)  → "зараховано"
mark(59)  → "не зараховано"

best_student({"Аня": 90, "Богдан": 75})  → "Аня"
best_student({"Аня": 90, "Ігор": 90})    → "Аня"   (рівні бали — перший у словнику)
best_student({})                         → ""</pre>
        <h4>Дві підказки про природу цих багів</h4>
        <ul>
        <li>У <code>best_student</code> початкове значення <code>best_score</code>
        вибране так, що умова всередині циклу не спрацьовує <b>жодного
        разу</b>. Порахуй, з яким балом треба порівнювати.</li>
        <li>У <code>mark</code> умови перевіряються зверху вниз і перша ж
        збіжна «перехоплює» випадок. Подумай, для якого балу це ламає
        порядок.</li>
        </ul>
        <p class="warn">Це задача про вдумливе читання. Запустити перевірки —
        корисно, але спершу спробуй знайти баги очима: так навичка
        закріплюється краще.</p>
    """,
    starter=BROKEN_GRADES,
    checks=[
        code("95 балів — відмінно", 'assert mark(95) == "відмінно"'),
        code("90 балів — відмінно", 'assert mark(90) == "відмінно"'),
        code("60 балів — зараховано", 'assert mark(60) == "зараховано"'),
        code("59 балів — не зараховано", 'assert mark(59) == "не зараховано"'),
        code("найкращий учень",
             'assert best_student({"Аня": 90, "Богдан": 75}) == "Аня"'),
        code("рівні бали — перемагає перший",
             'assert best_student({"Аня": 90, "Ігор": 90}) == "Аня"'),
        code("порожній словник",
             "assert best_student({}) == \"\""),
    ],
    hints=[
        hint("як перевірити best_student",
             "Пройди цикл руками: best_score починається зі 101, а бали — 90 і "
             "75. Чи може бал бути більшим за 101? Яке початкове значення "
             "зробило б умову справдженою?"),
        hint("як перевірити mark",
             "Іди за коментарями зверху вниз: чи зупинить функція перевірку на "
             "90 раніше, ніж дійде до умови про 90? Коли бал дорівнює 60, "
             "умова score > 60 істинна чи хибна?"),
        solution('''def best_student(grades):
    """Ім'я учня з найвищим балом ("" для порожнього словника)."""
    best_name = ""
    best_score = -1
    for name, score in grades.items():
        if score > best_score:
            best_name = name
            best_score = score
    return best_name


def mark(score):
    """95 → "відмінно", 60 → "зараховано", 59 → "не зараховано"."""
    if score >= 90:
        return "відмінно"
    elif score >= 60:
        return "зараховано"
    return "не зараховано"'''),
    ],
)


TASK_DEBUG_TOTALS = task(
    id="m4-debug-file",
    title="Налагодь: суми з CSV-файлу",
    level="Складно",
    minutes=25,
    cheatsheet="csv",
    statement="""
        <p>Це вже схоже на справжнє замовлення: є файл від клієнта, у ньому
        ціни, і треба порахувати суму за кожною валютою. Файл при цьому
        <b>брудний</b> — він так і приходить від людей.</p>
        <h4>Що функція мусить робити</h4>
        <ul>
        <li>повертати словник «валюта → сума»: <code>{"UAH": 34087.5}</code>;</li>
        <li>суми — числа з комою (<code>float</code>), не рядки;</li>
        <li>рядки, де ціни немає або вона не число, <b>тихо пропускати</b>
        (це нормально: у звіті клієнта буває порожня клітинка);</li>
        <li>від'ємні ціни враховувати — це знижки;</li>
        <li>порожній файл (лише заголовки) → <code>{}</code>.</li>
        </ul>
        <p>У задачі вже є файл <code>prices.csv</code> — саме з нього беруться
        числа. У заготовці <b>три</b> помилки, і кожна дасть неправильний
        результат, а не помилку виконання.</p>
        <pre>name,price,currency
Яблуко,12.5,UAH        → 12.5
Ноутбук,34000,UAH      → 34000
Кава,85,UAH            → 85
Невідомо,,UAH          → пропустити (ціни немає)
Знижка,-10,UAH         → -10
                       разом: 34087.5</pre>
        <p class="warn">Запусти заготовку: вона виведе щось дивне — усі
        значення будуть рядками, і замість суми стоятиме останнє число.</p>
    """,
    starter=BROKEN_TOTALS,
    checks=[
        code("рахує суму з prices.csv",
             'assert total_by_currency("prices.csv") == {"UAH": 34087.5}'),
        code("сума — число, не рядок",
             'assert isinstance(total_by_currency("prices.csv")["UAH"], float)'),
        code("різні валюти не змішуються",
             'with open("two.csv", "w", encoding="utf-8") as _f:\n'
             '    _f.write("name,price,currency\\nА,10,UAH\\nБ,3.5,USD\\n")\n'
             'assert total_by_currency("two.csv") == {"UAH": 10.0, "USD": 3.5}'),
        code("нечислова ціна не ламає функцію",
             'with open("mix.csv", "w", encoding="utf-8") as _f:\n'
             '    _f.write("name,price,currency\\nА,10,UAH\\nБ,,UAH\\n'
             'В,abc,UAH\\nГ,2.5,USD\\n")\n'
             'assert total_by_currency("mix.csv") == {"UAH": 10.0, "USD": 2.5}'),
        code("порожній файл",
             'with open("empty.csv", "w", encoding="utf-8") as _f:\n'
             '    _f.write("name,price,currency\\n")\n'
             'assert total_by_currency("empty.csv") == {}'),
    ],
    hints=[
        hint("перша помилка",
             "У CSV усі значення — рядки. Тому price приходить як \"12.5\", і "
             "коли «додати» рядки, вони не додаються. Потрібне перетворення "
             "float()."),
        hint("друга помилка",
             "totals[row[\"currency\"]] = row[\"price\"] — це присвоєння, а не "
             "додавання. Кожен новий рядок переписує попередній. Як зробити "
             "«додати до того, що вже є», якщо ключа може ще не існувати?"),
        hint("третя помилка",
             "float(\"\") кидає ValueError — а рядок «Невідомо» має бути просто "
             "пропущений. Обгорни перетворення в try/except і зроби "
             "continue, якщо не вийшло."),
        solution('''import csv


def total_by_currency(path):
    """Суми цін за кожною валютою: {"UAH": 34087.5}."""
    totals = {}
    with open(path, encoding="utf-8") as file:
        for row in csv.DictReader(file):
            try:
                price = float(row["price"])
            except (TypeError, ValueError):
                continue
            currency = row["currency"]
            totals[currency] = totals.get(currency, 0.0) + price
    return totals'''),
    ],
    files={"prices.csv": DIRTY_PRICES_CSV},
)


DEBUG_TASKS = (
    TASK_DEBUG_AVERAGE,
    TASK_DEBUG_GRADES,
    TASK_DEBUG_TOTALS,
)

__all__ = [
    "DEBUG_TASKS",
    "TASK_DEBUG_AVERAGE",
    "TASK_DEBUG_GRADES",
    "TASK_DEBUG_TOTALS",
]
