"""Міні-довідка: короткі шпаргалки, які підсвічуються прямо під час задачі.

Ідея проста: людина не має тримати в голові весь синтаксис. Коли відкривається
задача про словники — поруч з'являється шпаргалка про словники, і не треба
перемикатись у браузер.

Тіла шпаргалок навмисно зберігаються **звичайним текстом** (не HTML): так їх
легко читати й правити в цьому файлі, а форматування робить інтерфейс
(див. trainer/ui/task_panel.py, plain_to_html).

Важливе правило для тексту: панель довідки вузька (~46 символів у рядку коду),
тому **не робимо вирівняних колонок** — довгі пояснення виносимо окремим
рядком, який стане абзацом. Інакше рядки ламаються посеред слова.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CheatSheet:
    """Одна шпаргалка: ключ, заголовок, текст і слова для автопідбору."""

    key: str
    title: str
    body: str
    keywords: tuple[str, ...] = ()


# Порядок має значення: перша шпаргалка — це «база», яку отримує будь-яка
# задача, якщо для неї не знайшлося кращого збігу.
SHEETS: tuple[CheatSheet, ...] = (
    CheatSheet(
        key="basics",
        title="Основи: вивід, ввід, типи",
        keywords=("вивід", "знайомство", "основи", "print()", "змінн"),
        body="""\
Надрукувати текст:
print("Привіт, світ!")
print("Сума:", 2 + 3)
print(f"Привіт, {name}!")

Запитати в людини:
name = input("Як тебе звати? ")

input() завжди повертає рядок. Перетвори його:
age = int(input("Скільки тобі років? "))
price = float(input("Ціна: "))
text = str(42)

Базові типи:
int      7           ціле число
float    7.5         дробове
str      "7.5"       рядок
bool     True        так або ні
list     [1, 2, 3]   список
dict     {"a": 1}    словник

Дрібнички:
len("щось")       скільки символів
type(7)           якого типу значення
round(3.1415, 2)  3.14
abs(-5)           5
max(1, 7, 3)      7
min(1, 7, 3)      1
sum([1, 2, 3])    6

Коментар — це те, що Python ігнорує:
# пояснення для себе

У тренажері ввід подається автоматично, тому input()
не чекає на клавіатуру.""",
    ),
    CheatSheet(
        key="strings",
        title="Рядки (str)",
        keywords=("рядк", "послід", "текст", "f-string"),
        body="""\
Рядок можна різати, як торт — це зріз:
text = "Привіт, світ"
text[0]     "П"      перший символ
text[-1]    "т"      останній
text[:6]    "Привіт" з початку до 6 (6 не входить)
text[8:]    "світ"   від 8 до кінця
text[::-1]           перевернути рядок

Методи:
text.lower()                 маленькими літерами
text.upper()                 ВЕЛИКИМИ
text.strip()                 прибрати пробіли з країв
text.split(",")              порізати у список
", ".join(words)             зібрати список у рядок
text.replace("і", "и")       замінити
text.startswith("При")       починається з…
text.endswith("віт")         закінчується на…
text.find("світ")            позиція або -1
text.count("і")              скільки разів
"світ" in text               чи є підрядок

Порівнювати можна з ==, але регістр важить:
"Привіт" == "привіт"       → False
"Привіт".lower() == "привіт".lower()   → True

Порахувати літери без пробілів:
letters = [ch for ch in text if ch != " "]
len(letters)""",
    ),
    CheatSheet(
        key="numbers",
        title="Числа й арифметика",
        keywords=("арифмет", "числ", "матем", "математик", "калькул", "відсот"),
        body="""\
7 + 3      10
7 - 3      4
7 * 3      21
7 / 3      2.3333333333333335   завжди float
7 // 3     2                    ціле ділення
7 % 3      1                    остача
7 ** 2     49                   степінь

Два знаки після коми:
f"{price:.2f}"      → "12.35" (рядок)
round(price, 2)     → 12.35 (число)

