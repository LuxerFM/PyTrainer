"""Дрили місяця 1 — коротка практика після кожного тижня теорії.

Навіщо окремий модуль: у місяці 1 на 4 тижні було 18 задач, тобто приблизно
230 хвилин матеріалу. Для «бази» цього замало — змінні, умови, цикли й списки
засвоюються не розумінням, а кількістю повторів на різних даних. Тому після
кожного тижня теорії йде 5 коротких дрилів (5–12 хвилин кожен): одна навичка,
кілька перевірок на різних входах, три підказки.

Що дає саме така форма:

* дрил короткий, тому його не страшно почати («це на 8 хвилин, не на вечір»);
* дрили перевіряють поведінку на **кількох** входах, тому «вписати відповідь
  руками» не працює — це вже зловлено під час написання;
* після дрилів видно, яка саме навичка кульгає: тема «Тренування тижня N»
  у статистиці окрема, і саме туди дивиться план на день.

Ідеї вправ узяті з відкритих джерел, на які посилаємось у `source`:
Codewars (колекція Python 8 kyu), Exercism (Python track), PyNative (збірка
вправ для початківців). Умови переписані українською, перевірки — свої.

Розв'язки перевіряє `tests/test_curriculum.py`: кожен розв'язок має пройти
власні перевірки, а заготовка коду — ні.
"""

from .schema import code, hint, solution, stdout, task, topic

# --------------------------------------------------------------------------
# Тиждень 1 · числа, формати, умови
# --------------------------------------------------------------------------

