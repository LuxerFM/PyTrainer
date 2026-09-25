"""Місяць 1 — база Python: змінні, умови, цикли, функції, списки, словники, файли.

Кожна задача має заготовку коду, приховані перевірки та підказки. Розв'язки
перевіряє tests/test_curriculum.py — тому код у підказці `solution(...)`
завжди робочий.

Після кожного тижня теорії йде тема з дрилами (див. drills1.py): короткі
вправи, які й дають ту саму навичку на різних даних.
"""

from .drills1 import WEEK1_DRILLS, WEEK2_DRILLS, WEEK3_DRILLS, WEEK4_DRILLS
from .schema import Month, code, hint, solution, stdout, task, topic

MONTH = Month(
    title="Місяць 1 · База, частина 1",
    subtitle="Код пишемо руками, без ШІ",
    topics=(
        topic(
            "Тиждень 1 · Старт і змінні",
            task(
                id="w1-hello",
                title="Перший вивід: print()",
                level="Легко",
                statement="""
                    <p>Будь-яка програма починається з виводу на екран. За це
                    відповідає функція <code>print()</code>.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>виведи рядок <code>Привіт, світ!</code></li>
                        <li>наступним рядком — привітання зі своїм ім'ям</li>
                    </ul>
                    <h4>Синтаксис</h4>
                    <pre>print("текст у лапках")</pre>
                    <p class="warn">Лапки обов'язкові: без них Python вирішить,
                    що це ім'я змінної, і впаде з помилкою NameError.</p>
                """,
                starter='# Виведи два рядки: привітання і своє ім\'я\n',
                checks=[
                    stdout("виводить «Привіт, світ!»", contains="Привіт, світ!"),
                    stdout("друкує ще один рядок", lines=2),
                ],
                hints=[
                    hint("де шукати", "Тобі потрібна функція print(). Кожен виклик "
                                      "print() — це один рядок на екрані."),
                    hint("яка конструкція", "Два виклики поспіль дадуть два рядки:\n"
                                             'print("перший")\nprint("другий")'),
                    solution('print("Привіт, світ!")\nprint("Мене звати Аня")'),
                ],
            ),
            task(
                id="w1-vars",
                title="Змінні та f-рядки",
                level="Легко",
                statement="""
                    <p>Змінна — це іменована комірка пам'яті: <code>name = "Аня"</code>.
                    А f-рядок дозволяє вставити змінну прямо в текст.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>впиши у змінні <code>name</code>, <code>age</code>, <code>city</code>
                        свої дані (вік — числом, без лапок);</li>
                        <li>виведи <b>одним рядком</b>:
                        <code>Мене звати Аня, мені 20 років, я з Києва</code>
                        (замість Аня/20/Києва — твої значення);</li>
                        <li>використай f-рядок: <code>f"текст {змінна}"</code>.</li>
                    </ul>
                    <p class="warn">Якщо забути літеру f, дужки надрукуються як текст.</p>
                """,
                starter='''name = "ЗАМІНИ_МЕНЕ"
age = 0
city = "ЗАМІНИ_МЕНЕ"

# Виведи одним рядком: Мене звати <ім'я>, мені <вік> років, я з <місто>
''',
                checks=[
                    code("age — число, і воно твоє",
                         'assert isinstance(age, int) and age > 0, "постав у age свій вік числом"'),
                    code("name і city заповнені",
                         'assert "ЗАМІНИ_МЕНЕ" not in (name, city), "заповни name і city"'),
                    stdout("усе в одному рядку", lines=1, contains="Мене звати"),
                    stdout("підставляє значення змінних", contains="років, я з"),
                ],
                hints=[
                    hint("де шукати", "f-рядок — це звичайний рядок, перед лапками якого "
                                      "стоїть літера f. Значення змінних підставляються "
                                      "у фігурних дужках."),
                    hint("яка конструкція",
                         'print(f"Мене звати {name}, мені {age} років, я з {city}")'),
                    solution('''name = "Аня"
age = 20
city = "Київ"

print(f"Мене звати {name}, мені {age} років, я з {city}")'''),
                ],
            ),
            task(
                id="w1-input",
                title="input(): програма, що питає",
                level="Легко",
                stdin="Аня\n",
                statement="""
                    <p>Функція <code>input()</code> зупиняє програму й чекає, поки
                    користувач щось напише. Те, що він написав, потрапляє у змінну.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>запитай ім'я: <code>input("Як тебе звати? ")</code>;</li>
                        <li>виведи привітання у форматі <code>Привіт, Аня!</code>.</li>
                    </ul>
                    <h4>Важливо</h4>
                    <p>У тренажері немає клавіатури — ввід підставляється автоматично.
                    Натисни «Запустити», щоб побачити, який саме ввід подано.</p>
                """,
                starter='''name = "?"

# 1. Заміни "?" на input("Як тебе звати? ")
# 2. Виведи: Привіт, <ім'я>!
''',
                checks=[
                    stdout("вітається з введеним ім'ям",
                           contains="Привіт, Аня", stdin="Аня\n"),
                    stdout("працює з іншим ім'ям",
                           contains="Привіт, Олег", stdin="Олег\n"),
                    stdout("не друкує фігурні дужки",
                           not_contains="{name}", stdin="Аня\n"),
                ],
                hints=[
                    hint("де шукати", "input() повертає рядок — те, що ввели. "
                                      "Отже результат можна одразу вставити у f-рядок."),
                    hint("класична помилка", 'print("Привіт, {name}!") — без літери f '
                                             "дужки так і надрукуються."),
                    solution('''name = input("Як тебе звати? ")
print(f"Привіт, {name}!")'''),
                ],
            ),
            task(
                id="w1-arith",
                title="Арифметика: секунди у години",
                level="Середньо",
                statement="""
                    <p>У Python <code>//</code> — це ціле ділення, а <code>%</code> —
                    остача від ділення. Разом вони розкладають число на частини.</p>
                    <h4>Що треба зробити</h4>
                    <p>Число <code>total_seconds = 3725</code> — це 1 година 2 хвилини
                    5 секунд. Порахуй <code>hours</code>, <code>minutes</code>,
                    <code>seconds</code> так, щоб програма вивела:</p>
                    <pre>Годин: 1
Хвилин: 2
Секунд: 5</pre>
                    <h4>Напрямок думки</h4>
                    <ul>
                        <li>скільки цілих годин у 3725 секундах? <code>3725 // 3600</code></li>
                        <li>а що залишилось після годин? <code>3725 % 3600</code></li>
                    </ul>
                """,
                starter="""total_seconds = 3725

hours = 0      # заміни на правильний вираз
minutes = 0    # використай залишок після годин
seconds = 0    # а тут залишок після хвилин

print("Годин:", hours)
print("Хвилин:", minutes)
print("Секунд:", seconds)
""",
                checks=[
                    stdout("години правильні", contains="Годин: 1"),
                    stdout("хвилини правильні", contains="Хвилин: 2"),
                    stdout("секунди правильні", contains="Секунд: 5"),
                    code("змінні пораховані, а не вписані руками",
                         "\n".join([
                             "assert total_seconds // 3600 == hours",
                             "assert (total_seconds % 3600) // 60 == minutes",
                             "assert total_seconds % 60 == seconds",
                         ])),
                ],
                hints=[
                    hint("де шукати", "Хвилини — це залишок після годин, поділений на 60. "
                                      "Секунди — залишок після хвилин."),
                    hint("яка конструкція", "hours = total_seconds // 3600\n"
                                             "rest = total_seconds % 3600\n"
                                             "minutes = rest // 60\n"
                                             "seconds = rest % 60"),
                    solution("""total_seconds = 3725

hours = total_seconds // 3600
rest = total_seconds % 3600
minutes = rest // 60
seconds = rest % 60

print("Годин:", hours)
print("Хвилин:", minutes)
print("Секунд:", seconds)"""),
                ],
            ),
            task(
                id="w1-if-even",
                title="Умови: парне чи непарне",
                level="Середньо",
                stdin="8\n",
                statement="""
                    <p>Умова <code>if</code> виконує код лише тоді, коли вираз істинний.
                    Парність перевіряють остачею від ділення на 2.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>зчитай ціле число: <code>int(input(...))</code>;</li>
                        <li>якщо <code>number % 2 == 0</code> — виведи <code>парне</code>,
                        інакше — <code>непарне</code>.</li>
                    </ul>
                    <h4>Перевірять</h4>
                    <p>Не лише 8 і 7, а й <b>нуль</b> — він парний, і новачки тут часто
                    помиляються.</p>
                """,
                starter="""number = int(input("Введи число: "))

# Допиши if / else тут
print("не знаю")
""",
                checks=[
                    stdout("8 — парне", contains="парне", not_contains="непарне",
                           stdin="8\n"),
                    stdout("7 — непарне", contains="непарне", stdin="7\n"),
                    stdout("0 — парне", contains="парне", not_contains="непарне",
                           stdin="0\n"),
                ],
                hints=[
                    hint("де шукати", "Парне число ділиться на 2 без остачі: "
                                      "number % 2 == 0. Далі звичайна конструкція if / else."),
                    hint("яка конструкція", 'if number % 2 == 0:\n    print("парне")\n'
                                             'else:\n    print("непарне")'),
                    solution('''number = int(input("Введи число: "))

if number % 2 == 0:
    print("парне")
else:
    print("непарне")'''),
                ],
            ),
            task(
                id="w1-marks",
                title="elif: оцінка за балами",
                level="Середньо",
                stdin="95\n",
                statement="""
                    <p><code>elif</code> — це «а якщо ні, то перевір ще ось це».
                    Ланцюжок перевірок іде зверху вниз і звертається до першої істинної.</p>
                    <h4>Шкала</h4>
                    <ul>
                        <li>90 і більше → <code>Відмінно</code></li>
                        <li>75 і більше → <code>Добре</code></li>
                        <li>60 і більше → <code>Задовільно</code></li>
                        <li>менше 60 → <code>Не склав</code></li>
                    </ul>
                    <p class="warn">Порядок перевірок критичний: якщо першою поставити
                    «більше 60», то 95 балів теж пройдуть її.</p>
                """,
                starter="""score = int(input("Скільки балів? "))

# 90+ → Відмінно, 75+ → Добре, 60+ → Задовільно, інакше → Не склав
print("?")
""",
                checks=[
                    stdout("95 — Відмінно", contains="Відмінно", stdin="95\n"),
                    stdout("74 — Задовільно", contains="Задовільно",
                           not_contains="Відмінно", stdin="74\n"),
                    stdout("60 — Задовільно", contains="Задовільно", stdin="60\n"),
                    stdout("40 — Не склав", contains="Не склав", stdin="40\n"),
                ],
                hints=[
                    hint("де шукати", "Це ланцюжок if / elif / elif / else. "
                                      "Перевірки мають іти від найвищого балу до найнижчого."),
                    hint("яка конструкція", "if score >= 90:\n    ...\n"
                                             "elif score >= 75:\n    ...\n"
                                             "elif score >= 60:\n    ...\nelse:\n    ..."),
                    solution('''score = int(input("Скільки балів? "))

if score >= 90:
    print("Відмінно")
elif score >= 75:
    print("Добре")
elif score >= 60:
    print("Задовільно")
else:
    print("Не склав")'''),
                ],
            ),
            task(
                id="w1-calc",
                title="Проєкт: калькулятор",
                level="Проєкт",
                minutes=20,
                stdin="5\n3\n+\n",
                statement="""
                    <p>Перший справжній проєкт: програма, яка приймає два числа й дію,
                    а потім рахує результат. Це вже не вправа, а інструмент.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>зчитай два числа як <code>float</code>;</li>
                        <li>зчитай дію — один символ: <code>+ - * /</code>;</li>
                        <li>через <code>if / elif / else</code> порахуй результат і виведи його;</li>
                        <li>для ділення виводь рівно два знаки після коми:
                        <code>print(f"{result:.2f}")</code>.</li>
                    </ul>
                    <h4>Перевірять</h4>
                    <p>Усі чотири дії. Ділення на нуль поки не обробляємо — це буде
                    в темі <code>try / except</code>.</p>
                """,
                starter="""first = float(input("Перше число: "))
second = float(input("Друге число: "))
action = input("Дія (+, -, *, /): ")

# Порахуй результат для обраної дії та виведи його
print("?")
""",
                checks=[
                    stdout("додає", contains="8", stdin="5\n3\n+\n"),
                    stdout("віднімає", contains="2", stdin="5\n3\n-\n"),
                    stdout("множить", contains="15", stdin="5\n3\n*\n"),
                    stdout("ділить із двома знаками", contains="1.67", stdin="5\n3\n/\n"),
                ],
                hints=[
                    hint("де шукати", "Спершу виріш, яка дія обрана (if / elif), а потім "
                                      "порахуй результат. Символ дії порівнюй як рядок: "
                                      'action == "+".'),
                    hint("формат виводу", 'print(f"{result:.2f}") — дужки з :.2f '
                                          "означають «два знаки після коми»."),
                    solution('''first = float(input("Перше число: "))
second = float(input("Друге число: "))
action = input("Дія (+, -, *, /): ")

if action == "+":
    result = first + second
elif action == "-":
    result = first - second
elif action == "*":
    result = first * second
elif action == "/":
    result = first / second
else:
    result = None

if result is None:
    print("Невідома дія")
elif action == "/":
    print(f"{result:.2f}")
else:
    print(result)'''),
                ],
            ),
        ),
        # Дрили йдуть одразу після свого тижня: теорія → 5 коротких вправ
        # на ту саму навичку, поки вона ще гаряча.
        WEEK1_DRILLS,
        topic(
            "Тиждень 2 · Цикли та списки",
            task(
                id="w2-for",
                title="Цикл for: сума чисел",
                level="Середньо",
                statement="""
                    <p><code>for</code> перебирає числа й виконує тіло циклу для кожного.
                    <code>range(1, 101)</code> — це числа від 1 до 100 включно.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li>порахуй суму всіх чисел від 1 до 100 → <code>Сума: 5050</code>;</li>
                        <li>порахуй суму лише парних чисел → <code>Парних: 2550</code>.</li>
                    </ul>
                    <h4>Навіщо два рази</h4>
                    <p>Перший цикл — просте накопичення. Другий — накопичення з умовою
                    всередині, а це вже 90% реальних задач.</p>
                """,
                starter="""total = 0
# Проходь циклом по числах від 1 до 100 і додавай їх у total
for number in range(1, 101):
    pass

print("Сума:", total)

even_total = 0
# Тепер додавай лише парні числа
print("Парних:", even_total)
""",
                checks=[
                    stdout("сума 1..100", contains="Сума: 5050"),
                    stdout("сума парних", contains="Парних: 2550"),
                    code("змінні пораховані циклом",
                         "assert total == 5050 and even_total == 2550"),
                ],
                hints=[
                    hint("де шукати", "Перед циклом створи змінну-накопичувач (0), "
                                      "а всередині циклу додавай до неї число: total += number."),
                    hint("умова всередині циклу",
                         "if number % 2 == 0:\n    even_total += number"),
                    solution("""total = 0
for number in range(1, 101):
    total += number

print("Сума:", total)

even_total = 0
for number in range(1, 101):
    if number % 2 == 0:
        even_total += number

print("Парних:", even_total)"""),
                ],
            ),
            task(
                id="w2-while",
                title="Цикл while: таблиця множення",
                level="Середньо",
                statement="""
                    <p><code>while</code> повторюється, поки умова істинна. Головна
                    небезпека — забути змінити лічильник і отримати вічний цикл.
                    У тренажері такий код зупиниться по таймауту, але у звичайній
                    програмі він просто зависне.</p>
                    <h4>Що треба зробити</h4>
                    <p>Виведи таблицю множення числа 7 від 1 до 5:</p>
                    <pre>7 x 1 = 7
7 x 2 = 14
7 x 3 = 21
7 x 4 = 28
7 x 5 = 35</pre>
                """,
                starter="""number = 7
multiplier = 1

# Поки multiplier <= 5 — виводь рядок і збільшуй multiplier на 1
while False:
    pass
""",
                checks=[
                    stdout("перший рядок таблиці", contains="7 x 1 = 7"),
                    stdout("останній рядок таблиці", contains="7 x 5 = 35"),
                    stdout("не виходить за межі", not_contains="7 x 6"),
                ],
                hints=[
                    hint("де шукати", "Тіло while має містити дві дії: print(...) і "
                                      "multiplier += 1. Без другої цикл ніколи не закінчиться."),
                    hint("яка конструкція",
                         'print(f"{number} x {multiplier} = {number * multiplier}")\n'
                         "multiplier += 1"),
                    solution("""number = 7
multiplier = 1

while multiplier <= 5:
    print(f"{number} x {multiplier} = {number * multiplier}")
    multiplier += 1"""),
                ],
            ),
            task(
                id="w2-strings",
                title="Рядки: методи та форматування",
                level="Середньо",
                statement="""
                    <p>Рядок — теж послідовність, і в нього є власні методи:
                    <code>strip()</code>, <code>capitalize()</code>, <code>upper()</code>,
                    <code>split()</code>.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши функцію <code>clean(text)</code>, яка:</p>
                    <ul>
                        <li>прибирає пробіли з країв;</li>
                        <li>робить першу літеру великою, а решту — малими.</li>
                    </ul>
                    <pre>clean("  привіт  ")  →  "Привіт"
clean("ПРИВІТ")     →  "Привіт"
clean("")           →  ""</pre>
                    <h4>Підказка</h4>
                    <p>Методи можна викликати ланцюжком: <code>text.strip().capitalize()</code>.</p>
                """,
                starter="""def clean(text):
    # прибери пробіли з країв і вирівняй регістр
    return text
""",
                checks=[
                    code("прибирає зайві пробіли", 'assert clean("  привіт  ") == "Привіт"'),
                    code("вирівнює регістр", 'assert clean("ПРИВІТ") == "Привіт"'),
                    code("порожній рядок не ламає",
                         'assert clean("") == "", "порожній рядок має лишитись порожнім"'),
                    code("не псує готовий рядок", 'assert clean("Аня") == "Аня"'),
                ],
                hints=[
                    hint("де шукати", "Тобі потрібні два методи: strip() прибирає пробіли, "
                                      "capitalize() робить першу літеру великою."),
                    hint("яка конструкція", "return text.strip().capitalize()"),
                    solution("""def clean(text):
    return text.strip().capitalize()"""),
                ],
            ),
            task(
                id="w2-list",
                title="Списки: append, len і перебір",
                level="Середньо",
                statement="""
                    <p>Список — це впорядкований набір значень:
                    <code>[1, 2, 3]</code>. Додають елементи методом
                    <code>append()</code>, кількість показує <code>len()</code>.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши функцію <code>evens(numbers)</code>, яка повертає
                    <b>новий список</b> лише з парних чисел у тому ж порядку.</p>
                    <pre>evens([1, 2, 3, 4])  →  [2, 4]
evens([])            →  []
evens([1, 3])        →  []</pre>
                    <p class="warn">Створи порожній список усередині функції — інакше
                    при повторних викликах результати злипляться.</p>
                """,
                starter="""def evens(numbers):
    result = []
    # Пройди циклом по numbers і додай парні у result
    return result
""",
                checks=[
                    code("залишає лише парні", "assert evens([1, 2, 3, 4]) == [2, 4]"),
                    code("порожній список", "assert evens([]) == []"),
                    code("усі непарні — порожній результат", "assert evens([1, 3, 5]) == []"),
                    code("зберігає порядок і довжину",
                         "assert evens(list(range(10))) == [0, 2, 4, 6, 8]"),
                    code("не змінює вхідний список",
                         "\n".join([
                             "data = [1, 2, 3]",
                             "evens(data)",
                             'assert data == [1, 2, 3], "вхідний список має лишитись без змін"',
                         ])),
                ],
                hints=[
                    hint("де шукати", "Порожній список + цикл + умова + append()."),
                    hint("яка конструкція",
                         "for number in numbers:\n    if number % 2 == 0:\n        result.append(number)"),
                    solution("""def evens(numbers):
    result = []
    for number in numbers:
        if number % 2 == 0:
            result.append(number)
    return result"""),
                ],
            ),
            task(
                id="w2-guess",
                title="Проєкт: логіка гри «Вгадай число»",
                level="Проєкт",
                minutes=20,
                statement="""
                    <p>Гра «Вгадай число» — класика з твого роадмапу. Але спершу
                    відокремимо логіку від вводу: так код можна перевірити тестами,
                    і саме так роблять у реальних проєктах.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>hint_for(secret, guess)</code> → <code>"більше"</code>,
                        якщо загадане число більше за спробу; <code>"менше"</code>, якщо
                        менше; <code>"вгадав"</code>, якщо рівні;</li>
                        <li><code>distance(secret, guess)</code> → на скільки
                        спроба відрізняється від загаданого (модуль різниці);</li>
                        <li><code>is_hot(secret, guess)</code> → <code>True</code>,
                        якщо різниця не більша за 2.</li>
                    </ul>
                    <h4>Навіщо три функції</h4>
                    <p>Маленькі функції з однією відповідальністю легко читати й
                    перевіряти. Це перший крок до нормальної архітектури.</p>
                """,
                starter="""def distance(secret, guess):
    # модуль різниці: abs(...)
    return 0


def hint_for(secret, guess):
    # використай distance() або порівняння напряму
    return "?"


def is_hot(secret, guess):
    return False
""",
                checks=[
                    code('вгадав', 'assert hint_for(50, 50) == "вгадав"'),
                    code('загадане більше', 'assert hint_for(50, 30) == "більше"'),
                    code('загадане менше', 'assert hint_for(50, 70) == "менше"'),
                    code('рахує відстань', "assert distance(50, 45) == 5 and distance(45, 50) == 5"),
                    code('гаряче поруч',
                         "assert is_hot(50, 52) is True, 'різниця 2 — гаряче'\n"
                         "assert is_hot(50, 40) is False, 'різниця 10 — не гаряче'"),
                ],
                hints=[
                    hint("де шукати", "abs(secret - guess) — це відстань між числами. "
                                      "Далі лишається порівняти secret і guess."),
                    hint("яка конструкція",
                         'if secret == guess:\n    return "вгадав"\n'
                         'if secret > guess:\n    return "більше"\n'
                         'return "менше"'),
                    solution('''def distance(secret, guess):
    return abs(secret - guess)


def hint_for(secret, guess):
    if secret == guess:
        return "вгадав"
    if secret > guess:
        return "більше"
    return "менше"


def is_hot(secret, guess):
    return distance(secret, guess) <= 2'''),
                ],
            ),
        ),
        WEEK2_DRILLS,
        topic(
            "Тиждень 3 · Функції та словники",
            task(
                id="w3-greet",
                title="Функція greet(name)",
                level="Легко",
                statement="""
                    <p>Функція — це іменований шматок коду, який можна викликати
                    багато разів. Напиши функцію <code>greet(name)</code>, яка
                    <b>повертає</b> рядок привітання.</p>
                    <pre>greet("Аня")  →  "Привіт, Аня!"</pre>
                    <h4>Не забудь</h4>
                    <ul>
                        <li><code>return</code> віддає результат назовні, а
                        <code>print()</code> лише друкує — це різні речі;</li>
                        <li>f-рядок вставляє значення змінної в текст.</li>
                    </ul>
                """,
                starter='''def greet(name):
    # Функція поки нічого не повертає. Виправ це.
    pass


print(greet("Світ"))   # запусти й подивись, що виводить
''',
                checks=[
                    code("greet('Аня') повертає 'Привіт, Аня!'",
                         'assert greet("Аня") == "Привіт, Аня!"'),
                    code("працює з будь-яким іменем",
                         'assert greet("Python") == "Привіт, Python!"'),
                    code("повертає саме рядок",
                         'assert isinstance(greet("Тест"), str), "перевір, чи є return"'),
                ],
                hints=[
                    hint("де шукати", "Подивись у консоль знизу: зараз функція повертає None. "
                                      "Потрібен оператор, який віддає значення назовні."),
                    hint("яка конструкція",
                         'return f"Привіт, {name}!" — і жодного print() у тілі функції.'),
                    solution('''def greet(name):
    return f"Привіт, {name}!"'''),
                ],
            ),
            task(
                id="w3-dict",
                title="Словники: підрахунок слів",
                level="Середньо",
                statement="""
                    <p>Словник зберігає пари «ключ → значення»:
                    <code>{"їжа": 120, "таксі": 50}</code>. Головний трюк —
                    <code>dict.get(key, 0)</code>, який повертає 0 замість помилки,
                    якщо ключа ще немає.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши функцію <code>word_count(text)</code>, яка повертає
                    словник «слово → скільки разів воно зустрілось»:</p>
                    <pre>word_count("мама мила раму")  →  {"мама": 1, "мила": 1, "раму": 1}
word_count("а а б")           →  {"а": 2, "б": 1}</pre>
                    <h4>Схема</h4>
                    <ol>
                        <li><code>text.split()</code> розбиває рядок на слова;</li>
                        <li>для кожного слова: <code>counts[word] = counts.get(word, 0) + 1</code>.</li>
                    </ol>
                """,
                starter='''def word_count(text):
    counts = {}
    # розбий рядок на слова і порахуй кожне
    return counts
''',
                checks=[
                    code("рахує кожне слово",
                         'assert word_count("мама мила раму") == {"мама": 1, "мила": 1, "раму": 1}'),
                    code("рахує повтори", 'assert word_count("а а б") == {"а": 2, "б": 1}'),
                    code("порожній рядок", "assert word_count(\"\") == {}"),
                    code("подвійні пробіли не заважають",
                         'assert word_count("а  б") == {"а": 1, "б": 1}'),
                ],
                hints=[
                    hint("де шукати", "dict.get(ключ, 0) повертає значення або 0, якщо ключа "
                                      "ще немає — саме тому він ідеальний для лічильника."),
                    hint("яка конструкція",
                         "for word in text.split():\n"
                         "    counts[word] = counts.get(word, 0) + 1"),
                    solution('''def word_count(text):
    counts = {}
    for word in text.split():
        counts[word] = counts.get(word, 0) + 1
    return counts'''),
                ],
            ),
            task(
                id="w3-expenses",
                title="Проєкт: менеджер витрат (ядро)",
                level="Проєкт",
                minutes=25,
                statement="""
                    <p>Консольний менеджер витрат з твого роадмапу. Спершу — ядро
                    без вводу й файлів: три функції, які працюють зі словником
                    категорій.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>add_expense(expenses, category, amount)</code> —
                        додає витрату, повторні категорії сумуються;</li>
                        <li><code>total(expenses)</code> — сума всіх витрат;</li>
                        <li><code>top_category(expenses)</code> — назва найдорожчої
                        категорії, а для порожнього словника — <code>None</code>.</li>
                    </ul>
                    <h4>Приклад роботи</h4>
                    <pre>expenses = {}
add_expense(expenses, "їжа", 120)
add_expense(expenses, "їжа", 80)
add_expense(expenses, "таксі", 150)
expenses      →  {"їжа": 200, "таксі": 150}
total(...)    →  350
top_category(...)  →  "їжа"</pre>
                """,
                starter='''def add_expense(expenses, category, amount):
    # якщо категорія вже є — додай до неї, інакше створи
    pass


def total(expenses):
    # сума всіх значень словника (підказка: expenses.values())
    return 0


def top_category(expenses):
    # категорія з найбільшою сумою
    return None
''',
                checks=[
                    code("додає першу витрату",
                         '\n'.join([
                             "expenses = {}",
                             'add_expense(expenses, "їжа", 120)',
                             'assert expenses == {"їжа": 120}',
                         ])),
                    code("сумує повторні категорії",
                         '\n'.join([
                             "expenses = {}",
                             'add_expense(expenses, "їжа", 100)',
                             'add_expense(expenses, "їжа", 50)',
                             'assert expenses["їжа"] == 150, "повторні витрати мають сумуватись"',
                         ])),
                    code("рахує загальну суму",
                         'assert total({"їжа": 100, "таксі": 50}) == 150'),
                    code("знаходить найдорожчу категорію",
                         'assert top_category({"їжа": 100, "таксі": 250}) == "таксі"'),
                    code("порожній словник не ламає",
                         "\n".join([
                             "assert total({}) == 0",
                             'assert top_category({}) is None, "для порожнього словника поверни None"',
                         ])),
                ],
                hints=[
                    hint("де шукати", "Категорія — ключ словника. У add_expense знову "
                                      "стане у пригоді expenses.get(category, 0)."),
                    hint("найдорожча категорія",
                         "max(expenses, key=expenses.get) — max уміє шукати не значення, "
                         "а ключ за допомогою функції."),
                    solution('''def add_expense(expenses, category, amount):
    expenses[category] = expenses.get(category, 0) + amount


def total(expenses):
    return sum(expenses.values())


def top_category(expenses):
    if not expenses:
        return None
    return max(expenses, key=expenses.get)'''),
                ],
            ),
        ),
        WEEK3_DRILLS,
        topic(
            "Тиждень 4 · Файли і помилки",
            task(
                id="w4-files",
                title="Читання файлу рядок за рядком",
                level="Складно",
                statement="""
                    <p>Програма, яка не вміє читати файли, забуває все після виходу.
                    Конструкція <code>with open(...)</code> відкриває файл і гарантовано
                    закриває його, навіть якщо всередині сталась помилка.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>read_numbers(path)</code>, яка читає текстовий файл,
                    де кожен рядок — число, і повертає список цілих чисел.
                    Порожні рядки треба ігнорувати.</p>
                    <pre>файл: "1\\n2\\n3\\n"     →  [1, 2, 3]
файл: "5\\n\\n7\\n"      →  [5, 7]
порожній файл          →  []</pre>
                    <h4>Схема</h4>
                    <ol>
                        <li>відкрий файл: <code>with open(path, encoding="utf-8") as f:</code></li>
                        <li>пройди рядки циклом <code>for line in f:</code></li>
                        <li>очисти рядок <code>line.strip()</code>, пропусти порожній,
                        перетвори в число <code>int(...)</code>.</li>
                    </ol>
                """,
                starter='''def read_numbers(path):
    numbers = []
    # відкрий файл і додай у numbers усі числа з нього
    return numbers
''',
                checks=[
                    code("читає три числа",
                         "\n".join([
                             'with open("t1.txt", "w", encoding="utf-8") as handle:',
                             '    handle.write("1\\n2\\n3\\n")',
                             'assert read_numbers("t1.txt") == [1, 2, 3]',
                         ])),
                    code("ігнорує порожні рядки",
                         "\n".join([
                             'with open("t2.txt", "w", encoding="utf-8") as handle:',
                             '    handle.write("5\\n\\n7\\n")',
                             'assert read_numbers("t2.txt") == [5, 7]',
                         ])),
                    code("порожній файл дає порожній список",
                         "\n".join([
                             'with open("t3.txt", "w", encoding="utf-8") as handle:',
                             '    handle.write("")',
                             'assert read_numbers("t3.txt") == []',
                         ])),
                ],
                hints=[
                    hint("де шукати", "int() не вміє перетворити рядок із переносом "
                                      '("5\\n"), тому кожен рядок спершу очищують strip().'),
                    hint("яка конструкція",
                         "with open(path, encoding=\"utf-8\") as handle:\n"
                         "    for line in handle:\n"
                         "        line = line.strip()\n"
                         "        if line:\n"
                         "            numbers.append(int(line))"),
                    solution('''def read_numbers(path):
    numbers = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                numbers.append(int(line))
    return numbers'''),
                ],
            ),
            task(
                id="w4-errors",
                title="try / except: код, що не падає",
                level="Складно",
                statement="""
                    <p>Помилки не треба боятися — їх треба обробляти.
                    <code>try / except</code> дозволяє зробити запасний план, коли
                    щось пішло не так.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>safe_int(value, default=0)</code>, яка перетворює
                    рядок у число, а якщо це неможливо — повертає <code>default</code>.</p>
                    <pre>safe_int("42")            →  42
safe_int("не число", 7)   →  7
safe_int("")              →  0
safe_int("  8  ")         →  8</pre>
                    <h4>Питання на подумати</h4>
                    <p>Яку саме помилку кидає <code>int("не число")</code>? Подивись
                    у консоль, коли запустиш код без try.</p>
                """,
                starter='''def safe_int(value, default=0):
    # спробуй int(value); якщо не вийшло — поверни default
    return value
''',
                checks=[
                    code("читає число з рядка", 'assert safe_int("42") == 42'),
                    code("повертає default при помилці",
                         'assert safe_int("не число", 7) == 7, "у блоці except має бути return default"'),
                    code("default дорівнює нулю", 'assert safe_int("") == 0'),
                    code("пробіли навколо не заважають", 'assert safe_int("  8  ") == 8'),
                    code("повертає саме число",
                         'assert isinstance(safe_int("3"), int)'),
                ],
                hints=[
                    hint("де шукати", 'int("не число") кидає ValueError. Отже потрібен '
                                      "except ValueError."),
                    hint("яка конструкція",
                         "try:\n    return int(value)\nexcept ValueError:\n    return default"),
                    solution('''def safe_int(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default'''),
                ],
            ),
            task(
                id="w4-tracker",
                title="Проєкт: трекер витрат у файл",
                level="Проєкт",
                minutes=25,
                statement="""
                    <p>Фінал місяця: дані мають пережити закриття програми. Формат
                    <b>JSON</b> — це звичайний текст, у якому словники й списки
                    зберігаються як є.</p>
                    <h4>Що треба зробити</h4>
                    <ul>
                        <li><code>save_expenses(path, expenses)</code> — записує
                        словник у файл у форматі JSON;</li>
                        <li><code>load_expenses(path)</code> — читає словник назад,
                        а якщо файлу немає, повертає порожній <code>{}</code>.</li>
                    </ul>
                    <h4>Схема</h4>
                    <pre>import json
json.dump(data, handle, ensure_ascii=False)   # запис
json.load(handle)                             # читання
ensure_ascii=False — щоб українські літери не стали \\u0457</pre>
                    <p>Це остання задача місяця. Після неї — перший проєкт у портфоліо
                    й перехід до Git.</p>
                """,
                starter='''import json


def save_expenses(path, expenses):
    # запиши словник у файл як JSON
    pass


def load_expenses(path):
    # прочитай словник із файлу; якщо файлу немає — поверни {}
    return {}
''',
                checks=[
                    code("зберігає і читає назад",
                         "\n".join([
                             'save_expenses("budget.json", {"їжа": 120, "таксі": 50})',
                             'assert load_expenses("budget.json") == {"їжа": 120, "таксі": 50}',
                         ])),
                    code("файл справді у форматі JSON",
                         "\n".join([
                             "import json as _json",
                             'with open("budget.json", encoding="utf-8") as handle:',
                             "    data = _json.load(handle)",
                             'assert data == {"їжа": 120, "таксі": 50}',
                             'assert "їжа" in open("budget.json", encoding="utf-8").read(), '
                             '"додай ensure_ascii=False, щоб файл читався очима"',
                         ])),
                    code("відсутній файл не ламає програму",
                         'assert load_expenses("no_such_file.json") == {}, '
                         '"оброби FileNotFoundError у load_expenses"'),
                ],
                hints=[
                    hint("де шукати", "Для читання файлу, якого немає, Python кидає "
                                      "FileNotFoundError — використай try / except."),
                    hint("яка конструкція",
                         'with open(path, "w", encoding="utf-8") as handle:\n'
                         "    json.dump(expenses, handle, ensure_ascii=False)"),
                    solution('''import json


def save_expenses(path, expenses):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(expenses, handle, ensure_ascii=False)


def load_expenses(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}'''),
                ],
            ),
        ),
        WEEK4_DRILLS,
    ),
)