Відсотки — це просто множення:
price = 100
price * 1.2      додати 20%
price * 0.85     знижка 15%
price / 100      один відсоток

Перевірка на парність — через остачу:
number % 2 == 0      парне
number % 2 != 0      непарне""",
    ),
    CheatSheet(
        key="conditions",
        title="Умови: if / elif / else",
        keywords=("умов", "if", "розгалуж", "порівнян", "логік"),
        body="""\
if score >= 90:
    print("Відмінно")
elif score >= 60:
    print("Зараховано")
else:
    print("Спробуй ще")

Порівняння:
==   дорівнює         !=   не дорівнює
>    більше           <    менше
>=   більше-рівне     <=   менше-рівне

Логіка:
and   і те, і те:   age > 18 and has_passport
or    або:          day == "сб" or day == "нд"
not   заперечення:  not finished

Відступ у 4 пробіли — це частина синтаксису.
Після if завжди стоїть двокрапка.

Короткий запис (тернарний оператор):
status = "дорослий" if age >= 18 else "дитина"

Перевірка «чи є значення»:
if name:            порожній рядок і None — хибні
if not items:       список порожній
if value is None:   саме None, а не 0 і не "" """,
    ),
    CheatSheet(
        key="loops",
        title="Цикли: for і while",
        keywords=("цикл", "повторен", "while", "range", "for"),
        body="""\
for — коли знаєш, скільки разів або по чому йти:
for fruit in ["яблуко", "груша"]:
    print(fruit)

for number in range(5):        0 1 2 3 4
for number in range(1, 6):     1 2 3 4 5
for number in range(0, 10, 2): 0 2 4 6 8

Нумерація з одиниці — візьми enumerate:
for index, fruit in enumerate(fruits, start=1):
    print(index, fruit)

І ключ, і значення словника:
for key, value in prices.items():
    print(key, "коштує", value)

while — поки умова істинна:
guess = 0
while guess != secret:
    guess = int(input("Вгадай: "))

Обов'язково перевір, чи змінна всередині справді
змінюється — інакше цикл ніколи не завершиться.

Керування циклом:
break       вийти з циклу
continue    перейти до наступного кроку
else        виконається, якщо не було break""",
    ),
    CheatSheet(
        key="lists",
        title="Списки (list) і кортежі",
        keywords=("список", "list", "массив", "масив", "comprehension", "генератор"),
        body="""\
items = [3, 1, 2]
items.append(4)          додати в кінець
items.insert(0, 9)       вставити на позицію
items.remove(1)          прибрати перше таке
items.pop()              забрати останній
items.pop(0)             забрати за індексом
items.sort()             відсортувати (змінює)
items.sort(reverse=True) від більшого до меншого
sorted(items)            те саме, але НОВИЙ список
items.reverse()          перевернути на місці
items.index(3)           індекс першого входження
items.count(3)           скільки разів
items.extend([7, 8])     додати кілька
len(items)               довжина
3 in items               чи є елемент

Корисне без циклів:
sum(numbers)
min(numbers), max(numbers)
any(x > 10 for x in numbers)   хоч один True
all(x > 0 for x in numbers)    усі True

Генератор списку коротший за цикл:
squares = [x * x for x in range(5)]
evens = [x for x in numbers if x % 2 == 0]
words = [w.strip().lower() for w in raw]

Копія списку:
copy = items[:]
copy = list(items)

Кортеж — незмінний список:
point = (10, 20)
x, y = point             розпакування""",
    ),
    CheatSheet(
        key="dicts",
        title="Словники (dict) і множини (set)",
        keywords=("словник", "dict", "json-об'єкт", "множин", "set", "підрахун", "count"),
        body="""\
prices = {"яблуко": 15, "груша": 22}
prices["банан"] = 30        додати або змінити
prices.get("ківі")          None, якщо немає
prices.get("ківі", 0)       0, якщо немає
"яблуко" in prices          чи є такий ключ
prices.keys()               усі ключі
prices.values()             усі значення
prices.items()              пари ключ і значення
del prices["яблуко"]        видалити ключ
prices.pop("груша", None)   видалити й повернути
len(prices)                 скільки ключів