WEEK1_DRILLS = topic(
    "Тренування тижня 1 · числа, формати, умови",
    task(
        id="d1-temp",
        title="Дрил: конвертер температури",
        level="Легко",
        minutes=8,
        cheatsheet="numbers",
        stdin="36.6\n",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Світ ділиться на дві частини: ті, хто міряє температуру в
            Цельсіях, і ті, хто у Фаренгейтах. Напиши конвертер — заодно
            потренуєш <code>float</code> і форматування чисел.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай температуру в Цельсіях як <code>float</code>;</li>
                <li>порахуй <code>fahrenheit = celsius * 9 / 5 + 32</code>;</li>
                <li>виведи рівно два рядки — по одній цифрі після коми:</li>
            </ul>
            <pre>C: 36.6
F: 97.9</pre>
            <p class="warn">Без <code>:.1f</code> Python покаже
            <code>97.88000000000001</code> — це не помилка, а те, як
            комп'ютер зберігає дробові числа.</p>
        """,
        starter='''celsius = float(input("Температура в Цельсіях: "))

# 1. Порахуй fahrenheit за формулою: C * 9 / 5 + 32
fahrenheit = 0

# 2. Виведи два рядки: C: 36.6 та F: 97.9 (одна цифра після коми)
print("C: ?")
print("F: ?")
''',
        checks=[
            stdout("36.6 °C → 97.9 °F", contains="F: 97.9", stdin="36.6\n"),
            stdout("показує й саму температуру", contains="C: 36.6", stdin="36.6\n"),
            stdout("нуль дає 32.0", contains="F: 32.0", stdin="0\n"),
        ],
        hints=[
            hint("де шукати", "Перетворення — це звичайна арифметика над "
                             "змінною celsius: множення, ділення, додавання."),
            hint("як обмежити знаки", 'f"{celsius:.1f}" — дужки з :.1f означають '
                                      "«одна цифра після коми». Працює і для "
                                      "цілих чисел: 0 стане 0.0."),
            solution('''celsius = float(input("Температура в Цельсіях: "))

fahrenheit = celsius * 9 / 5 + 32

print(f"C: {celsius:.1f}")
print(f"F: {fahrenheit:.1f}")'''),
        ],
    ),
    task(
        id="d1-digits",
        title="Дрил: сума цифр тризначного числа",
        level="Легко",
        minutes=8,
        cheatsheet="numbers",
        stdin="472\n",
        source="Codewars · Python 8 kyu",
        source_url="https://www.codewars.com/collections/python-8kyu-1",
        statement="""
            <p>Число 472 — це три цифри. Дістати їх можна арифметикою:
            <code>472 // 100</code> — сотні, <code>(472 // 10) % 10</code> —
            десятки, <code>472 % 10</code> — одиниці.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай ціле тризначне число;</li>
                <li>порахуй суму його цифр через <code>//</code> і <code>%</code>;</li>
                <li>виведи одним рядком: <code>Сума цифр: 13</code>.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Три різні числа — тому «вписати 13» не вийде.</p>
        """,
        starter='''number = int(input("Тризначне число: "))

# Розклади number на цифри через // і % та додай їх
digits_sum = 0

print("Сума цифр:", digits_sum)
''',
        checks=[
            stdout("472 → 13", contains="Сума цифр: 13", stdin="472\n"),
            stdout("918 → 18", contains="Сума цифр: 18", stdin="918\n"),
            stdout("640 → 10", contains="Сума цифр: 10", stdin="640\n"),
        ],
        hints=[
            hint("де шукати", "Одиниці — це залишок від ділення на 10. "
                             "Відкинути їх — те саме, що поділити націло на 10."),
            hint("яка конструкція", "hundreds = number // 100\n"
                                    "tens = (number // 10) % 10\n"
                                    "units = number % 10\n"
                                    "digits_sum = hundreds + tens + units"),
            solution('''number = int(input("Тризначне число: "))

hundreds = number // 100
tens = (number // 10) % 10
units = number % 10

digits_sum = hundreds + tens + units

print("Сума цифр:", digits_sum)'''),
        ],
    ),
    task(
        id="d1-swap",
        title="Дрил: обмін значень без третьої змінної",
        level="Легко",
        minutes=5,
        cheatsheet="basics",
        statement="""
            <p>У Python обмін двох значень робиться одним рядком — без
            тимчасової змінної, як у більшості інших мов.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>у коді вже є <code>a = 3</code> і <code>b = 7</code>;</li>
                <li>зроби так, щоб у <code>a</code> стало 7, а в <code>b</code> — 3;</li>
                <li>вивід має бути <code>a=7 b=3</code>.</li>
            </ul>
            <p class="warn">Умова здається дурною, але саме так міняються місцями
            два елементи в списку — і це буде в алгоритмах сортування.</p>
        """,
        starter='''a = 3
b = 7

# Обміняй значення місцями
# (підказка: Python уміє присвоювати кільком змінним одночасно)

print(f"a={a} b={b}")
''',
        checks=[
            code("значення справді обміняні",
                 'assert (a, b) == (7, 3), "у a має бути 7, а в b — 3"'),
            stdout("виводить a=7 b=3", contains="a=7 b=3"),
            stdout("старого порядку не лишилось", not_contains="a=3 b=7"),
        ],
        hints=[
            hint("де шукати", "Праворуч від знака = обчислюється значення "
                             "до того, як його присвоять. Тому справа можна "
                             "перелічити обидві змінні."),
            hint("яка конструкція", "a, b = b, a — один рядок, і обидві змінні "
                                    "вже поміняні місцями."),
            solution('''a = 3
b = 7

a, b = b, a

print(f"a={a} b={b}")'''),
        ],
    ),
    task(
        id="d1-max-three",
        title="Дрил: найбільше з трьох — власними умовами",
        level="Середньо",
        minutes=8,
        cheatsheet="conditions",
        stdin="5\n9\n2\n",
        source="Exercism · Python track",
        source_url="https://exercism.org/tracks/python/exercises",
        statement="""
            <p><code>max()</code> розв'яже цю задачу за один рядок, але вміти
            порівнювати самому важливіше: саме так працюють умови в реальному
            коді, де порівнюється не число, а складний стан.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай три цілі числа;</li>
                <li>знайди найбільше <b>власними умовами</b>, без
                <code>max()</code> і без сортування;</li>
                <li>виведи <code>Найбільше: 9</code>.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Три набори чисел, у тому числі коли всі числа рівні — на цьому
            ламається найпопулярніший спосіб «порівняти перше з другим, потім
            переможця з третім».</p>
        """,
        starter='''first = int(input("Перше число: "))
second = int(input("Друге число: "))
third = int(input("Третє число: "))

# Знайди найбільше через if / else
biggest = 0

print("Найбільше:", biggest)
''',
        checks=[
            stdout("5, 9, 2 → 9", contains="Найбільше: 9", stdin="5\n9\n2\n"),
            stdout("8, 1, 3 → 8", contains="Найбільше: 8", stdin="8\n1\n3\n"),
            stdout("4, 4, 4 → 4", contains="Найбільше: 4", stdin="4\n4\n4\n"),
        ],
        hints=[
            hint("де шукати", "Порівнюй парами: спершу перше з другим, потім "
                             "переможця — із третім."),
            hint("яка конструкція",
                 "if first >= second:\n    biggest = first\nelse:\n"
                 "    biggest = second\n\nif third > biggest:\n"
                 "    biggest = third"),
            solution('''first = int(input("Перше число: "))
second = int(input("Друге число: "))
third = int(input("Третє число: "))

if first >= second:
    biggest = first
else:
    biggest = second

if third > biggest:
    biggest = third

print("Найбільше:", biggest)'''),
        ],
    ),
    task(
        id="d1-input-type",
        title="Дрил: input() завжди повертає рядок",
        level="Середньо",
        minutes=8,
        cheatsheet="basics",
        stdin="20\n",
        statement="""
            <p>Найчастіша пастка першого тижня: <code>input()</code> повертає
            <b>рядок</b>, навіть якщо там написані цифри. Тому
            <code>"20" + 10</code> — це помилка <code>TypeError</code>, а не 30.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай вік як рядок;</li>
                <li>перетвори його в ціле число через <code>int()</code>;</li>
                <li>виведи <code>Через 10 років тобі буде 30</code>;</li>
                <li>окремим рядком виведи <code>Тип: int</code> — назву типу
                змінної (не сам об'єкт).</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Ще й те, що <code>age</code> справді число, а не рядок: інакше
            додавання не спрацює.</p>
        """,
        starter='''age_text = input("Скільки тобі років? ")

# age_text — це рядок, навіть якщо там цифри
# 1. Перетвори його в число: age = int(age_text)
age = 0

# 2. Виведи: Через 10 років тобі буде 30
# 3. Виведи: Тип: int   (підказка: type(age).__name__)
print("?")
''',
        checks=[
            stdout("додає роки до числа", contains="Через 10 років тобі буде 30",
                   stdin="20\n"),
            stdout("працює з іншим віком", contains="Через 10 років тобі буде 17",
                   stdin="7\n"),
            stdout("називає тип", contains="Тип: int", stdin="20\n"),
            code("age — справжнє число",
                 'assert isinstance(age, int) and age == 20, "age має бути числом 20"'),
        ],
        hints=[
            hint("де шукати", "int(...) перетворює рядок із цифрами в число. "
                             "Далі з ним можна рахувати як звичайно."),
            hint("як назвати тип", "type(age) — це сам тип; його назва — "
                                   "type(age).__name__, тобто рядок \"int\"."),
            solution('''age_text = input("Скільки тобі років? ")

age = int(age_text)

print(f"Через 10 років тобі буде {age + 10}")
print(f"Тип: {type(age).__name__}")'''),
        ],
    ),
)

# --------------------------------------------------------------------------
# Тиждень 2 · цикли та списки
# --------------------------------------------------------------------------

WEEK2_DRILLS = topic(
    "Тренування тижня 2 · цикли та списки",
    task(
        id="d2-fizzbuzz",
        title="Дрил: FizzBuzz — класика співбесід",
        level="Середньо",
        minutes=10,
        cheatsheet="loops",
        source="Codewars · Python 8 kyu",
        source_url="https://www.codewars.com/collections/python-8kyu-1",
        statement="""
            <p>Цю задачу дають на співбесідах частіше за будь-яку іншу: вона
            перевіряє, чи ти розумієш порядок перевірок і остачу від ділення.</p>
            <h4>Що треба зробити</h4>
            <p>Виведи числа від 1 до 15, кожне з нового рядка, але:</p>
            <ul>
                <li>кратні 3 → <code>Fizz</code>;</li>
                <li>кратні 5 → <code>Buzz</code>;</li>
                <li>кратні і 3, і 5 → <code>FizzBuzz</code>.</li>
            </ul>
            <pre>1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz</pre>
            <p class="warn">Порядок перевірок критичний: якщо спершу поставити
            «кратне 3», то 15 ніколи не дійде до FizzBuzz.</p>
        """,
        starter='''# Для кожного числа від 1 до 15 виведи число, Fizz, Buzz або FizzBuzz
for number in range(1, 16):
    print("?")
''',
        checks=[
            stdout("усі 15 рядків правильні",
                   equals="1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\n"
                          "Fizz\n13\n14\nFizzBuzz"),
            stdout("кожне число з нового рядка", lines=15),
        ],
        hints=[
            hint("де шукати", "Тобі потрібні два залишки: number % 3 і "
                             "number % 5, обидва порівнюються з нулем."),
            hint("яка конструкція",
                 'if number % 15 == 0:\n    print("FizzBuzz")\n'
                 'elif number % 3 == 0:\n    print("Fizz")\n'
                 'elif number % 5 == 0:\n    print("Buzz")\n'
                 "else:\n    print(number)"),
            solution('''for number in range(1, 16):
    if number % 15 == 0:
        print("FizzBuzz")
    elif number % 3 == 0:
        print("Fizz")
    elif number % 5 == 0:
        print("Buzz")
    else:
        print(number)'''),
        ],
    ),
    task(
        id="d2-digits-loop",
        title="Дрил: сума цифр циклом while",
        level="Середньо",
        minutes=10,
        cheatsheet="loops",
        stdin="907\n",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Той самий трюк з <code>% 10</code> і <code>// 10</code>, але
            тепер для числа з <b>будь-якою</b> кількістю цифр — а отже, у циклі.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай ціле число;</li>
                <li>поки число більше за нуль: додай його останню цифру
                (<code>number % 10</code>) і відкинь її (<code>number //= 10</code>);</li>
                <li>виведи <code>Сума цифр: 16</code>.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Три числа різної довжини: 907, 999 і 640.</p>
        """,
        starter='''number = int(input("Число: "))
digits_sum = 0

# Поки number > 0:
#     digits_sum += number % 10
#     number = number // 10

print("Сума цифр:", digits_sum)
''',
        checks=[
            stdout("907 → 16", contains="Сума цифр: 16", stdin="907\n"),
            stdout("999 → 27", contains="Сума цифр: 27", stdin="999\n"),
            stdout("640 → 10", contains="Сума цифр: 10", stdin="640\n"),
        ],
        hints=[
            hint("де шукати", "Кожен прохід циклу «відкушує» одну цифру справа: "
                             "остання цифра — це number % 10, решта числа — "
                             "number // 10."),
            hint("умова циклу", "while number > 0:\n    digits_sum += number % 10\n"
                                "    number = number // 10"),
            solution('''number = int(input("Число: "))
digits_sum = 0

while number > 0:
    digits_sum += number % 10
    number = number // 10

print("Сума цифр:", digits_sum)'''),
        ],
    ),
    task(
        id="d2-min-max",
        title="Дрил: найбільше й найменше у списку",
        level="Середньо",
        minutes=10,
        cheatsheet="lists",
        source="Codewars · Python 8 kyu",
        source_url="https://www.codewars.com/collections/python-8kyu-1",
        statement="""
            <p>Список чисел — найчастіша структура в задачах. Звичний спосіб
            знайти крайнє значення — пройтися по списку й порівнювати кожен
            елемент із тим, що вже знайшли.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>у коді вже є список <code>numbers</code>;</li>
                <li>знайди найбільший і найменший елемент <b>власним циклом</b>,
                без <code>max()</code> і <code>min()</code>;</li>
                <li>виведи <code>Найбільше: 9</code> і <code>Найменше: -2</code>.</li>
            </ul>
            <p class="warn">Стартуй не з нуля, а з першого елемента списку:
            інакше список із самих від'ємних чисел дасть неправильну відповідь.</p>
        """,
        starter='''numbers = [7, 3, 9, -2, 9, 0]

biggest = numbers[0]
smallest = numbers[0]

# Пройдися по списку циклом і порівняй кожен елемент

print("Найбільше:", biggest)
print("Найменше:", smallest)
''',
        checks=[
            code("найбільше знайдено правильно",
                 'assert biggest == max(numbers), "biggest пораховano неправильно"'),
            code("найменше знайдено правильно",
                 'assert smallest == min(numbers), "smallest пораховano неправильно"'),
            stdout("друкує найбільше", contains="Найбільше: 9"),
            stdout("друкує найменше", contains="Найменше: -2"),
        ],
        hints=[
            hint("де шукати", "Кожен елемент списку порівнюй із тим, що вже "
                             "лежить у biggest: якщо елемент більший — "
                             "запам'ятай його."),
            hint("яка конструкція", "for number in numbers:\n"
                                    "    if number > biggest:\n"
                                    "        biggest = number"),
            solution('''numbers = [7, 3, 9, -2, 9, 0]

biggest = numbers[0]
smallest = numbers[0]

for number in numbers:
    if number > biggest:
        biggest = number
    if number < smallest:
        smallest = number

print("Найбільше:", biggest)
print("Найменше:", smallest)'''),
        ],
    ),
    task(
        id="d2-vowels",
        title="Дрил: голосні літери у слові",
        level="Середньо",
        minutes=10,
        cheatsheet="strings",
        stdin="Програмування\n",
        source="Codewars · Python 8 kyu",
        source_url="https://www.codewars.com/collections/python-8kyu-1",
        statement="""
            <p>Рядок у Python — це послідовність символів, тож по ньому можна
            ходити циклом так само, як по списку.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай слово;</li>
                <li>порахуй у ньому голосні:
                <code>а е є и і ї о у ю я</code>;</li>
                <li>виведи <code>Голосних: 5</code>.</li>
            </ul>
            <p class="warn">Слово може починатися з великої літери — «Україна»
            має 4 голосні, і <code>У</code> серед них. Тому порівнюй у
            нижньому регістрі.</p>
        """,
        starter='''word = input("Слово: ")
vowels = 0

# Пройдися циклом по слову й порахуй голосні

print("Голосних:", vowels)
''',
        checks=[
            stdout("Програмування → 5", contains="Голосних: 5", stdin="Програмування\n"),
            stdout("Україна → 4 (велика літера теж голосна)",
                   contains="Голосних: 4", stdin="Україна\n"),
            stdout("Молоко → 3", contains="Голосних: 3", stdin="Молоко\n"),
        ],
        hints=[
            hint("де шукати", "Перебирай символи словом: for letter in word. "
                             "Для кожного перевір, чи він є серед голосних."),
            hint("як перевірити входження",
                 'if letter.lower() in "аеєиіїоуюя":\n    vowels += 1'),
            solution('''word = input("Слово: ")
vowels = 0

for letter in word.lower():
    if letter in "аеєиіїоуюя":
        vowels += 1

print("Голосних:", vowels)'''),
        ],
    ),
    task(
        id="d2-reverse",
        title="Дрил: перевернути список — циклом і зрізом",
        level="Середньо",
        minutes=10,
        cheatsheet="lists",
        source="Exercism · Python track",
        source_url="https://exercism.org/tracks/python/exercises/reverse-string",
        statement="""
            <p>Одну й ту саму дію в Python часто можна зробити «руками» й
            готовим інструментом. Корисно вміти обидва способи: перший показує,
            як це працює всередині, другий — як писати коротко.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>є список <code>words</code>; створи <code>backward</code> —
                той самий список у зворотному порядку, зібраний <b>циклом</b>
                (без <code>reversed()</code>);</li>
                <li>зроби те саме зрізом: <code>sliced = words[::-1]</code>;</li>
                <li>виведи два рядки: <code>Циклом: жарт не вже це</code> та
                <code>Зрізом: жарт не вже це</code>.</li>
            </ul>
        """,
        starter='''words = ["це", "вже", "не", "жарт"]
backward = []

# 1. Збери backward циклом: від останнього індексу до нульового
# 2. sliced = words[::-1]
sliced = []

# 3. Виведи два рядки з пробілами між словами: " ".join(...)
print("Циклом: ?")
print("Зрізом: ?")
''',
        checks=[
            code("цикл дав перевернутий список",
                 'assert backward == ["жарт", "не", "вже", "це"], '
                 '"у backward неправильний порядок"'),
            code("зріз дав те саме", "assert sliced == backward"),
            stdout("друкує результат циклу", contains="Циклом: жарт не вже це"),
            stdout("друкує результат зрізу", contains="Зрізом: жарт не вже це"),
        ],
        hints=[
            hint("де шукати", "Індекси списку йдуть від 0 до len(words) - 1. "
                             "Щоб іти з кінця, потрібен range із кроком -1."),
            hint("яка конструкція",
                 "for index in range(len(words) - 1, -1, -1):\n"
                 "    backward.append(words[index])\n\nsliced = words[::-1]"),
            solution('''words = ["це", "вже", "не", "жарт"]
backward = []

for index in range(len(words) - 1, -1, -1):
    backward.append(words[index])

sliced = words[::-1]

print("Циклом:", " ".join(backward))
print("Зрізом:", " ".join(sliced))'''),
        ],
    ),
)

# --------------------------------------------------------------------------
# Тиждень 3 · функції та словники
# --------------------------------------------------------------------------

WEEK3_DRILLS = topic(
    "Тренування тижня 3 · функції та словники",
    task(
        id="d3-discount",
        title="Дрил: функція зі знижкою",
        level="Середньо",
        minutes=12,
        cheatsheet="functions",
        source="Exercism · Python track",
        source_url="https://exercism.org/tracks/python/exercises/two-fer",
        statement="""
            <p>Функція з параметром за замовчуванням — це спосіб сказати
            «звичайно ось так, але можна й інакше».</p>
            <h4>Що треба зробити</h4>
            <p>Допиши функцію <code>final_price(price, percent=10)</code>:</p>
            <ul>
                <li>повертає ціну після знижки, округлену до копійок;</li>
                <li>якщо <code>percent</code> не передали — знижка 10%;</li>
                <li>знижка не може бути від'ємною чи більшою за 90%: такі
                значення «обрізаються» до 0 і 90 відповідно.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Звичайну знижку, типову (без другого аргументу) і безглузду
            (150%) — функція має витримати всі.</p>
        """,
        starter='''def final_price(price, percent=10):
    """Ціна після знижки: percent відсотків, не менше 0 і не більше 90."""
    return price


print(final_price(100))
''',
        checks=[
            code("без знижки ціна не змінюється", "assert final_price(100, 0) == 100.0"),
            code("знижка 25%", "assert final_price(200, 25) == 150.0"),
            code("типова знижка за замовчуванням", "assert final_price(100) == 90.0"),
            code("завелику знижку обрізає до 90%",
                 "assert final_price(100, 150) == 10.0"),
            code("повертає число, а не рядок",
                 "assert isinstance(final_price(100), float)"),
        ],
        hints=[
            hint("де шукати", "Ціна після знижки — це price * (1 - percent / 100). "
                             "Обрізати значення зручно через min() і max()."),
            hint("як обмежити значення",
                 "percent = max(0, min(90, percent))\n"
                 "return round(price * (1 - percent / 100), 2)"),
            solution('''def final_price(price, percent=10):
    """Ціна після знижки: percent відсотків, не менше 0 і не більше 90."""
    percent = max(0, min(90, percent))
    return round(price * (1 - percent / 100), 2)


print(final_price(100))'''),
        ],
    ),
    task(
        id="d3-copy",
        title="Дрил: не зіпсуй чужий словник",
        level="Середньо",
        minutes=12,
        cheatsheet="dicts",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Функція, яка змінює словник, переданий їй як аргумент, змінює
            його і <b>зовні</b> — бо це той самий об'єкт. Це джерело найважчих
            багів, які шукають годинами.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>допиши <code>with_discount(prices, percent)</code>;</li>
                <li>вона повертає <b>новий</b> словник із цінами після знижки,
                округленими до копійок;</li>
                <li>словник-аргумент має лишитися без змін.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Саме це: що оригінал не змінився. Якщо змінився — перевірка
            скаже про це прямо.</p>
        """,
        starter='''def with_discount(prices, percent):
    """Повертає НОВИЙ словник із цінами після знижки. Оригінал не чіпає."""
    return prices


print(with_discount({"хліб": 100}, 10))
''',
        checks=[
            code("знижує всі ціни",
                 'assert with_discount({"хліб": 100, "сир": 200}, 10) == '
                 '{"хліб": 90.0, "сир": 180.0}'),
            code("оригінал лишається незмінним",
                 'prices = {"хліб": 100}\n'
                 'discounted = with_discount(prices, 50)\n'
                 'assert prices == {"хліб": 100}, "словник-аргумент змінився!"\n'
                 'assert discounted == {"хліб": 50.0}'),
            code("порожній словник не ламає", "assert with_discount({}, 10) == {}"),
        ],
        hints=[
            hint("де шукати", "Створи порожній словник усередині функції й "
                             "заповни його в циклі по prices.items()."),
            hint("яка конструкція",
                 "for name, price in prices.items():\n"
                 "    result[name] = round(price * (1 - percent / 100), 2)"),
            solution('''def with_discount(prices, percent):
    """Повертає НОВИЙ словник із цінами після знижки. Оригінал не чіпає."""
    result = {}
    for name, price in prices.items():
        result[name] = round(price * (1 - percent / 100), 2)
    return result


print(with_discount({"хліб": 100}, 10))'''),
        ],
    ),
    task(
        id="d3-names",
        title="Дрил: чистка тексту й ініціали",
        level="Середньо",
        minutes=12,
        cheatsheet="strings",
        source="Exercism · Python track",
        source_url="https://exercism.org/tracks/python/exercises",
        statement="""
            <p>Дані, які вводить людина, майже завжди «брудні»: зайві пробіли,
            випадковий регістр. Привести їх до ладу — звичайна робота в будь-якій
            програмі.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li><code>clean_name(raw)</code> — прибирає пробіли по краях і
                робить кожне слово з великої літери:
                <code>'  оЛЕна петренко '</code> → <code>'Олена Петренко'</code>;</li>
                <li><code>initials(name)</code> — з повного імені робить
                ініціали: <code>'Олена Петренко'</code> → <code>'О. П.'</code>,
                а для одного слова — <code>'А.'</code>.</li>
            </ul>
            <p class="warn">Рядок незмінний: <code>raw.strip()</code> не змінює
            <code>raw</code>, а <b>повертає</b> новий рядок. Тому результат
            треба комусь присвоїти або повернути.</p>
        """,
        starter='''def clean_name(raw):
    """Прибирає пробіли по краях і виправляє регістр."""
    return raw


def initials(name):
    """З повного імені робить ініціали: 'Олена Петренко' → 'О. П.'"""
    return ""


print(initials("Олена Петренко"))
''',
        checks=[
            code("чистить і виправляє регістр",
                 'assert clean_name("  оЛЕна петренко  ") == "Олена Петренко"'),
            code("працює з одним словом", 'assert clean_name("АНЯ") == "Аня"'),
            code("ініціали з двох слів", 'assert initials("Олена Петренко") == "О. П."'),
            code("ініціали з одного слова", 'assert initials("Аня") == "А."'),
        ],
        hints=[
            hint("де шукати", "У рядків є готові методи: strip() прибирає "
                             "пробіли по краях, title() робить слова з великої "
                             "літери."),
            hint("як узяти ініціали", 'parts = name.split()\n'
                                      'return " ".join(f"{part[0]}." for part in parts)'),
            solution('''def clean_name(raw):
    """Прибирає пробіли по краях і виправляє регістр."""
    return raw.strip().title()


def initials(name):
    """З повного імені робить ініціали: 'Олена Петренко' → 'О. П.'"""
    parts = clean_name(name).split()
    return " ".join(f"{part[0]}." for part in parts)


print(initials("Олена Петренко"))'''),
        ],
    ),
    task(
        id="d3-longest",
        title="Дрил: найдовше слово",
        level="Середньо",
        minutes=12,
        cheatsheet="functions",
        source="Codewars · Python 8 kyu",
        source_url="https://www.codewars.com/collections/python-8kyu-1",
        statement="""
            <p>Функція має повертати <b>результат</b>, а не друкувати його —
            інакше її не можна перевірити тестами й не можна використати в
            іншій програмі.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>допиши <code>longest_word(text)</code>;</li>
                <li>вона повертає найдовше слово з тексту;</li>
                <li>якщо два слова однакової довжини — повертається те, яке
                зустрілося раніше;</li>
                <li>порожній текст → порожній рядок.</li>
            </ul>
        """,
        starter='''def longest_word(text):
    """Повертає найдовше слово. Однакова довжина — перемагає перше."""
    return text


print(longest_word("я вчу python щодня"))
''',
        checks=[
            code("знаходить найдовше", 'assert longest_word("я вчу python щодня") == "python"'),
            code("при рівній довжині — перше",
                 'assert longest_word("код і рот") == "код", '
                 '"для однакових слів має перемагати перше"'),
            code("порожній рядок", 'assert longest_word("") == ""'),
            code("зайві пробіли не заважають", 'assert longest_word("  а   бб  ") == "бб"'),
        ],
        hints=[
            hint("де шукати", "text.split() без аргументів сам прибирає зайві "
                             "пробіли й робить список слів. Далі — звичайний "
                             "пошук найбільшого, як у списку чисел."),
            hint("яка конструкція",
                 'best = ""\nfor word in text.split():\n'
                 "    if len(word) > len(best):\n        best = word\nreturn best"),
            solution('''def longest_word(text):
    """Повертає найдовше слово. Однакова довжина — перемагає перше."""
    best = ""
    for word in text.split():
        if len(word) > len(best):
            best = word
    return best


print(longest_word("я вчу python щодня"))'''),
        ],
    ),
    task(
        id="d3-args",
        title="Дрил: функція, що приймає скільки завгодно чисел",
        level="Середньо",
        minutes=12,
        cheatsheet="functions",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p><code>*numbers</code> у заголовку функції означає «зібери всі
            позиційні аргументи в одну послідовність». Саме так влаштована
            <code>print()</code>, якій байдуже, скільки в неї аргументів.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>допиши <code>total(*numbers)</code>;</li>
                <li>вона повертає суму будь-якої кількості чисел;</li>
                <li>без аргументів — <code>0</code>;</li>
                <li>працює і з дробовими числами.</li>
            </ul>
        """,
        starter='''def total(*numbers):
    """Сума будь-якої кількості чисел. Без аргументів — 0."""
    return 0


print(total(1, 2, 3))
''',
        checks=[
            code("без аргументів — нуль", "assert total() == 0"),
            code("одне число", "assert total(5) == 5"),
            code("багато чисел", "assert total(1, 2, 3, 4) == 10"),
            code("дробові теж рахує", "assert total(1.5, 2.5) == 4.0"),
        ],
        hints=[
            hint("де шукати", "Усередині функції numbers — це звичайна "
                             "послідовність, по якій можна йти циклом."),
            hint("яка конструкція",
                 "result = 0\nfor number in numbers:\n    result += number\nreturn result"),
            solution('''def total(*numbers):
    """Сума будь-якої кількості чисел. Без аргументів — 0."""
    result = 0
    for number in numbers:
        result += number
    return result


print(total(1, 2, 3))'''),
        ],
    ),
)

# --------------------------------------------------------------------------
# Тиждень 4 · файли та помилки
# --------------------------------------------------------------------------

WEEK4_DRILLS = topic(
    "Тренування тижня 4 · файли та помилки",
    task(
        id="d4-write",
        title="Дрил: записати список у файл",
        level="Середньо",
        minutes=12,
        cheatsheet="files",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Файл — це спосіб зберегти дані після завершення програми.
            Запис і читання — дві окремі дії, і звична помилка новачка —
            робити їх одночасно.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>запиши кожен рядок зі списку <code>notes</code> у файл
                <code>notes.txt</code>, кожен — з нового рядка;</li>
                <li>закрий файл і відкрий його знову <b>на читання</b>;</li>
                <li>виведи рядки з нумерацією:</li>
            </ul>
            <pre>1) перший
2) другий
3) третій</pre>
            <p class="warn">Коли пишеш через <code>print</code> у консоль —
            перевірка не побачить цього у файлі. І навпаки: сам файл
            перевіряється окремо.</p>
        """,
        starter='''notes = ["перший", "другий", "третій"]

# 1. Відкрий "notes.txt" у режимі "w" і запиши кожен рядок із \\n
# 2. Відкрий його знову на читання й виведи: 1) перший

print("?")
''',
        checks=[
            code("у файлі справді три рядки",
                 'assert open("notes.txt", encoding="utf-8").read().splitlines() == '
                 '["перший", "другий", "третій"], "вміст notes.txt неправильний"'),
            stdout("нумерує з одиниці", contains="1) перший"),
            stdout("доходить до третього", contains="3) третій"),
            stdout("рівно три рядки", lines=3),
        ],
        hints=[
            hint("де шукати", 'Запис: open("notes.txt", "w", encoding="utf-8"). '
                             "Читання: той самий open, але без другого аргументу. "
                             "Найзручніше — через with, щоб файл закрився сам."),
            hint("як пронумерувати",
                 "for index, line in enumerate(file, start=1):\n"
                 '    print(f"{index}) {line.strip()}")'),
            solution('''notes = ["перший", "другий", "третій"]

with open("notes.txt", "w", encoding="utf-8") as file:
    for note in notes:
        file.write(note + "\\n")

with open("notes.txt", encoding="utf-8") as file:
    for index, line in enumerate(file, start=1):
        print(f"{index}) {line.strip()}")'''),
        ],
    ),
    task(
        id="d4-append",
        title="Дрил: дописати у файл, не стерши старе",
        level="Середньо",
        minutes=12,
        cheatsheet="files",
        files={"log.txt": "старт\n"},
        statement="""
            <p>Режим <code>"w"</code> стирає файл повністю. Тому для журналів,
            логів і списків справ є режим <code>"a"</code> — дописати в кінець.</p>
            <h4>Що треба зробити</h4>
            <p>Поруч із твоїм кодом уже лежить файл <code>log.txt</code> із
            одним рядком <code>старт</code>.</p>
            <ul>
                <li>допиши в кінець два рядки: <code>крок 1</code> і <code>крок 2</code>;</li>
                <li>порахуй, скільки рядків тепер у файлі;</li>
                <li>виведи <code>Рядків: 3</code>.</li>
            </ul>
            <p class="warn">Якщо відкрити у режимі <code>"w"</code>, рядок
            «старт» зникне — і перевірка це помітить.</p>
        """,
        starter='''# У файлі log.txt уже лежить рядок «старт»
with open("log.txt", "w", encoding="utf-8") as file:
    file.write("крок 1\\n")
    file.write("крок 2\\n")

# Порахуй рядки у файлі й виведи: Рядків: 3
print("Рядків: ?")
''',
        checks=[
            stdout("рахує всі три рядки", contains="Рядків: 3"),
            code("старий рядок уцілів",
                 'assert open("log.txt", encoding="utf-8").read().splitlines() == '
                 '["старт", "крок 1", "крок 2"], "файл перезаписано — рядок «старт» зник"'),
        ],
        hints=[
            hint("де шукати", 'Режим дописування — "a" (від append). '
                             'Відкриття: open("log.txt", "a", encoding="utf-8").'),
            hint("як порахувати рядки",
                 'with open("log.txt", encoding="utf-8") as file:\n'
                 "    lines = file.readlines()\n"
                 '    print(f"Рядків: {len(lines)}")'),
            solution('''with open("log.txt", "a", encoding="utf-8") as file:
    file.write("крок 1\\n")
    file.write("крок 2\\n")

with open("log.txt", encoding="utf-8") as file:
    lines = [line for line in file if line.strip()]

print(f"Рядків: {len(lines)}")'''),
        ],
    ),
    task(
        id="d4-count",
        title="Дрил: порахувати рядки й слова у файлі",
        level="Середньо",
        minutes=12,
        cheatsheet="files",
        files={
            "diary.txt": "Сьогодні я вчив Python\n"
                         "Це було складно але цікаво\n"
                         "Завтра продовжу\n"
        },
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Щоденник, лог, звіт — усе це файли, які хочеться швидко
            проаналізувати: скільки там рядків, слів, записів.</p>
            <h4>Що треба зробити</h4>
            <p>Задача приносить із собою файл <code>diary.txt</code> із трьома
            рядками. Прочитай його й виведи:</p>
            <pre>Рядків: 3
Слів: 11</pre>
            <ul>
                <li>рядок — це рядок тексту (порожні не рахуємо);</li>
                <li>слово — те, що <code>split()</code> вважає словом;</li>
                <li>файл змінювати не можна — тільки читати.</li>
            </ul>
        """,
        starter='''# Файл diary.txt уже лежить поруч із твоїм кодом
with open("diary.txt", encoding="utf-8") as file:
    text = file.read()

# Порахуй рядки та слова
print("Рядків: ?")
print("Слів: ?")
''',
        checks=[
            stdout("рахує рядки", contains="Рядків: 3"),
            stdout("рахує слова", contains="Слів: 11"),
            code("файл лишився незмінним",
                 'assert open("diary.txt", encoding="utf-8").read().startswith('
                 '"Сьогодні"), "файл було змінено"'),
        ],
        hints=[
            hint("де шукати", "text.splitlines() дає список рядків, "
                             "text.split() — список слів. Лишається порахувати "
                             "їх len()."),
            hint("як не рахувати порожні",
                 "lines = [line for line in text.splitlines() if line.strip()]"),
            solution('''with open("diary.txt", encoding="utf-8") as file:
    text = file.read()

lines = [line for line in text.splitlines() if line.strip()]
words = text.split()

print(f"Рядків: {len(lines)}")
print(f"Слів: {len(words)}")'''),
        ],
    ),
    task(
        id="d4-try",
        title="Дрил: не падати на поганому вводі",
        level="Середньо",
        minutes=12,
        cheatsheet="exceptions",
        source="PyNative · вправи для початківців",
        source_url="https://pynative.com/python-exercises-with-solutions/",
        statement="""
            <p>Користувач може ввести будь-що. Якщо програма падає з
            <code>ValueError</code> на слові «двадцять» — це не «поганий
            користувач», а непродуманий код.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай вік як рядок;</li>
                <li>спробуй перетворити його в число: якщо вдалося — виведи
                <code>Подвоєний вік: 40</code>;</li>
                <li>якщо ні — виведи <code>Це не число, але я не впав</code>.</li>
            </ul>
            <h4>Перевірять</h4>
            <p>Два числа (20 і 3) і безглуздий текст — третя перевірка
            провалиться, якщо програма впаде.</p>
        """,
        starter='''raw = input("Скільки тобі років? ")

# int(raw) на тексті падає з ValueError — обгорни це в try / except
age = int(raw)
print("?")
''',
        checks=[
            stdout("число подвоює", contains="Подвоєний вік: 40", stdin="20\n"),
            stdout("працює з іншим числом", contains="Подвоєний вік: 6", stdin="3\n"),
            stdout("не падає на тексті",
                   contains="Це не число, але я не впав", stdin="двадцять\n"),
        ],
        hints=[
            hint("де шукати", "try / except ValueError: у try — небезпечне "
                             "перетворення, в except — що робити, якщо не вийшло."),
            hint("яка конструкція",
                 "try:\n    age = int(raw)\nexcept ValueError:\n"
                 '    print("Це не число, але я не впав")\nelse:\n'
                 '    print(f"Подвоєний вік: {age * 2}")'),
            solution('''raw = input("Скільки тобі років? ")

try:
    age = int(raw)
except ValueError:
    print("Це не число, але я не впав")
else:
    print(f"Подвоєний вік: {age * 2}")'''),
        ],
    ),
    task(
        id="d4-divide",
        title="Дрил: ділення, яке не падає на нулі",
        level="Середньо",
        minutes=12,
        cheatsheet="exceptions",
        statement="""
            <p>Ділення на нуль — найчастіша аварія в калькуляторах і звітах.
            Прибирати її «перевіркою заздалегідь» можна, але цікавіше зробити
            це через виняток — і заодно побачити <code>else</code> та
            <code>finally</code>.</p>
            <h4>Що треба зробити</h4>
            <ul>
                <li>зчитай два цілі числа;</li>
                <li>поділи перше на друге та виведи <code>Результат: 5.0</code>;</li>
                <li>якщо друге число нуль — виведи
                <code>На нуль ділити не можна</code>;</li>
                <li><b>у будь-якому випадку</b> останнім рядком виведи
                <code>Перевірку завершено</code>.</li>
            </ul>
            <p class="warn">Останній рядок — це саме те, для чого існує
            <code>finally</code>: він виконується і коли все добре, і коли
            сталася помилка.</p>
        """,
        starter='''first = int(input("Перше число: "))
second = int(input("Друге число: "))

result = first / second
print(f"Результат: {result}")
''',
        checks=[
            stdout("ділить", contains="Результат: 5.0", stdin="10\n2\n"),
            stdout("ловить ділення на нуль",
                   contains="На нуль ділити не можна", stdin="10\n0\n"),
            stdout("завершує роботу після помилки",
                   contains="Перевірку завершено", stdin="10\n0\n"),
            stdout("і коли все добре — теж",
                   contains="Перевірку завершено", stdin="9\n3\n"),
        ],
        hints=[
            hint("де шукати", "Небезпечний рядок — ділення. У try поклади "
                             "саме його, а в except — назву винятку "
                             "ZeroDivisionError."),
            hint("яка конструкція",
                 "try:\n    result = first / second\n"
                 "except ZeroDivisionError:\n"
                 '    print("На нуль ділити не можна")\nelse:\n'
                 '    print(f"Результат: {result}")\nfinally:\n'
                 '    print("Перевірку завершено")'),
            solution('''first = int(input("Перше число: "))
second = int(input("Друге число: "))

try:
    result = first / second
except ZeroDivisionError:
    print("На нуль ділити не можна")
else:
    print(f"Результат: {result}")
finally:
    print("Перевірку завершено")'''),
        ],
    ),
)

# Усі теми дрилів місяця 1 — у порядку тижнів: саме так їх вплітає month1.py.
ALL_DRILL_TOPICS = (WEEK1_DRILLS, WEEK2_DRILLS, WEEK3_DRILLS, WEEK4_DRILLS)

__all__ = [
    "ALL_DRILL_TOPICS",
    "WEEK1_DRILLS",
    "WEEK2_DRILLS",
    "WEEK3_DRILLS",
    "WEEK4_DRILLS",
]
