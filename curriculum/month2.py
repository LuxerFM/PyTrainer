"""Місяць 2 — база, частина 2: ООП, винятки, дані, SQL і те, що питають на співбесіді.

Тут 12 задач, які можна розв'язувати вже зараз. Практика поза тренажером
(venv, Git, pytest) лишається задачею-позначкою: її робиш у своєму терміналі,
а не в редакторі тренажера.
"""

from .schema import Month, code, hint, solution, stdout, stub, task, topic

MONTH = Month(
    title="Місяць 2 · База, частина 2",
    subtitle="ООП, дані та інструменти, яких чекають на співбесіді",
    topics=(
        topic(
            "Тиждень 5 · Класи та об'єкти",
            task(
                id="m2-class-expense",
                title="Перший клас: Expense",
                level="Середньо",
                statement="""
                    <p>Клас — це креслення об'єкта. <code>__init__</code> викликається,
                    коли об'єкт створюють, і саме там з'являються його поля.</p>
                    <h4>Що треба зробити</h4>
                    <p>Створи клас <code>Expense</code> (витрата) з полями
                    <code>category</code> і <code>amount</code> та методами:</p>
                    <ul>
                        <li><code>describe()</code> → <code>"їжа: 120 грн"</code>;</li>
                        <li><code>is_big()</code> → <code>True</code>, якщо сума 1000 і більше.</li>
                    </ul>
                    <h4>Приклад</h4>
                    <pre>expense = Expense("їжа", 120)
expense.describe()   →  "їжа: 120 грн"
expense.is_big()     →  False</pre>
                    <p class="warn">Забути <code>self</code> у параметрах методу —
                    найчастіша помилка новачка: Python передає об'єкт першим
                    аргументом автоматично.</p>
                """,
                starter='''class Expense:
    def __init__(self, category, amount):
        # збережи category і amount у self
        pass

    def describe(self):
        return "?"

    def is_big(self):
        return False
''',
                checks=[
                    code("поля зберігаються",
                         "expense = Expense('їжа', 120)\n"
                         "assert expense.category == 'їжа', 'немає поля category'\n"
                         "assert expense.amount == 120, 'немає поля amount'"),
                    code("describe описує витрату",
                         "assert Expense('їжа', 120).describe() == 'їжа: 120 грн'"),
                    code("велика витрата розпізнається",
                         "assert Expense('таксі', 1500).is_big() is True\n"
                         "assert Expense('таксі', 50).is_big() is False"),
                    code("is_big на межі — 1000 теж велика",
                         "assert Expense('техніка', 1000).is_big() is True"),
                ],
                hints=[
                    hint("де шукати", "У __init__ присвой полям: self.category = category. "
                                      "Методи також отримують self першим."),
                    hint("формат describe",
                         "return f'{self.category}: {self.amount} грн'"),
                    solution("""class Expense:
    def __init__(self, category, amount):
        self.category = category
        self.amount = amount

    def describe(self):
        return f"{self.category}: {self.amount} грн"

    def is_big(self):
        return self.amount >= 1000"""),
                ],
            ),
            task(
                id="m2-class-account",
                title="Клас із поведінкою: Account",
                level="Складно",
                minutes=15,
                statement="""
                    <p>Справжній клас не просто зберігає дані — він <b>захищає</b> їх
                    від неправильних дій. Саме тому тут з'явиться <code>raise</code>.</p>
                    <h4>Що треба зробити</h4>
                    <p>Клас <code>Account</code> (рахунок):</p>
                    <ul>
                        <li><code>Account(owner, balance=0)</code> — власник і баланс;</li>
                        <li><code>deposit(amount)</code> — додає гроші й повертає новий баланс;</li>
                        <li><code>withdraw(amount)</code> — знімає гроші, а якщо їх не
                        вистачає, кидає <code>ValueError("Недостатньо коштів")</code>;</li>
                        <li><code>statement()</code> → <code>"Аня: 500 грн"</code>.</li>
                    </ul>
                    <h4>Приклад</h4>
                    <pre>account = Account("Аня", 100)
account.deposit(50)      # 150
account.withdraw(40)     # баланс 110
account.statement()      →  "Аня: 110 грн"
account.withdraw(500)    →  ValueError</pre>
                """,
                starter='''class Account:
    def __init__(self, owner, balance=0):
        pass

    def deposit(self, amount):
        pass

    def withdraw(self, amount):
        pass

    def statement(self):
        return "?"
''',
                checks=[
                    code("рахунок починається з нуля",
                         "account = Account('Аня')\n"
                         "assert account.owner == 'Аня'\n"
                         "assert account.balance == 0, 'баланс за замовчуванням має бути 0'"),
                    code("deposit повертає новий баланс",
                         "account = Account('Аня', 100)\n"
                         "assert account.deposit(50) == 150\n"
                         "assert account.balance == 150"),
                    code("withdraw зменшує баланс",
                         "\n".join([
                             "account = Account('Аня', 100)",
                             "account.withdraw(40)",
                             "assert account.balance == 60",
                         ])),
                    code("withdraw не дає піти в мінус",
                         "\n".join([
                             "account = Account('Аня', 10)",
                             "try:",
                             "    account.withdraw(50)",
                             "except ValueError as error:",
                             "    assert 'Недостатньо коштів' in str(error), \\",
                             "        'потрібне повідомлення «Недостатньо коштів»'",
                             "else:",
                             "    raise AssertionError('зняття понад баланс має кидати ValueError')",
                             "assert account.balance == 10, 'баланс не має змінитись'",
                         ])),
                    code("statement показує власника й баланс",
                         "assert Account('Аня', 500).statement() == 'Аня: 500 грн'"),
                ],
                hints=[
                    hint("де шукати", "deposit — це self.balance += amount і return self.balance. "
                                      "Той самий підхід у withdraw, але з перевіркою."),
                    hint("як кинути помилку",
                         'if amount > self.balance:\n'
                         '    raise ValueError("Недостатньо коштів")'),
                    solution('''class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Недостатньо коштів")
        self.balance -= amount
        return self.balance

    def statement(self):
        return f"{self.owner}: {self.balance} грн"'''),
                ],
            ),
        ),
        topic(
            "Тиждень 6 · Модулі та бібліотеки",
            task(
                id="m2-math",
                title="Модуль math: не винаходь колесо",
                level="Легко",
                statement="""
                    <p>Стандартна бібліотека Python — це тисячі готових рішень.
                    Модуль <code>math</code> уже вміє корені, число π і степені.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>circle_area(radius)</code> — площа кола (πr²);</li>
                        <li><code>hypotenuse(a, b)</code> — довжина гіпотенузи
                        (√(a² + b²)).</li>
                    </ul>
                    <pre>circle_area(1)     →  3.14159…
hypotenuse(3, 4)   →  5.0</pre>
                    <h4>Правило</h4>
                    <p>Перед тим як писати формулу руками — подивись, чи немає її в
                    стандартній бібліотеці. Це називають «не винаходити колесо».</p>
                """,
                starter="""import math


def circle_area(radius):
    return 0


def hypotenuse(a, b):
    return 0
""",
                checks=[
                    code("площа кола", "assert round(circle_area(1), 2) == 3.14"),
                    code("площа кола радіуса 2",
                         "assert round(circle_area(2), 2) == 12.57, 'перевір формулу πr²'"),
                    code("гіпотенуза 3-4-5",
                         "assert hypotenuse(3, 4) == 5.0"),
                    code("гіпотенуза працює з дробовими",
                         "assert round(hypotenuse(1, 1), 3) == 1.414"),
                ],
                hints=[
                    hint("де шукати", "math.pi — це число π, math.sqrt(x) — корінь, "
                                      "а x ** 2 — квадрат."),
                    solution("""import math


def circle_area(radius):
    return math.pi * radius ** 2


def hypotenuse(a, b):
    return math.sqrt(a ** 2 + b ** 2)"""),
                ],
            ),
            task(
                id="m2-random",
                title="Модуль random і чому seed — це важливо",
                level="Середньо",
                statement="""
                    <p><code>random</code> дає випадкові значення. Але код із
                    випадковістю неможливо перевірити — тому існує
                    <code>random.seed(число)</code>: після нього «випадкові» числа
                    стають передбачуваними для того, хто знає seed.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>pick(numbers, seed)</code> — фіксує seed і повертає
                        один випадковий елемент списку;</li>
                        <li><code>shuffle_copy(numbers, seed)</code> — повертає
                        <b>перемішану копію</b>, не змінюючи початковий список.</li>
                    </ul>
                    <p class="warn">Саме через seed тести зможуть перевірити твою
                    функцію: однаковий seed — однаковий результат.</p>
                """,
                starter="""import random


def pick(numbers, seed):
    # random.seed(seed), потім random.choice(numbers)
    return None


def shuffle_copy(numbers, seed):
    copy = numbers[:]
    # перемішай копію з фіксованим seed
    return copy
""",
                checks=[
                    code("однаковий seed — однаковий результат",
                         "assert pick([1, 2, 3], 42) == pick([1, 2, 3], 42)"),
                    code("елемент справді зі списку",
                         "assert pick([9], 3) == 9"),
                    code("перемішана копія теж передбачувана",
                         "assert shuffle_copy([1, 2, 3, 4, 5], 7) == "
                         "shuffle_copy([1, 2, 3, 4, 5], 7)"),
                    code("копія містить ті самі елементи",
                         "assert sorted(shuffle_copy([1, 2, 3, 4, 5], 1)) == [1, 2, 3, 4, 5]"),
                    code("початковий список не змінюється",
                         "data = [1, 2, 3, 4, 5]\n"
                         "shuffle_copy(data, 2)\n"
                         "assert data == [1, 2, 3, 4, 5], 'перемішуй копію, а не оригінал'"),
                ],
                hints=[
                    hint("де шукати", "random.seed(seed) ставиться ПЕРЕД випадковим "
                                      "вибором. random.choice(numbers) бере елемент."),
                    hint("копія списку", "copy = numbers[:]  — так роблять копію; "
                                         "далі random.shuffle(copy)."),
                    solution("""import random


def pick(numbers, seed):
    random.seed(seed)
    return random.choice(numbers)


def shuffle_copy(numbers, seed):
    copy = numbers[:]
    random.seed(seed)
    random.shuffle(copy)
    return copy"""),
                ],
            ),
            task(
                id="m2-datetime",
                title="Модуль datetime: дати без болю",
                level="Середньо",
                statement="""
                    <p>Дати — джерело половини багів у реальних проєктах. Модуль
                    <code>datetime</code> уміє перетворювати текст у дату й навпаки.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>days_between(first, second)</code> — скільки днів між
                        датами, заданими як <code>"2026-01-01"</code>;</li>
                        <li><code>human(text)</code> — перетворює
                        <code>"2026-09-24"</code> у <code>"24.09.2026"</code>.</li>
                    </ul>
                    <h4>Схема</h4>
                    <pre>datetime.strptime(text, "%Y-%m-%d").date()   # текст → дата
date.today().strftime("%d.%m.%Y")            # дата → текст</pre>
                    <p>Віднімання двох дат дає <code>timedelta</code>, у якого є
                    <code>.days</code>.</p>
                """,
                starter="""from datetime import date, datetime


def days_between(first, second):
    return 0


def human(text):
    return text
""",
                checks=[
                    code("рахує дні між датами",
                         "assert days_between('2026-01-01', '2026-01-10') == 9"),
                    code("працює в обидва боки",
                         "assert abs(days_between('2026-01-10', '2026-01-01')) == 9"),
                    code("одна дата — нуль днів",
                         "assert days_between('2026-05-05', '2026-05-05') == 0"),
                    code("форматує дату по-людськи",
                         "assert human('2026-09-24') == '24.09.2026'"),
                ],
                hints=[
                    hint("де шукати", "strptime перетворює текст у дату за шаблоном. "
                                      "Формат %Y-%m-%d — це «рік-місяць-день»."),
                    hint("різниця дат",
                         "datetime.strptime(second, '%Y-%m-%d') - "
                         "datetime.strptime(first, '%Y-%m-%d')  →  .days"),
                    solution("""from datetime import datetime


def _parse(text):
    return datetime.strptime(text, "%Y-%m-%d")


def days_between(first, second):
    return (_parse(second) - _parse(first)).days


def human(text):
    return _parse(text).strftime("%d.%m.%Y")"""),
                ],
            ),
        ),
        topic(
            "Тиждень 7 · Помилки та дебаг",
            task(
                id="m2-raise",
                title="raise: помилка з поясненням",
                level="Середньо",
                statement="""
                    <p>Кидати власні помилки — це не «зламати програму», а
                    <b>повідомити, що вхідні дані погані</b>. Клієнтський код тоді
                    вирішує, що робити.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>divide(a, b)</code> — ділення; якщо <code>b == 0</code>,
                        кидає <code>ValueError("Ділення на нуль")</code>;</li>
                        <li><code>parse_age(text)</code> — вік із тексту; якщо це не
                        число або вік не в межах 0–120, кидає
                        <code>ValueError("Некоректний вік")</code>.</li>
                    </ul>
                    <h4>Навіщо</h4>
                    <p>Без перевірки <code>int("двадцять")</code> впаде з незрозумілим
                    <code>ValueError</code> без контексту. З перевіркою — ти сам
                    пояснюєш, що саме не так.</p>
                """,
                starter="""def divide(a, b):
    return a / b


def parse_age(text):
    return int(text)
""",
                checks=[
                    code("звичайне ділення",
                         "assert divide(6, 3) == 2.0 and divide(5, 2) == 2.5"),
                    code("ділення на нуль дає своє повідомлення",
                         "\n".join([
                             "try:",
                             "    divide(1, 0)",
                             "except ValueError as error:",
                             "    assert 'Ділення на нуль' in str(error)",
                             "else:",
                             "    raise AssertionError('divide(1, 0) має кидати ValueError')",
                         ])),
                    code("читає коректний вік",
                         "assert parse_age('30') == 30 and parse_age('0') == 0"),
                    code("некоректний текст — помилка",
                         "\n".join([
                             "try:",
                             "    parse_age('двадцять')",
                             "except ValueError as error:",
                             "    assert 'Некоректний вік' in str(error)",
                             "else:",
                             "    raise AssertionError('текст замість числа має кидати ValueError')",
                         ])),
                    code("неможливий вік — помилка",
                         "\n".join([
                             "for wrong in ('-3', '500'):",
                             "    try:",
                             "        parse_age(wrong)",
                             "    except ValueError:",
                             "        pass",
                             "    else:",
                             "        raise AssertionError(f'вік {wrong} має бути відхилений')",
                         ])),
                ],
                hints=[
                    hint("де шукати", "Перевірка йде ПЕРЕД обчисленням: спершу дивимось, "
                                      "чи дані придатні, і лише потім рахуємо."),
                    hint("перевірка віку",
                         "age = int(text)\n"
                         "if not 0 <= age <= 120:\n"
                         '    raise ValueError("Некоректний вік")'),
                    solution('''def divide(a, b):
    if b == 0:
        raise ValueError("Ділення на нуль")
    return a / b


def parse_age(text):
    try:
        age = int(text)
    except ValueError:
        raise ValueError("Некоректний вік")
    if not 0 <= age <= 120:
        raise ValueError("Некоректний вік")
    return age'''),
                ],
            ),
            task(
                id="m2-debug",
                title="Знайди три баґи",
                level="Складно",
                minutes=15,
                statement="""
                    <p>Найважливіший навик джуна — <b>читати чужий код і знаходити,
                    чому він бреше</b>. У кожній із трьох функцій нижче рівно один
                    баґ. Код виглядає логічно — саме тому такі баґи й живуть у
                    проєктах роками.</p>
                    <h4>Що перевірять</h4>
                    <ul>
                        <li><code>average([2, 4, 6])</code> → <code>4</code>
                        (а не 5, як зараз);</li>
                        <li><code>biggest([-5, -2, -9])</code> → <code>-2</code>;</li>
                        <li><code>count_vowels("Аня і Олег")</code> → <code>5</code>
                        (великі літери теж голосні).</li>
                    </ul>
                    <h4>Підхід</h4>
                    <p>Не вгадуй — <b>перевір крайові випадки</b>: список з одного
                    елемента, усі від'ємні числа, великі літери. Саме там баґи й
                    вилазять.</p>
                """,
                starter="""def average(numbers):
    total = 0
    for index in range(1, len(numbers)):
        total += numbers[index]
    return total / len(numbers)


def biggest(numbers):
    best = 0
    for number in numbers:
        if number > best:
            best = number
    return best


def count_vowels(text):
    vowels = "аеиоуіюя"
    count = 0
    for letter in text:
        if letter in vowels:
            count += 1
    return count
""",
                checks=[
                    code("average рахує всі елементи",
                         "assert average([2, 4, 6]) == 4, 'перевір, звідки починається цикл'"),
                    code("average працює з одним елементом",
                         "assert average([10]) == 10"),
                    code("biggest працює з від'ємними",
                         "assert biggest([-5, -2, -9]) == -2, "
                         "'стартове значення не має бути нулем'"),
                    code("biggest на додатних",
                         "assert biggest([3, 7, 2]) == 7"),
                    code("count_vowels бачить великі літери",
                         "assert count_vowels('Аня і Олег') == 5, "
                         "'приведи текст до нижнього регістру'"),
                ],
                hints=[
                    hint("де шукати", "У кожній функції рівно один баґ, і жоден з них "
                                      "не про синтаксис. Дивись на початкові значення "
                                      "та межі діапазонів."),
                    hint("напрямок",
                         "average: скільки елементів реально додається? "
                         "biggest: а якщо всі числа менші за нуль? "
                         "count_vowels: а велика «А»?"),
                    solution('''def average(numbers):
    total = 0
    for index in range(len(numbers)):
        total += numbers[index]
    return total / len(numbers)


def biggest(numbers):
    best = numbers[0]
    for number in numbers:
        if number > best:
            best = number
    return best


def count_vowels(text):
    vowels = "аеиоуіюя"
    count = 0
    for letter in text.lower():
        if letter in vowels:
            count += 1
    return count'''),
                ],
            ),
        ),
        topic(
            "Тиждень 8 · Дані: JSON, CSV, SQL",
            task(
                id="m2-json",
                title="JSON: дані для зберігання й обміну",
                level="Середньо",
                statement="""
                    <p>JSON — універсальна мова даних: нею спілкуються сайти, боти й
                    бази. У Python словники й списки перетворюються в JSON і назад
                    без втрат.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>to_json(data)</code> — словник у текст JSON,
                        з <code>ensure_ascii=False</code> (щоб українські літери
                        лишались читабельними) і <code>sort_keys=True</code>
                        (щоб однакові дані давали однаковий текст);</li>
                        <li><code>from_json(text)</code> — текст назад у словник.</li>
                    </ul>
                    <h4>Приклад</h4>
                    <pre>to_json({"їжа": [120, 80]})  →  '{"їжа": [120, 80]}'
from_json('{"a": 1}')        →  {"a": 1}</pre>
                    <h4>Навіщо sort_keys</h4>
                    <p>Якщо порядок ключів стрибає, файли щоразу виглядають інакше —
                    і в Git з'являється шум замість справжніх змін.</p>
                """,
                starter="""import json


def to_json(data):
    return ""


def from_json(text):
    return {}
""",
                checks=[
                    code("читає JSON назад у словник",
                         "assert from_json('{\"a\": 1}') == {'a': 1}"),
                    code("вкладені структури не ламаються",
                         "text = to_json({'їжа': [120, 80]})\n"
                         "assert from_json(text) == {'їжа': [120, 80]}"),
                    code("українські літери лишаються читабельними",
                         "assert 'їжа' in to_json({'їжа': 120}), "
                         "'додай ensure_ascii=False'"),
                    code("порядок ключів стабільний",
                         "assert to_json({'b': 1, 'a': 2}) == to_json({'a': 2, 'b': 1}), "
                         "'додай sort_keys=True'"),
                    code("справжній JSON, а не схоже",
                         "assert json.loads(to_json({'x': [1, 2]})) == {'x': [1, 2]}"),
                ],
                hints=[
                    hint("де шукати", "json.dumps(data, ensure_ascii=False, sort_keys=True) "
                                      "і json.loads(text)."),
                    solution("""import json


def to_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def from_json(text):
    return json.loads(text)"""),
                ],
            ),
            task(
                id="m2-csv",
                title="CSV: таблиця, яку розуміє Excel",
                level="Середньо",
                statement="""
                    <p>CSV — це просто текст, де колонки розділені комами. Але якщо
                    розділити рядок вручну через <code>split(",")</code>, усе зламається
                    на значенні з комою всередині. Тому є модуль <code>csv</code>.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>save_rows(path, rows)</code> — записує список рядків
                        (кожен рядок — список клітинок) у CSV;</li>
                        <li><code>load_rows(path)</code> — читає файл назад у список
                        рядків.</li>
                    </ul>
                    <h4>Приклад</h4>
                    <pre>save_rows("e.csv", [["категорія", "сума"], ["їжа", "120"]])
load_rows("e.csv")  →  [["категорія", "сума"], ["їжа", "120"]]</pre>
                    <p class="warn">Відкривай файл із <code>newline=""</code> — інакше
                    на Windows у файл залізуть зайві порожні рядки.</p>
                """,
                starter="""import csv


def save_rows(path, rows):
    pass


def load_rows(path):
    return []
""",
                checks=[
                    code("записує й читає назад",
                         "\n".join([
                             "save_rows('rows.csv', [['категорія', 'сума'], ['їжа', '120']])",
                             "assert load_rows('rows.csv') == "
                             "[['категорія', 'сума'], ['їжа', '120']]",
                         ])),
                    code("у файлі справді кома між колонками",
                         "assert 'їжа,120' in open('rows.csv', encoding='utf-8').read(), "
                         "'використай модуль csv, а не ручний join'"),
                    code("порожній список не ламає",
                         "\n".join([
                             "save_rows('empty.csv', [])",
                             "assert load_rows('empty.csv') == []",
                         ])),
                    code("кома всередині значення не ламає рядок",
                         "\n".join([
                             "save_rows('quotes.csv', [['їжа, напої', '50']])",
                             "assert load_rows('quotes.csv') == [['їжа, напої', '50']], "
                             "'саме тому csv, а не split(\",\")'",
                         ])),
                ],
                hints=[
                    hint("де шукати", "csv.writer(handle).writerows(rows) і "
                                      "list(csv.reader(handle))."),
                    hint("відкриття файлу",
                         'with open(path, "w", encoding="utf-8", newline="") as handle:'),
                    solution('''import csv


def save_rows(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def load_rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))'''),
                ],
            ),
            task(
                id="m2-sql",
                title="SQL: перша база даних",
                level="Проєкт",
                minutes=25,
                statement="""
                    <p>Файли добре працюють, поки даних мало. Коли треба шукати,
                    фільтрувати й рахувати — потрібна база. SQLite вбудований у Python,
                    тож ти почнеш з SQL прямо тут.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>setup(conn)</code> — створює таблицю
                        <code>expenses (id, category, amount)</code>, якщо її ще немає;</li>
                        <li><code>add(conn, category, amount)</code> — додає витрату;</li>
                        <li><code>total(conn)</code> — сума всіх витрат;</li>
                        <li><code>by_category(conn)</code> — словник
                        <code>{категорія: сума}</code>;</li>
                        <li><code>top(conn)</code> — категорія з найбільшою сумою
                        або <code>None</code>, якщо таблиця порожня.</li>
                    </ul>
                    <h4>SQL, який знадобиться</h4>
                    <pre>CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    amount REAL NOT NULL
)
INSERT INTO expenses (category, amount) VALUES (?, ?)
SELECT SUM(amount) FROM expenses
SELECT category, SUM(amount) FROM expenses GROUP BY category
...</pre>
                    <p class="warn">Значення передавай через <code>?</code>, а не
                    склеюванням рядків: це захист від SQL-ін'єкцій, і саме так
                    роблять у реальному коді.</p>
                """,
                starter="""def setup(conn):
    pass


def add(conn, category, amount):
    pass


def total(conn):
    return 0


def by_category(conn):
    return {}


def top(conn):
    return None
""",
                checks=[
                    code("таблиця створюється",
                         "\n".join([
                             "import sqlite3",
                             "first = sqlite3.connect(':memory:')",
                             "setup(first)",
                             "add(first, 'їжа', 120)",
                             "assert total(first) == 120",
                         ])),
                    code("setup можна викликати двічі",
                         "\n".join([
                             "import sqlite3",
                             "second = sqlite3.connect(':memory:')",
                             "setup(second)",
                             "setup(second)",
                             "add(second, 'таксі', 50)",
                             "assert total(second) == 50",
                         ])),
                    code("сума по категоріях",
                         "\n".join([
                             "import sqlite3",
                             "third = sqlite3.connect(':memory:')",
                             "setup(third)",
                             "add(third, 'їжа', 100)",
                             "add(third, 'їжа', 50)",
                             "add(third, 'таксі', 25)",
                             "assert by_category(third) == {'їжа': 150.0, 'таксі': 25.0}",
                         ])),
                    code("найдорожча категорія",
                         "\n".join([
                             "import sqlite3",
                             "fourth = sqlite3.connect(':memory:')",
                             "setup(fourth)",
                             "add(fourth, 'їжа', 100)",
                             "add(fourth, 'таксі', 250)",
                             "assert top(fourth) == 'таксі'",
                         ])),
                    code("порожня таблиця не ламає",
                         "\n".join([
                             "import sqlite3",
                             "fifth = sqlite3.connect(':memory:')",
                             "setup(fifth)",
                             "assert total(fifth) == 0",
                             "assert top(fifth) is None",
                         ])),
                ],
                hints=[
                    hint("де шукати", "conn.execute('INSERT INTO expenses (category, "
                                      "amount) VALUES (?, ?)', (category, amount)), "
                                      "а після змін — conn.commit()."),
                    hint("GROUP BY",
                         "rows = conn.execute('SELECT category, SUM(amount) FROM "
                         "expenses GROUP BY category')\n"
                         "return {category: sum_ for category, sum_ in rows}"),
                    solution("""def setup(conn):
    conn.execute(
        \"\"\"
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL
        )
        \"\"\"
    )
    conn.commit()


def add(conn, category, amount):
    conn.execute(
        "INSERT INTO expenses (category, amount) VALUES (?, ?)",
        (category, amount),
    )
    conn.commit()


def total(conn):
    row = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()
    return row[0] or 0


def by_category(conn):
    rows = conn.execute(
        "SELECT category, SUM(amount) FROM expenses GROUP BY category"
    )
    return {category: sum_ for category, sum_ in rows}


def top(conn):
    row = conn.execute(
        "SELECT category, SUM(amount) FROM expenses "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1"
    ).fetchone()
    return row[0] if row else None"""),
                ],
            ),
        ),
        topic(
            "Тиждень 9 · Код, який легко читати",
            task(
                id="m2-comprehensions",
                title="Comprehensions: цикл в один рядок",
                level="Середньо",
                statement="""
                    <p>Три рядки «порожній список → цикл → append» Python уміє
                    записати одним виразом:</p>
                    <pre>evens = [number for number in numbers if number % 2 == 0]</pre>
                    <p>Читається як речення: «число — для кожного числа зі списку —
                    якщо воно парне».</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>squares(n)</code> → <code>[1, 4, 9]</code> для 3;</li>
                        <li><code>evens(numbers)</code> → лише парні;</li>
                        <li><code>prices_with_vat(prices)</code> → ціни з ПДВ 20%,
                        округлені до копійок;</li>
                        <li><code>long_names(names, limit)</code> → імена довші за
                        <code>limit</code>.</li>
                    </ul>
                    <h4>Важливо</h4>
                    <p>Пиши comprehension лише тоді, коли вираз уміщається в голову
                    одним реченням. Три вкладені цикли «в один рядок» — це вже
                    шкідливо.</p>
                """,
                starter="""def squares(n):
    return []


def evens(numbers):
    return []


def prices_with_vat(prices):
    return []


def long_names(names, limit):
    return []
""",
                checks=[
                    code("squares", "assert squares(3) == [1, 4, 9] and squares(0) == []"),
                    code("evens", "assert evens([1, 2, 3, 4]) == [2, 4] and evens([]) == []"),
                    code("ціни з ПДВ", "assert prices_with_vat([100, 50]) == [120.0, 60.0]"),
                    code("ПДВ округлюється",
                         "assert prices_with_vat([99.99]) == [119.99]"),
                    code("довгі імена",
                         "assert long_names(['Аня', 'Олександр', 'Київ'], 3) == "
                         "['Олександр', 'Київ']"),
                ],
                hints=[
                    hint("де шукати", "Форма така: [що_зробити for елемент in колекція "
                                      "if умова]. Умова не обов'язкова."),
                    hint("ПДВ", "prices_with_vat: у дужках має бути round(price * 1.2, 2)."),
                    solution("""def squares(n):
    return [number ** 2 for number in range(1, n + 1)]


def evens(numbers):
    return [number for number in numbers if number % 2 == 0]


def prices_with_vat(prices):
    return [round(price * 1.2, 2) for price in prices]


def long_names(names, limit):
    return [name for name in names if len(name) > limit]"""),
                ],
            ),
            task(
                id="m2-typing",
                title="Анотації типів: код, який пояснює себе",
                level="Легко",
                statement="""
                    <p>Анотації типів не змінюють роботу програми — вони для
                    <b>людей і редактора</b>. Редактор починає підказувати методи,
                    а той, хто читає код, одразу розуміє, що приходить і що
                    повертається.</p>
                    <h4>Що треба зробити</h4>
                    <p>Підпиши типи (поведінка функцій теж перевіряється):</p>
                    <ul>
                        <li><code>greet(name: str) -&gt; str</code>
                        → <code>"Привіт, Аня!"</code>;</li>
                        <li><code>average(numbers: list[float]) -&gt; float</code>
                        → середнє, для порожнього списку <code>0.0</code>;</li>
                        <li><code>find(rows: dict[str, int], key: str) -&gt; int | None</code>
                        → значення або <code>None</code>.</li>
                    </ul>
                    <pre>def greet(name: str) -&gt; str:
    return f"Привіт, {name}!"</pre>
                    <p class="warn">Це не перевірка типів під час виконання: якщо
                    передати число туди, де очікується рядок, помилки не буде.
                    Анотації — це документація, а не охоронець.</p>
                """,
                starter='''def greet(name):
    return f"Привіт, {name}!"


def average(numbers):
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def find(rows, key):
    return rows.get(key)
''',
                checks=[
                    code("greet підписана й працює",
                         "assert greet.__annotations__ == {'name': str, 'return': str}, "
                         "'додай анотації до greet'\n"
                         "assert greet('Аня') == 'Привіт, Аня!'"),
                    code("average підписана й працює",
                         "annotations = average.__annotations__\n"
                         "assert annotations.get('return') is float\n"
                         "assert 'numbers' in annotations\n"
                         "assert average([2, 4]) == 3.0 and average([]) == 0.0"),
                    code("find підписана й працює",
                         "assert find.__annotations__.get('return') == int | None, \\\n"
                         "    'return має бути int | None'\n"
                         "assert find({'а': 1}, 'а') == 1 and find({'а': 1}, 'б') is None"),
                ],
                hints=[
                    hint("де шукати", "Анотації пишуть прямо в рядку з def: "
                                      "name: str — тип аргументу, -> str — тип результату."),
                    hint("int | None", "Знак | означає «або»: повертає або int, "
                                       "або None."),
                    solution('''def greet(name: str) -> str:
    return f"Привіт, {name}!"


def average(numbers: list[float]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def find(rows: dict[str, int], key: str) -> int | None:
    return rows.get(key)'''),
                ],
            ),
        ),
        topic(
            "Практика поза тренажером",
            stub("m2-venv", "venv і pip: своє оточення (у тебе вже працює!)"),
            stub("m2-git", "Git: перший коміт у своєму проєкті"),
            stub("m2-pytest", "Перші тести з pytest"),
            stub("m2-modules", "Свій модуль: розбити код на файли"),
            stub("m2-codewars", "Codewars: 2–3 задачі рівня 8–7 kyu щодня"),
        ),
    ),
)