Підрахунок — найчастіша задача на словники:
counts = {}
for letter in "банана":
    counts[letter] = counts.get(letter, 0) + 1
# {'б': 1, 'а': 3, 'н': 2}

Словник із двох списків:
codes = dict(zip(names, values))

Генератор словника:
squares = {x: x * x for x in range(4)}

Множина (set) — унікальні значення, дуже швидка:
unique = set([1, 2, 2, 3])    → {1, 2, 3}
unique.add(4)
a & b      спільні елементи
a | b      об'єднання

Чи всі слова різні:
len(set(words)) == len(words)

Топ-N після підрахунку:
top = sorted(counts.items(),
             key=lambda pair: pair[1],
             reverse=True)""",
    ),
    CheatSheet(
        key="functions",
        title="Функції, область видимості",
        keywords=("функц", "def", "аргумент", "параметр", "return"),
        body="""\
def greet(name):
    return f"Привіт, {name}!"

message = greet("Аня")

Що повертає функція — те й отримуєш.
Без return повертається None, і це найчастіша причина
помилок «TypeError: can only concatenate str not NoneType».

Значення за замовчуванням:
def greet(name, greeting="Привіт"):
    return f"{greeting}, {name}!"

greet("Аня")                    "Привіт, Аня!"
greet("Аня", "Вітаю")           "Вітаю, Аня!"

Скільки завгодно аргументів:
def total(*numbers):
    return sum(numbers)

Область видимості: змінна всередині функції не видна
зовні. Для зміни зовнішньої є global, але краще так не
робити — передавай значення параметром.

Документація:
def area(width, height):
    \"\"\"Повертає площу прямокутника.\"\"\"
    return width * height""",
    ),
    CheatSheet(
        key="classes",
        title="Класи й об'єкти",
        keywords=("клас", "class", "об'єкт", "метод", "__init__", "self"),
        body="""\
class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Сума має бути додатною")
        self.balance += amount
        return self.balance

    def __str__(self):
        return f"{self.owner}: {self.balance} грн"


account = Account("Аня", 100)
account.deposit(50)
print(account)          викличе __str__

self — це «сам об'єкт». Через self методи бачать дані
свого об'єкта, а не чужого.

__init__ викликається автоматично при створенні об'єкта.

Помилку можна підняти самому:
raise ValueError("Недостатньо коштів")
raise TypeError("Очікувався рядок")

Наслідування, коли два класи схожі:
class Savings(Account):
    def __init__(self, owner, balance, rate):
        super().__init__(owner, balance)
        self.rate = rate""",
    ),
    CheatSheet(
        key="exceptions",
        title="Помилки та try / except",
        keywords=("помилк", "винят", "try", "except", "raise", "баґ", "баг"),
        body="""\
try:
    number = int(text)
except ValueError:
    print("Це не число")
except (TypeError, KeyError) as error:
    print("Щось пішло не так:", error)
except Exception as error:      ловить усе інше
    print("Невідома помилка:", error)
else:
    print("Помилки не було")
finally:
    print("Виконається завжди")

Найчастіші помилки:
NameError          ім'я не знайдене
TypeError          несумісні типи
ValueError         тип ок, значення ні
IndentationError   поламані відступи
SyntaxError        Python не читає код
KeyError           немає такого ключа
IndexError         індекс за межами
ZeroDivisionError  ділення на нуль
AttributeError     немає такого методу
UnboundLocalError  змінна ще не створена
RecursionError     функція без зупинки

Що робити з кожною:
NameError — друкарська помилка або забув лапки навколо
тексту (name = "Аня", а не name = Аня).

TypeError — змішав рядок із числом: перетвори int(),
float(), str(). Часто винен забутий return (тоді
виходить None).

ValueError — int("abc") або розпакування не тієї
кількості значень.

IndentationError — відступ рівно 4 пробіли, не мішай
табуляцію з пробілами.

KeyError — користуйся .get(key) замість [key].
IndexError — перевір len(), для останнього є [-1].
ZeroDivisionError — перевір знаменник до ділення,
особливо len() порожнього списку.

Як читати traceback:
1. Останній рядок — тип помилки й коротке пояснення.
2. Вище — номер рядка у твоєму файлі: саме там усе почалося.
3. Виправляй причину, а не місце, де воно гучно впало.""",
    ),
    CheatSheet(
        key="files",
        title="Файли: читання й запис",
        keywords=("файл", "file", "open", "читання"),
        body="""\
with open("data.txt", encoding="utf-8") as file:
    text = file.read()          весь файл
    lines = file.readlines()    список рядків

with open("data.txt", encoding="utf-8") as file:
    for line in file:           читаємо по рядку
        print(line.strip())

Запис:
with open("out.txt", "w", encoding="utf-8") as file:
    file.write("Привіт\\n")
    file.writelines(["один\\n", "два\\n"])

Режими:
"r"   читати (файл мусить існувати)
"w"   писати (СТАРИЙ ВМІСТ ЗНИКАЄ)
"a"   дописати в кінець

encoding="utf-8" обов'язковий, якщо в тексті є
українські літери.

Файл у папці поруч із програмою:
from pathlib import Path
folder = Path(__file__).parent
text = (folder / "data.txt").read_text(encoding="utf-8")

Чи існує файл:
Path("data.txt").exists()

`with` закриває файл сам, навіть якщо станеться помилка —
тому пиши саме так, а не file = open(...).

Рядки з файлу мають зайвий \\n — прибирай .strip().""",
    ),
    CheatSheet(
        key="json",
        title="JSON: обмін даними",
        keywords=("json", "api", "словник даних"),
        body="""\
import json

Рядок → Python-об'єкт:
data = json.loads('{"name": "Аня", "age": 20}')
data["name"]        "Аня"

Python-об'єкт → рядок:
text = json.dumps({"city": "Київ"},
                  ensure_ascii=False)

Файл:
with open("data.json", encoding="utf-8") as file:
    data = json.load(file)

with open("out.json", "w", encoding="utf-8") as file:
    json.dump(data, file,
              ensure_ascii=False, indent=2)

Відповідність типів:
JSON object  →  dict
JSON array   →  list
string       →  str
number       →  int / float
true/false   →  True / False
null         →  None

ensure_ascii=False потрібен, щоб «Київ» був літерами,
а не \\u041a\\u0438… 

У JSON лапки тільки подвійні, і немає коми після
останнього елемента — інакше JSONDecodeError.

Типові ключі у відповідях: "name", "value", "rate",
"items". Безпечний доступ: data.get("items", [])""",
    ),
    CheatSheet(
        key="csv",
        title="CSV: таблиці у файлі",
        keywords=("csv", "таблич", "експорт"),
        body="""\
import csv

Читання списком:
with open("prices.csv", encoding="utf-8",
          newline="") as file:
    rows = list(csv.reader(file))
# rows[0] — заголовки, далі по рядку

Читання як словники (зручніше):
with open("prices.csv", encoding="utf-8",
          newline="") as file:
    for row in csv.DictReader(file):
        print(row["name"], row["price"])

Запис:
with open("out.csv", "w", encoding="utf-8",
          newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["назва", "ціна"])
    writer.writerow(["яблуко", 15])

Запис словників:
    writer = csv.DictWriter(file,
                            fieldnames=["name", "price"])
    writer.writeheader()
    writer.writerow({"name": "яблуко", "price": 15})

newline="" — щоб на Windows не з'являлись порожні рядки.
Числа з CSV теж приходять рядками: int(row["price"])

Інший розділювач:
csv.reader(file, delimiter=";")""",
    ),
    CheatSheet(
        key="sqlite",
        title="SQLite: база даних із нуля",
        keywords=("sql", "sqlite", "база", "таблич", "select"),
        body="""\
import sqlite3

connect = sqlite3.connect("shop.db")
cursor = connect.cursor()

Створення таблиці:
cursor.execute(
    "CREATE TABLE IF NOT EXISTS products ("
    "    id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "    name TEXT NOT NULL, "
    "    price REAL"
    ")"
)

Додавання — параметри через ?, НЕ через f-рядок:
cursor.execute(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    ("яблуко", 15.5),
)
connect.commit()      без commit зміни не збережуться

Читання:
cursor.execute("SELECT name, price FROM products")
for name, price in cursor:
    print(name, price)

cursor.execute("SELECT COUNT(*) FROM products")
count = cursor.fetchone()[0]

З умовою:
cursor.execute(
    "SELECT name FROM products WHERE price > ?",
    (10,),
)
one = cursor.fetchone()      один рядок або None
all_rows = cursor.fetchall() усі рядки

Оновлення і видалення:
cursor.execute("UPDATE products SET price = ? WHERE name = ?",
               (20, "яблуко"))
cursor.execute("DELETE FROM products WHERE id = ?", (3,))
connect.commit()

Наприкінці: connect.close()

Чому ? замість f-рядка: параметри захищають від
SQL-ін'єкції та лапок усередині даних.""",
    ),
    CheatSheet(
        key="typing",
        title="Анотації типів",
        keywords=("анотац", "типізац", "typing", "mypy"),
        body="""\
Анотації — підказки для людей і редактора. Python їх не
перевіряє сам, але код стає зрозумілішим, а автодоповнення
в редакторі — розумнішим.

def average(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers)


def greet(name: str, excited: bool = False) -> str:
    ending = "!" if excited else "."
    return f"Привіт, {name}{ending}"


def find_user(user_id: int) -> dict | None:
    ...            # може повернути словник або None

Позначення:
int, float, str, bool        прості типи
list[int]                    список цілих
dict[str, float]             словник рядок → число
tuple[int, str]              кортеж фіксованої форми
set[str]                     множина рядків
str | None                   рядок або None
list[str] | None             список або None
Any                          будь-що (краще уникати)

Змінні теж можна анотувати:
count: int = 0
names: list[str] = []

Перевірити анотації у себе в коді:
print(average.__annotations__)
# {'numbers': list[float], 'return': float}

Перевірка типів (не обов'язково):
python -m pip install mypy
python -m mypy solution.py""",
    ),
    CheatSheet(
        key="algorithms",
        title="Алгоритми: складність, пошук, прийоми",
        keywords=("алгоритм", "складніст", "сортування", "пошук", "leetcode", "codewars"),
        body="""\
Складність — це «як швидко росте робота разом із даними».

O(1)        одна дія незалежно від розміру
            dict[key], set, len()
O(log n)    ділення навпіл — бінарний пошук
O(n)        один прохід по даних
O(n log n)  нормальне сортування, sorted()
O(n²)       вкладений цикл по тих самих даних

O(n²) на 100 000 елементів — це ~10^10 дій.
Вкладені цикли на великих даних майже завжди
переписують на словник або множину.

Бінарний пошук (список УЖЕ відсортований):
low, high = 0, len(items) - 1
while low <= high:
    middle = (low + high) // 2
    if items[middle] == target:
        ...
    elif items[middle] < target:
        low = middle + 1
    else:
        high = middle - 1

Готовий бінарний пошук:
from bisect import bisect_left
index = bisect_left(sorted_items, target)

Прийоми, які вирішують більшість задач:

1. Словник «те, що вже бачив» — прибирає вкладений цикл.
   Потрібна сума двох чисел: кладемо в dict доповнення.

2. Множина для перевірки унікальності:
   has_duplicate = len(set(items)) != len(items)

3. Два вказівники (зліва й справа) — паліндроми,
   перевертання, пари.

4. Накопичувальний максимум (Kadane) — максимальна сума
   неперервного шматка:
   best = current = items[0]
   for value in items[1:]:
       current = max(value, current + value)
       best = max(best, current)

5. Стек (звичайний список) — дужки, вкладені структури:
   stack.append(x) / stack.pop() / if not stack

Перед кодом випиши 3 приклади руками: на папері алгоритм
знаходиться за 2 хвилини, а «біля клавіатури» — за 20.""",
    ),
    CheatSheet(
        key="modules",
        title="Модулі, імпорти, свій проєкт із кількох файлів",
        keywords=("модул", "імпорт", "import", "файли проєкту", "utils"),
        body="""\
import math
print(math.sqrt(16))        4.0
math.pi                     3.141592653589793

from datetime import datetime, timedelta
now = datetime.now()
yesterday = now - timedelta(days=1)

import random
random.seed(42)             фіксує випадковість
random.randint(1, 6)        число від 1 до 6 включно
random.choice(["а", "б"])   випадковий елемент
random.shuffle(items)       перемішати список (змінює)

Свої файли в одній папці імпортуються за іменем:

utils.py:
    def double(x):
        return x * 2

solution.py:
    from utils import double
    print(double(21))       → 42
    # або: import utils → utils.double(21)

Імпорт має бути на початку файлу. Файл у тій самій папці
доступний без розширення .py.

Щоб код працював і як модуль, і як програма:
if __name__ == "__main__":
    main()""",
    ),
    CheatSheet(
        key="venv",
        title="Віртуальне оточення, pip, Git, проєкт",
        keywords=("venv", "оточенн", "pip", "залежност", "термінал", "git",
                  "коміт", "гілк", "github", "requirements", "pytest"),
        body="""\
Віртуальне оточення — окрема «кімната» для залежностей
одного проєкту, щоб версії бібліотек не сварились.

Windows:
python -m venv .venv
.venv\\Scripts\\activate

Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

Встановлення бібліотек:
python -m pip install requests
python -m pip freeze > requirements.txt
python -m pip install -r requirements.txt

Викликай pip через python -m pip — тоді точно встановиш
у потрібне оточення, а не в системний Python.

Git — мінімум для співбесіди:
git init
git status
git add main.py
git commit -m "Перший коміт"
git branch -M main
git remote add origin <адреса>
git push -u origin main

Нові гілки:
git checkout -b feature/parser
... працюєш ...
git checkout main
git merge feature/parser

Тести:
python -m pip install pytest
pytest -q            запускає всі test_*.py""",
    ),
)


def all_sheets() -> tuple[CheatSheet, ...]:
    return SHEETS


def get(key: str) -> CheatSheet | None:
    """Шпаргалка за ключем (None, якщо такого ключа немає)."""
    for sheet in SHEETS:
        if sheet.key == key:
            return sheet
    return None


def _best(haystack: str) -> CheatSheet | None:
    """Шпаргалка з найбільшою кількістю ключових слів у тексті."""
    haystack = haystack.lower()
    best, best_score = None, 0
    for sheet in SHEETS:
        score = sum(1 for word in sheet.keywords if word in haystack)
        if score > best_score:
            best, best_score = sheet, score
    return best


def pick(task) -> CheatSheet:
    """Підбирає шпаргалку для задачі.

    Спочатку — явний ключ у самій задачі, потім — пошук за словами в назві
    теми й задачі. Якщо нічого не збіглось, віддаємо «Основи»: краще
    показати базову шпаргалку, ніж порожню вкладку.
    """
    explicit = get(getattr(task, "cheatsheet", "") or "")
    if explicit is not None:
        return explicit

    title = f"{getattr(task, 'title', '')}"
    haystack = title
    try:                       # тема задачі — найсильніший сигнал
        from . import topic_of

        haystack = f"{topic_of(task.id)} {title}"
    except Exception:          # pragma: no cover — підбір не має ламати вікно
        pass

    return _best(haystack) or get("basics") or SHEETS[0]


def pick_text(text: str) -> CheatSheet:
    """Підбір за довільним текстом — для пунктів плану без задачі."""
    return _best(text) or get("basics") or SHEETS[0]


__all__ = ["CheatSheet", "all_sheets", "get", "pick", "pick_text"]
