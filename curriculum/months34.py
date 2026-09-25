"""Місяці 3–4 — інструменти й перші проєкти: інтернет, парсинг, алгоритми.

Алгоритмічний міні-блок зібраний із **класичних задач LeetCode та Codewars**:
умови переказані українською своїми словами, але в кожній задачі вказано
джерело й посилання на оригінал — щоб можна було подивитись англійський
варіант і обговорити його на співбесіді.

Чому саме ці задачі:

* вони розв'язуються тим, що вже вмієш (списки, словники, цикли, функції);
* кожна навчає прийому, який трапляється в реальному коді;
* перевірки власні й приховані — тому «згадати формулу» не вийде, треба
  написати код, який справді працює.
"""

from .debugging import DEBUG_TASKS
from .network import INTERNET_TASKS
from .schema import Month, code, hint, solution, stdout, stub, task, topic

MONTH = Month(
    title="Місяці 3–4 · Інструменти + перші проєкти",
    subtitle="Перші роботи в портфоліо",
    topics=(
        topic(
            "Дані з інтернету",
            *INTERNET_TASKS,
            stub("m3-requests", "requests: та сама робота бібліотекою-клієнтом"),
            stub("m3-nbu", "Проєкт: курси НБУ зі справжнього API (потрібен інтернет)"),
        ),
        topic(
            "Алгоритми й типи (міні-блок, 2 тижні)",
            task(
                id="m3-algo",
                title="Складність на пальцях: друге за величиною число",
                level="Середньо",
                minutes=12,
                cheatsheet="algorithms",
                statement="""
                    <p>Перший алгоритмічний блок починається з дуже простого
                    прикладу — бо тут важлива не сама задача, а спосіб думати.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши функцію <code>second_largest(numbers)</code>, яка
                    повертає <b>друге за величиною</b> число у списку. Повтори
                    одного й того самого числа не рахуються — у
                    <code>[5, 5, 5]</code> другого числа немає, тому
                    повертаємо <code>None</code>.</p>
                    <h4>Два способи, і різниця між ними</h4>
                    <ul>
                        <li>звичайний прохід по списку з двома «комірками»
                        (найбільше й друге) — це <b>O(n)</b>: один прохід;</li>
                        <li><code>sorted(set(numbers))</code> — коротко й
                        зрозуміло, це <b>O(n log n)</b>: сортування.</li>
                    </ul>
                    <p>Для цієї задачі обидва способи правильні. Звикай питати
                    себе «а скільки роботи це коштує?» — саме це відрізняє
                    джуна, який проходить співбесіду, від джуна, який не
                    проходить.</p>
                    <pre>second_largest([1, 2, 3, 4])   → 3
second_largest([5, 5, 5])      → None
second_largest([2, 1])         → 1</pre>
                    <p class="warn">Порожній список і список з одного числа — теж
                    випадки, які треба обробити: повертай <code>None</code>.</p>
                """,
                starter='''def second_largest(numbers):
    """Повертає друге за величиною УНІКАЛЬНЕ число або None."""
    # твій код
''',
                checks=[
                    code("знаходить друге за величиною",
                         "assert second_largest([1, 2, 3, 4]) == 3"),
                    code("ігнорує повтори одного числа",
                         "assert second_largest([5, 5, 5]) is None"),
                    code("не потребує відсортованого списку",
                         "assert second_largest([10, 1, 9]) == 9"),
                    code("працює з двома різними числами",
                         "assert second_largest([2, 1]) == 1"),
                    code("порожній список не ламає функцію",
                         "assert second_largest([]) is None"),
                ],
                hints=[
                    hint("з чого почати",
                         "Спершу треба позбутись повторів — інакше у [5, 5, 5] "
                         "«другим» виявиться те саме 5. Для цього є множина: "
                         "set(numbers)."),
                    hint("яка конструкція",
                         "Найкоротший розв'язок: зробити set, відсортувати у "
                         "зворотному порядку і взяти елемент з індексом 1.\n"
                         "Перевірити довжину треба ДО того, як брати [1], "
                         "інакше буде IndexError."),
                    solution('''def second_largest(numbers):
    unique = sorted(set(numbers), reverse=True)
    if len(unique) < 2:
        return None
    return unique[1]'''),
                ],
            ),
            task(
                id="m3-algo-binary-search",
                title="Бінарний пошук своїми руками",
                level="Середньо",
                minutes=15,
                cheatsheet="algorithms",
                source="Binary Search · LeetCode #704",
                source_url="https://leetcode.com/problems/binary-search/",
                statement="""
                    <p>Класика співбесіди. Уявіть телефонний довідник: щоб
                    знайти «Петренка», ви не читаєте всі сторінки — ви
                    відкриваєте середину й відкидаєте половину. Це і є
                    <b>бінарний пошук</b>, складність <b>O(log n)</b>.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>binary_search(numbers, target)</code> — вона
                    повертає <b>індекс</b> числа <code>target</code> у
                    <b>відсортованому</b> списку, або <code>-1</code>, якщо
                    такого числа немає.</p>
                    <p class="warn">Не використовуй <code>numbers.index()</code>
                    і <code>in</code> — сенс задачі в тому, щоб зробити пошук
                    самому. Через них складність буде O(n), тобто весь
                    сенс загубиться.</p>
                    <h4>Як це працює</h4>
                    <pre>low, high = 0, len(numbers) - 1
while low <= high:
    middle = (low + high) // 2
    # порівнюємо numbers[middle] із target
    # і «відрізаємо» ту половину, де його точно немає</pre>
                    <p>Кожен крок зменшує зону пошуку вдвічі: список із 1 000 000
                    елементів звужується за ~20 кроків замість мільйона.</p>
                """,
                starter='''def binary_search(numbers, target):
    """Повертає індекс target у ВІДСОРТОВАНОМУ списку або -1."""
    # твій код
''',
                checks=[
                    code("знаходить число у середині",
                         "assert binary_search([-1, 0, 3, 5, 9, 12], 9) == 4"),
                    code("шукає у лівій половині",
                         "assert binary_search([-1, 0, 3, 5, 9, 12], 0) == 1"),
                    code("повертає -1, коли числа немає",
                         "assert binary_search([-1, 0, 3, 5, 9, 12], 2) == -1"),
                    code("порожній список",
                         "assert binary_search([], 5) == -1"),
                    code("список з одного елемента",
                         "assert binary_search([7], 7) == 0"),
                    code("шукає останній елемент",
                         "assert binary_search([1, 2, 3, 4, 5], 5) == 4"),
                ],
                hints=[
                    hint("як не зациклитись",
                         "Тобі потрібні дві межі — low і high — і цикл while. "
                         "Умова циклу: low <= high. Кожна ітерація ОБОВ'ЯЗКОВО "
                         "звужує межі, інакше цикл буде нескінченний:\n"
                         "якщо numbers[middle] < target → low = middle + 1\n"
                         "інакше → high = middle - 1"),
                    hint("коли зупинитись",
                         "Три випадки: знайшли (повертаємо middle), шукане "
                         "правіше (рухаємо low), шукане лівіше (рухаємо high). "
                         "Якщо цикл завершився, а ми не вийшли через return — "
                         "числа немає, повертаємо -1."),
                    solution('''def binary_search(numbers, target):
    low, high = 0, len(numbers) - 1
    while low <= high:
        middle = (low + high) // 2
        if numbers[middle] == target:
            return middle
        if numbers[middle] < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1'''),
                ],
            ),
            task(
                id="m3-typing",
                title="Анотації типів у своєму коді",
                level="Легко",
                minutes=10,
                cheatsheet="typing",
                statement="""
                    <p>Анотації типів — це підказки для людей і редактора.
                    Python їх не перевіряє під час роботи, але код стає
                    зрозумілішим: видно, що функція приймає і що повертає.</p>
                    <h4>Що треба зробити</h4>
                    <p>Допиши дві функції <b>разом з анотаціями</b>:</p>
                    <ul>
                        <li><code>average(numbers)</code> приймає список чисел і
                        повертає середнє (число з комою);</li>
                        <li><code>greet(name)</code> приймає ім'я і повертає
                        <code>Привіт, Аня!</code>.</li>
                    </ul>
                    <h4>Синтаксис</h4>
                    <pre>def average(numbers: list[float]) -&gt; float:
    ...
</pre>
                    <p>Двокрапка після параметра — його тип, стрілка
                    <code>-&gt;</code> — тип результату. Перевірити, що
                    анотації справді на місці, можна так:</p>
                    <pre>print(average.__annotations__)
# {'numbers': list[float], 'return': float}</pre>
                    <p class="warn">Заготовка повертає <code>None</code> і не має
                    анотацій — і перевірки це помітять.</p>
                """,
                starter='''# Допиши анотації типів і реалізацію обох функцій.


def average(numbers):
    ...


def greet(name):
    ...
''',
                checks=[
                    code("у average є анотації",
                         'assert average.__annotations__, "додай анотації до average"'),
                    code("greet повертає str",
                         'assert greet.__annotations__.get("return") is str'),
                    code("average рахує середнє",
                         "assert average([2, 4]) == 3.0"),
                    code("greet вітається з іменем",
                         'assert greet("Аня") == "Привіт, Аня!"'),
                    code("анотація повернення у average",
                         'assert average.__annotations__.get("return") is float'),
                ],
                hints=[
                    hint("що таке анотація",
                         "Тип пишеться після двокрапки: numbers: list[float]. "
                         "Тип результату — через стрілку: -> float. "
                         "Це не перевіряється під час роботи, але саме так "
                         "пишуть у реальних проєктах."),
                    hint("як порахувати середнє",
                         "sum(numbers) / len(numbers) — саме ділення, а не //. "
                         "Для {} у f-рядку використовуй фігурні дужки, як у "
                         "f\"Привіт, {name}!\""),
                    solution('''def average(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers)


def greet(name: str) -> str:
    return f"Привіт, {name}!"'''),
                ],
            ),
        ),
        topic(
            "Задачі з LeetCode та Codewars (міні-блок)",
            task(
                id="m3-lc-two-sum",
                title="Two Sum: сума двох чисел",
                level="Середньо",
                minutes=15,
                cheatsheet="dicts",
                source="Two Sum · LeetCode #1",
                source_url="https://leetcode.com/problems/two-sum/",
                statement="""
                    <p>Найвідоміша задача LeetCode — з неї починають майже всі.
                    І вона чудово показує, як словник перетворює повільний
                    розв'язок на швидкий.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>two_sum(numbers, target)</code>: вона
                    повертає <b>список із двох індексів</b> чисел, які в сумі
                    дають <code>target</code>. Розв'язок у кожному списку
                    рівно один, і те саме число двічі використати не
                    можна.</p>
                    <pre>two_sum([2, 7, 11, 15], 9)   → [0, 1]   бо 2 + 7 = 9
two_sum([3, 2, 4], 6)        → [1, 2]   бо 2 + 4 = 6
two_sum([3, 3], 6)           → [0, 1]</pre>
                    <h4>Два підходи</h4>
                    <ul>
                        <li><b>в лоб</b> — два цикли один в одному, O(n²):
                        працює, але на 100 000 числах зачекаєшся;</li>
                        <li><b>через словник</b> — один прохід, O(n):
                        для кожного числа рахуємо, скільки йому бракує до
                        <code>target</code>, і питаємо словник, чи ми вже
                        бачили це доповнення.</li>
                    </ul>
                    <p>Саме другий підхід тут і потрібен — це той самий прийом,
                    який щодня використовують у реальному коді.</p>
                """,
                starter='''def two_sum(numbers, target):
    """Повертає [i, j] — індекси двох чисел, що в сумі дають target."""
    # твій код
''',
                checks=[
                    code("простий випадок",
                         "assert two_sum([2, 7, 11, 15], 9) == [0, 1]"),
                    code("пара не на початку списку",
                         "assert sorted(two_sum([3, 2, 4], 6)) == [1, 2]"),
                    code("два однакові числа",
                         "assert sorted(two_sum([3, 3], 6)) == [0, 1]"),
                    code("працює на довгому списку",
                         "assert sorted(two_sum(list(range(1000)), 1997)) == [998, 999]"),
                ],
                hints=[
                    hint("що шукати для кожного числа",
                         "Для числа value доповнення — це target - value. "
                         "Питання задачі: чи є воно вже в словнику (лівіше)? "
                         "Якщо так — це і є відповідь."),
                    hint("який словник вести",
                         "Словник value → index тих чисел, які вже пройшли. "
                         "Порядок важливий: спершу перевіряємо словник, і лише "
                         "потім додаємо поточне число — тоді одне й те саме "
                         "число не потрапить у пару двічі."),
                    solution('''def two_sum(numbers, target):
    seen = {}
    for index, value in enumerate(numbers):
        need = target - value
        if need in seen:
            return [seen[need], index]
        seen[value] = index
    return []'''),
                ],
            ),
            task(
                id="m3-lc-palindrome",
                title="Паліндром без зайвих символів",
                level="Легко",
                minutes=12,
                cheatsheet="strings",
                source="Valid Palindrome · LeetCode #125",
                source_url="https://leetcode.com/problems/valid-palindrome/",
                statement="""
                    <p>Паліндром — це текст, який читається однаково в обидва
                    боки. Але в реальних даних є коми, пробіли й великі літери,
                    які не мають заважати.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>is_palindrome(text)</code>, яка повертає
                    <code>True</code> або <code>False</code>, якщо:</p>
                    <ul>
                        <li>ігнорувати все, крім літер і цифр;</li>
                        <li>не зважати на великі й малі літери;</li>
                        <li>порожній рядок вважається паліндромом.</li>
                    </ul>
                    <pre>is_palindrome("A man, a plan, a canal: Panama")  → True
is_palindrome("race a car")                     → False
is_palindrome("А роза упала на лапу Азора")     → True</pre>
                    <h4>Тобі знадобиться</h4>
                    <ul>
                        <li><code>char.isalnum()</code> — чи це літера або
                        цифра (працює і для українських літер);</li>
                        <li><code>char.lower()</code> — привести до нижнього
                        регістру;</li>
                        <li><code>letters[::-1]</code> — перевернути список.</li>
                    </ul>
                    <p class="warn">Повертати треба саме <code>True</code>/
                    <code>False</code>, а не рядок чи число.</p>
                """,
                starter='''def is_palindrome(text):
    """True, якщо текст читається однаково в обидва боки (без розділових знаків)."""
    # твій код
''',
                checks=[
                    code("фраза з розділовими знаками",
                         'assert is_palindrome("A man, a plan, a canal: Panama") is True'),
                    code("не паліндром",
                         'assert is_palindrome("race a car") is False'),
                    code("порожній рядок",
                         "assert is_palindrome('') is True"),
                    code("працює з українськими літерами",
                         'assert is_palindrome("А роза упала на лапу Азора") is True'),
                    code("один символ",
                         'assert is_palindrome(" * ") is True'),
                ],
                hints=[
                    hint("з чого почати",
                         "Спершу «вичисти» рядок: залиш лише літери й цифри, "
                         "приведи все до нижнього регістру. Вийде список "
                         "символів — з ним уже просто."),
                    hint("як порівняти",
                         "Паліндром — це коли список символів дорівнює "
                         "самому собі, перевернутому: letters == letters[::-1]. "
                         "Це вже готовий bool, його й повертай."),
                    solution('''def is_palindrome(text):
    letters = [char.lower() for char in text if char.isalnum()]
    return letters == letters[::-1]'''),
                ],
            ),
            task(
                id="m3-lc-fizzbuzz",
                title="FizzBuzz: перевірка на подільність",
                level="Легко",
                minutes=12,
                cheatsheet="conditions",
                source="Fizz Buzz · LeetCode #412",
                source_url="https://leetcode.com/problems/fizz-buzz/",
                statement="""
                    <p>FizzBuzz — задача, яку дають на співбесіді, щоб побачити,
                    чи людина взагалі вміє писати код. Тут перевіряється
                    порядок умов — і саме на ньому найчастіше спотикаються.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>fizz_buzz(n)</code>, яка повертає
                    <b>список рядків</b> для чисел від 1 до <code>n</code>:</p>
                    <ul>
                        <li>ділиться на 3 і на 5 → <code>"FizzBuzz"</code></li>
                        <li>ділиться на 3 → <code>"Fizz"</code></li>
                        <li>ділиться на 5 → <code>"Buzz"</code></li>
                        <li>інакше — саме число, але <b>рядком</b></li>
                    </ul>
                    <pre>fizz_buzz(5) → ["1", "2", "Fizz", "4", "Buzz"]</pre>
                    <h4>Пастка, на якій падають</h4>
                    <p>Число 15 ділиться і на 3, і на 5. Якщо перевіряти
                    «на 3» першою — 15 ніколи не стане FizzBuzz. Тому
                    перевірка на 15 іде <b>першою</b>.</p>
                    <pre>if number % 15 == 0: ...</pre>
                    <p class="warn">Елементи списку — рядки, і для звичайних
                    чисел теж: <code>str(number)</code>, а не
                    <code>number</code>.</p>
                """,
                starter='''def fizz_buzz(n):
    """Повертає список рядків для чисел від 1 до n."""
    # твій код
''',
                checks=[
                    code("перші п'ять значень",
                         'assert fizz_buzz(5) == ["1", "2", "Fizz", "4", "Buzz"]'),
                    code("на 15 — FizzBuzz",
                         'assert fizz_buzz(15)[-1] == "FizzBuzz"'),
                    code("на 3 — Fizz",
                         'assert fizz_buzz(3)[2] == "Fizz"'),
                    code("один елемент",
                         'assert fizz_buzz(1) == ["1"]'),
                    code("довжина списку дорівнює n",
                         "assert len(fizz_buzz(30)) == 30"),
                    code("усі елементи — рядки",
                         'assert all(isinstance(item, str) for item in fizz_buzz(20))'),
                ],
                hints=[
                    hint("структура",
                         "Це цикл for по range(1, n + 1) і всередині — "
                         "ланцюжок if/elif/else. Результат збирай у список "
                         "через append."),
                    hint("порядок умов",
                         "Найспецифічніша умова йде першою: спочатку "
                         "number % 15 == 0, потім % 3, потім % 5, і аж тоді "
                         "else зі str(number)."),
                    solution('''def fizz_buzz(n):
    result = []
    for number in range(1, n + 1):
        if number % 15 == 0:
            result.append("FizzBuzz")
        elif number % 3 == 0:
            result.append("Fizz")
        elif number % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(number))
    return result'''),
                ],
            ),
            task(
                id="m3-lc-anagram",
                title="Анаграми: чи ті самі літери",
                level="Легко",
                minutes=10,
                cheatsheet="dicts",
                source="Valid Anagram · LeetCode #242",
                source_url="https://leetcode.com/problems/valid-anagram/",
                statement="""
                    <p>Анаграма — це слово, складене з тих самих літер:
                    <i>listen</i> і <i>silent</i>. Перевіряти це доводиться
                    часто — від ігор у слова до нормалізації назв у базах.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>is_anagram(first, second)</code>, яка
                    повертає <code>True</code>, якщо в обох рядках однакова
                    кількість кожної літери. Регістр і пробіли не
                    враховуй.</p>
                    <pre>is_anagram("listen", "silent")  → True
is_anagram("hello", "world")   → False
is_anagram("", "")             → True</pre>
                    <h4>Два способи</h4>
                    <ul>
                        <li><code>sorted(...)</code> — коротко: якщо
                        відсортовані літери однакові, то й набір літер
                        однаковий;</li>
                        <li>словник із підрахунком кожної літери — це вже
                        <b>O(n)</b> і саме те, що питають далі.</li>
                    </ul>
                """,
                starter='''def is_anagram(first, second):
    """True, якщо в обох рядках ті самі літери в тій самій кількості."""
    # твій код
''',
                checks=[
                    code("справжня анаграма",
                         'assert is_anagram("listen", "silent") is True'),
                    code("не анаграма",
                         'assert is_anagram("hello", "world") is False'),
                    code("регістр не заважає",
                         'assert is_anagram("Listen", "SILENT") is True'),
                    code("порожні рядки",
                         'assert is_anagram("", "") is True'),
                    code("працює з українськими словами",
                         'assert is_anagram("абетка", "бакета") is True'),
                    code("різна довжина",
                         'assert is_anagram("кот", "коти") is False'),
                ],
                hints=[
                    hint("найпростіший шлях",
                         "Приведи обидва рядки до нижнього регістру, прибери "
                         "пробіли (replace(\" \", \"\")) і порівняй відсортовані "
                         "списки символів: sorted(first) == sorted(second)."),
                    hint("швидший шлях",
                         "Порахуй літери у словник — або скористайся готовим "
                         "collections.Counter, він уміє порівнюватись "
                         "напряму: Counter(first) == Counter(second)."),
                    solution('''from collections import Counter


def is_anagram(first, second):
    first = first.lower().replace(" ", "")
    second = second.lower().replace(" ", "")
    return Counter(first) == Counter(second)'''),
                ],
            ),
            task(
                id="m3-lc-duplicate",
                title="Чи є повтори у списку",
                level="Легко",
                minutes=8,
                cheatsheet="dicts",
                source="Contains Duplicate · LeetCode #217",
                source_url="https://leetcode.com/problems/contains-duplicate/",
                statement="""
                    <p>Перевірка «чи не задублювались дані» трапляється постійно:
                    імпорт із CSV, список email-ів, ID із форми.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>has_duplicate(items)</code>, яка повертає
                    <code>True</code>, якщо хоч одне значення зустрічається
                    двічі або більше.</p>
                    <pre>has_duplicate([1, 2, 3, 1])  → True
has_duplicate([1, 2, 3, 4])  → False
has_duplicate([])            → False</pre>
                    <h4>Ідея</h4>
                    <p>Множина <code>set()</code> зберігає лише унікальні
                    значення. Якщо після перетворення довжина зменшилась —
                    щось повторювалось.</p>
                    <pre>len(set(items)) != len(items)</pre>
                    <p class="warn">Не роби подвійний цикл «кожне з кожним»:
                    для 10 000 елементів це 100 мільйонів порівнянь, а
                    множина впорається за один прохід.</p>
                """,
                starter='''def has_duplicate(items):
    """True, якщо в списку є хоч одне повторюване значення."""
    # твій код
''',
                checks=[
                    code("є повтор",
                         "assert has_duplicate([1, 2, 3, 1]) is True"),
                    code("усі різні",
                         "assert has_duplicate([1, 2, 3, 4]) is False"),
                    code("порожній список",
                         "assert has_duplicate([]) is False"),
                    code("працює з рядками",
                         'assert has_duplicate(["а", "б", "а"]) is True'),
                    code("швидко на великому списку — множина, а не цикли",
                         "assert has_duplicate(list(range(50000))) is False"),
                ],
                hints=[
                    hint("який інструмент",
                         "Множина зберігає тільки унікальні значення. "
                         "Порівняй її довжину з довжиною самого списку."),
                    hint("що повернути",
                         "Функція має повернути bool. Вираз "
                         "len(set(items)) != len(items) уже дає True або False "
                         "— його й повертай."),
                    solution('''def has_duplicate(items):
    return len(set(items)) != len(items)'''),
                ],
            ),
            task(
                id="m3-lc-move-zeroes",
                title="Перенести нулі в кінець (на місці)",
                level="Середньо",
                minutes=15,
                cheatsheet="lists",
                source="Move Zeroes · LeetCode #283",
                source_url="https://leetcode.com/problems/move-zeroes/",
                statement="""
                    <p>Тут з'являється нове поняття — <b>зміна списку на
                    місці</b>. Функція не повертає новий список, а
                    переставляє елементи в тому самому, який їй передали.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>move_zeroes(numbers)</code>: усі нулі
                    переїжджають у кінець списку, порядок решти чисел
                    зберігається.</p>
                    <pre>data = [0, 1, 0, 3, 12]
move_zeroes(data)
data   → [1, 3, 12, 0, 0]</pre>
                    <h4>Пастка</h4>
                    <p>Не можна робити <code>numbers = [...]</code> — це створить
                    <b>новий</b> список і забуде про старий. Треба
                    змінювати елементи за індексом: <code>numbers[i] = value</code>.</p>
                    <h4>Прийом «курсор запису»</h4>
                    <p>Тримай індекс <code>write</code> — куди покласти наступне
                    ненульове число. Пройди список один раз, складаючи туди все,
                    крім нулів. Потім решту списку заповни нулями.</p>
                    <p class="warn">Функція нічого не повертає — перевірка
                    дивитиметься на змінений список.</p>
                """,
                starter='''def move_zeroes(numbers):
    """Переносить нулі в кінець СПИСКУ, що переданий (на місці)."""
    # твій код
''',
                checks=[
                    code("нулі в кінці, порядок збережено",
                         "data = [0, 1, 0, 3, 12]\nmove_zeroes(data)\nassert data == [1, 3, 12, 0, 0]"),
                    code("самий нуль",
                         "data = [0]\nmove_zeroes(data)\nassert data == [0]"),
                    code("нулів немає",
                         "data = [1, 2]\nmove_zeroes(data)\nassert data == [1, 2]"),
                    code("самих нулів багато",
                         "data = [0, 0, 0, 7]\nmove_zeroes(data)\nassert data == [7, 0, 0, 0]"),
                    code("змінює той самий список, а не створює новий",
                         'data = [1, 0, 2]\nbefore = id(data)\nmove_zeroes(data)\nassert id(data) == before and data == [1, 2, 0]'),
                ],
                hints=[
                    hint("чому не працює простий варіант",
                         "Якщо написати numbers = [x for x in numbers if x] + "
                         "[0] * кількість_нулів — це НОВИЙ список, і зовні "
                         "нього ніхто не побачить. Потрібна зміна за індексом: "
                         "numbers[i] = ..."),
                    hint("прийом із двома індексами",
                         "Індекс write показує, куди класти наступне ненульове "
                         "число. Проходь список один раз: якщо value != 0 — "
                         "numbers[write] = value і write += 1. Наприкінці "
                         "заповни індекси від write до кінця нулями."),
                    solution('''def move_zeroes(numbers):
    write = 0
    for value in numbers:
        if value != 0:
            numbers[write] = value
            write += 1
    for index in range(write, len(numbers)):
        numbers[index] = 0'''),
                ],
            ),
            task(
                id="m3-lc-max-subarray",
                title="Максимальна сума підрядка (Kadane)",
                level="Складно",
                minutes=20,
                cheatsheet="algorithms",
                source="Maximum Subarray · LeetCode #53",
                source_url="https://leetcode.com/problems/maximum-subarray/",
                statement="""
                    <p>Задача з реального життя: є графік прибутку по днях, треба
                    знайти період із найбільшим сумарним прибутком. Це і є
                    «максимальний підсумок неперервного відрізка».</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>max_sum(numbers)</code>, яка повертає
                    найбільшу суму <b>неперервного</b> шматка списку.
                    Шматок не може бути порожнім, тому список з одного
                    від'ємного числа повертає це саме число.</p>
                    <pre>max_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])  → 6   (4 + -1 + 2 + 1)
max_sum([-1])                            → -1
max_sum([5, 4, -1, 7, 8])                → 23</pre>
                    <h4>Ідея алгоритму Кадане</h4>
                    <p>Йди по списку й тримай дві змінні:</p>
                    <ul>
                        <li><code>current</code> — найкраща сума, яка
                        <b>закінчується</b> на поточному елементі;</li>
                        <li><code>best</code> — найкраща сума, яку ми взагалі
                        бачили.</li>
                    </ul>
                    <pre>current = max(value, current + value)</pre>
                    <p>Ця одна строчка — уся суть: або починаємо шматок заново з
                    поточного числа, або продовжуємо попередній. Складність —
                    <b>O(n)</b>.</p>
                """,
                starter='''def max_sum(numbers):
    """Повертає максимальну суму неперервного шматка списку."""
    # твій код
''',
                checks=[
                    code("класичний випадок",
                         "assert max_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6"),
                    code("усі числа від'ємні",
                         "assert max_sum([-1]) == -1"),
                    code("працює без від'ємних",
                         "assert max_sum([5, 4, -1, 7, 8]) == 23"),
                    code("усі від'ємні, кілька чисел",
                         "assert max_sum([-2, -1, -3]) == -1"),
                    code("відрізок посередині",
                         "assert max_sum([-1, -1, 10, -1, -1]) == 10"),
                ],
                hints=[
                    hint("з чого почати",
                         "Наївний варіант — перебрати всі початки й кінці "
                         "(два цикли) і порахувати суми. Він пройде перевірки, "
                         "але це O(n²). Спершу зроби так, щоб зрозуміти "
                         "задачу."),
                    hint("крок до O(n)",
                         "Тримай current і best. Для кожного числа: "
                         "current = max(value, current + value) — або "
                         "починаємо новий шматок, або продовжуємо.\n"
                         "Далі best = max(best, current). Стартові значення "
                         "обох — перший елемент списку."),
                    solution('''def max_sum(numbers):
    best = current = numbers[0]
    for value in numbers[1:]:
        current = max(value, current + value)
        best = max(best, current)
    return best'''),
                ],
            ),
            task(
                id="m3-lc-reverse-words",
                title="Перевернути порядок слів",
                level="Середньо",
                minutes=12,
                cheatsheet="strings",
                source="Reverse Words in a String · LeetCode #151",
                source_url="https://leetcode.com/problems/reverse-words-in-a-string/",
                statement="""
                    <p>Слова — це найчастіша одиниця, з якою працюють у тексті.
                    Тут важливо навчитись отримувати слова без зайвих
                    пробілів.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>reverse_words(text)</code>: порядок слів
                    змінюється на зворотний, а між словами рівно <b>один</b>
                    пробіл (без пробілів на початку й у кінці).</p>
                    <pre>reverse_words("the sky is blue")   → "blue is sky the"
reverse_words("  hello   world  ") → "world hello"
reverse_words("a")                 → "a"</pre>
                    <h4>Підказка до інструментів</h4>
                    <p><code>text.split()</code> без аргументів — чарівний:
                    він ріже по будь-якій кількості пробілів і сам прибирає
                    порожні шматки. А <code>" ".join(слова)</code> збирає
                    назад.</p>
                    <p class="warn">Тому <code>split(" ")</code> (з пробілом
                    усередині) тут дасть порожні рядки — це найчастіша
                    помилка.</p>
                """,
                starter='''def reverse_words(text):
    """Повертає той самий текст, але слова у зворотному порядку."""
    # твій код
''',
                checks=[
                    code("проста фраза",
                         'assert reverse_words("the sky is blue") == "blue is sky the"'),
                    code("зайві пробіли",
                         'assert reverse_words("  hello   world  ") == "world hello"'),
                    code("одне слово",
                         'assert reverse_words("a") == "a"'),
                    code("порожній рядок",
                         'assert reverse_words("   ") == ""'),
                    code("українською",
                         'assert reverse_words("я вчу пайтон") == "пайтон вчу я"'),
                ],
                hints=[
                    hint("що робить split()",
                         "text.split() без аргументів ріже рядок по будь-яких "
                         "пробілах і не створює порожніх рядків для повторних "
                         "пробілів. Це саме те, що потрібно."),
                    hint("як перевернути",
                         "Перевернути список слів можна зрізом: "
                         "words[::-1] або list(reversed(words)). Далі "
                         '" ".join(...) збирає рядок із потрібними пробілами.'),
                    solution('''def reverse_words(text):
    words = text.split()
    return " ".join(reversed(words))'''),
                ],
            ),
            task(
                id="m3-lc-roman",
                title="Римські числа у звичайні",
                level="Середньо",
                minutes=15,
                cheatsheet="dicts",
                source="Roman to Integer · LeetCode #13",
                source_url="https://leetcode.com/problems/roman-to-integer/",
                statement="""
                    <p>Римські числа досі трапляються в даних: номери томів,
                    розділів, copyright на сайтах. Заодно це чудова практика
                    на словник і «хитру» логіку.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>roman_to_int(roman)</code>, яка
                    перетворює римське число на звичайне.</p>
                    <pre>roman_to_int("III")     → 3
roman_to_int("LVIII")   → 58
roman_to_int("MCMXCIV") → 1994</pre>
                    <h4>Правило віднімання</h4>
                    <p>Зазвичай значення літер додаються зліва направо. Але якщо
                    літера <b>менша</b> за наступну — її треба
                    <b>відняти</b>: в «IV» одиниця стоїть перед п'ятіркою,
                    тому 5 − 1 = 4.</p>
                    <pre>if current &lt; next:  total -= current
else:               total += current</pre>
                    <p>Тобто достатньо дивитись на поточну літеру й наступну —
                    і весь алгоритм уміщається в один цикл.</p>
                """,
                starter='''VALUES = {"I": 1, "V": 5, "X": 10, "L": 50,
          "C": 100, "D": 500, "M": 1000}


def roman_to_int(roman):
    """Перетворює римське число у звичайне."""
    # твій код
''',
                checks=[
                    code("прості одиниці",
                         'assert roman_to_int("III") == 3'),
                    code("з відніманням на кінці",
                         'assert roman_to_int("LVIII") == 58'),
                    code("класичний приклад із сайту",
                         'assert roman_to_int("MCMXCIV") == 1994'),
                    code("число без віднімань",
                         'assert roman_to_int("MMXXVI") == 2026'),
                    code("один символ",
                         'assert roman_to_int("V") == 5'),
                ],
                hints=[
                    hint("що дано в заготовці",
                         "Словник VALUES уже є — ним і користуйся. "
                         "Для літери roman[i] значення це VALUES[roman[i]]."),
                    hint("як врахувати правило віднімання",
                         "У циклі візьми поточне значення value. "
                         "Якщо це не останній символ і value менше за значення "
                         "НАСТУПНОГО символу — віднімай, інакше додавай. "
                         "Для «наступного» використай enumerate, щоб знати "
                         "індекс."),
                    solution('''VALUES = {"I": 1, "V": 5, "X": 10, "L": 50,
          "C": 100, "D": 500, "M": 1000}


def roman_to_int(roman):
    total = 0
    for index, letter in enumerate(roman):
        value = VALUES[letter]
        if index + 1 < len(roman) and value < VALUES[roman[index + 1]]:
            total -= value
        else:
            total += value
    return total'''),
                ],
            ),
            task(
                id="m3-lc-missing-number",
                title="Якого числа бракує",
                level="Легко",
                minutes=12,
                cheatsheet="numbers",
                source="Missing Number · LeetCode #268",
                source_url="https://leetcode.com/problems/missing-number/",
                statement="""
                    <p>Типова перевірка цілісності даних: є номери від 0 до n,
                    але одне число загубилось при імпорті. Треба знайти, яке.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>missing_number(numbers)</code>. У списку
                    лежать <b>усі</b> числа від 0 до <code>n</code>, крім
                    одного (довжина списку — це і є <code>n</code>). Поверни
                    те, яке загубилось.</p>
                    <pre>missing_number([3, 0, 1])                → 2
missing_number([0, 1])                   → 2
missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) → 8</pre>
                    <h4>Два підходи</h4>
                    <ul>
                        <li>множина: пройтись по range(n + 1) і знайти те, чого
                        немає в set(numbers) — зрозуміло й швидко;</li>
                        <li>математика: сума всіх чисел від 0 до n дорівнює
                        <code>n * (n + 1) // 2</code>. Відніми від неї суму
                        списку — і отримаєш те, що загубилось. O(1) пам'яті.</li>
                    </ul>
                """,
                starter='''def missing_number(numbers):
    """Повертає число з діапазону 0..n, якого немає у списку."""
    # твій код
''',
                checks=[
                    code("класичний випадок",
                         "assert missing_number([3, 0, 1]) == 2"),
                    code("загубилось останнє число",
                         "assert missing_number([0, 1]) == 2"),
                    code("довгий список",
                         "assert missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8"),
                    code("список з одного нуля",
                         "assert missing_number([0]) == 1"),
                    code("загубився нуль",
                         "assert missing_number([1, 2, 3]) == 0"),
                ],
                hints=[
                    hint("спосіб із множиною",
                         "Пройди циклом по range(len(numbers) + 1) і поверни "
                         "перше число, якого немає в set(numbers). Це "
                         "найзрозуміліший варіант."),
                    hint("спосіб із математикою",
                         "n = len(numbers). Сума 0+1+...+n = n * (n + 1) // 2. "
                         "Відніми sum(numbers) — і отримаєш пропущене число."),
                    solution('''def missing_number(numbers):
    n = len(numbers)
    return n * (n + 1) // 2 - sum(numbers)'''),
                ],
            ),
            task(
                id="m3-lc-brackets",
                title="Перевірка дужок (стек)",
                level="Складно",
                minutes=20,
                cheatsheet="algorithms",
                source="Valid Parentheses · LeetCode #20",
                source_url="https://leetcode.com/problems/valid-parentheses/",
                statement="""
                    <p>Перша задача, де потрібна структура даних «стек» —
                    хоча це просто список, у який кладуть і з якого забирають
                    з одного кінця. Такі самі перевірки роблять парсери HTML,
                    JSON і компілятори.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>is_valid(text)</code>, яка повертає
                    <code>True</code>, якщо всі дужки закриті правильно й у
                    правильному порядку. Розглядаємо три види:
                    <code>()</code>, <code>[]</code>, <code>{}</code>.</p>
                    <pre>is_valid("()[]{}")  → True
is_valid("(]")      → False
is_valid("([)]")    → False   ← порядок не той
is_valid("{[]}")    → True</pre>
                    <h4>Алгоритм</h4>
                    <ol>
                        <li>зустріли відкриту дужку — поклали в стек
                        (<code>stack.append(char)</code>);</li>
                        <li>зустріли закриту — забрали верхню зі стека
                        (<code>stack.pop()</code>) і перевірили, що вона
                        правильного типу;</li>
                        <li>у кінці стек мусить бути порожній.</li>
                    </ol>
                    <p class="warn">Перевіряй <code>if not stack</code> перед
                    <code>pop()</code> — інакше на рядку «)» буде IndexError.</p>
                """,
                starter='''PAIRS = {")": "(", "]": "[", "}": "{"}


def is_valid(text):
    """True, якщо дужки закриті правильно."""
    # твій код
''',
                checks=[
                    code("різні види дужок",
                         'assert is_valid("()[]{}") is True'),
                    code("неправильна пара",
                         'assert is_valid("(]") is False'),
                    code("неправильний порядок",
                         'assert is_valid("([)]") is False'),
                    code("вкладені дужки",
                         'assert is_valid("{[]}") is True'),
                    code("порожній рядок",
                         'assert is_valid("") is True'),
                    code("зайва закриваюча",
                         'assert is_valid(")") is False'),
                    code("незакрита відкриваюча",
                         'assert is_valid("(()") is False'),
                ],
                hints=[
                    hint("що таке стек",
                         "Звичайний список: додаєш у кінець через append і "
                         "забираєш з кінця через pop. Остання відкрита дужка "
                         "має закритись першою — саме це стек і забезпечує."),
                    hint("порядок перевірок",
                         "Для кожної літери: якщо вона у \"([{\" — у стек. "
                         "Якщо у PAIRS — спершу перевір, що стек не порожній, "
                         "потім pop() і порівняй із PAIRS[char]. Наприкінці "
                         "поверни not stack."),
                    solution('''PAIRS = {")": "(", "]": "[", "}": "{"}


def is_valid(text):
    stack = []
    for char in text:
        if char in "([{":
            stack.append(char)
        elif char in PAIRS:
            if not stack or stack.pop() != PAIRS[char]:
                return False
    return not stack'''),
                ],
            ),
            task(
                id="m3-cw-two-smallest",
                title="Codewars: сума двох найменших",
                level="Легко",
                minutes=10,
                cheatsheet="lists",
                source="Sum of two lowest positive integers · Codewars (7 kyu)",
                source_url="https://www.codewars.com/kata/558fc85d8fd1938afb000014",
                statement="""
                    <p>Задача з Codewars рівня 7 kyu — саме той рівень, з якого
                    варто починати, коли зареєструєшся на платформі. Умова
                    коротка, і перевіряється нею насамперед розуміння
                    сортування.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>sum_two_smallest(numbers)</code>, яка
                    повертає <b>суму двох найменших</b> чисел зі списку
                    (мінімум 4 числа, усі додатні).</p>
                    <pre>sum_two_smallest([19, 5, 42, 2, 77]) → 7    (2 + 5)
sum_two_smallest([5, 4, 3, 2, 1])    → 3    (1 + 2)</pre>
                    <h4>Не забудь про ефективність</h4>
                    <p>Сортувати весь список (O(n log n)) — нормально. Але
                    якщо список величезний, а потрібні лише два найменші,
                    дешевше пройти його один раз. Про це гарно згадати
                    на співбесіді.</p>
                """,
                starter='''def sum_two_smallest(numbers):
    """Повертає суму двох найменших чисел списку."""
    # твій код
''',
                checks=[
                    code("звичайний список",
                         "assert sum_two_smallest([19, 5, 42, 2, 77]) == 7"),
                    code("великі числа",
                         "assert sum_two_smallest([10, 343445353, 3453445, 3453545353453]) == 3453455"),
                    code("найменші в кінці",
                         "assert sum_two_smallest([5, 4, 3, 2, 1]) == 3"),
                    code("однакові найменші",
                         "assert sum_two_smallest([2, 2, 9, 9]) == 4"),
                ],
                hints=[
                    hint("найкоротший шлях",
                         "Відсортуй список і візьміть перші два елементи: "
                         "sorted(numbers)[:2], і сумуй їх через sum()."),
                    hint("без сортування всього списку",
                         "Можна скористатись heapq.nsmallest(2, numbers) — "
                         "це швидше на великих списках, бо не сортує все. "
                         "Або пройти циклом і тримати дві змінні."),
                    solution('''def sum_two_smallest(numbers):
    smallest = sorted(numbers)[:2]
    return smallest[0] + smallest[1]'''),
                ],
            ),
            task(
                id="m3-cw-vowels",
                title="Codewars: скільки голосних",
                level="Легко",
                minutes=8,
                cheatsheet="loops",
                source="Vowel Count · Codewars (7 kyu)",
                source_url="https://www.codewars.com/kata/54ff3102c1bad923760001f3",
                statement="""
                    <p>Ще одна класична задача Codewars (7 kyu) — на цикл і
                    перевірку входження. Такі підрахунки трапляються в
                    аналізі тексту й у валідації даних.</p>
                    <h4>Що треба зробити</h4>
                    <p>Напиши <code>count_vowels(text)</code>, яка рахує
                    кількість голосних у рядку. Голосні —
                    <code>a e i o u</code> (українські літери не рахуємо,
                    <code>y</code> — теж ні).</p>
                    <pre>count_vowels("abracadabra") → 5
count_vowels("AEIOU")       → 5
count_vowels("rhythm")      → 0</pre>
                    <h4>Дві ідеї</h4>
                    <ul>
                        <li>цикл із лічильником — класика для початківця;</li>
                        <li>сума генератора в один рядок:
                        <code>sum(1 for char in text.lower() if char in "aeiou")</code>
                        — те саме, але коротко.</li>
                    </ul>
                    <p class="warn">Не забудь привести текст до нижнього
                    регістру, інакше <code>"AEIOU"</code> дасть 0.</p>
                """,
                starter='''def count_vowels(text):
    """Повертає кількість голосних a, e, i, o, u у тексті."""
    # твій код
''',
                checks=[
                    code("слово з п'ятьма голосними",
                         'assert count_vowels("abracadabra") == 5'),
                    code("великі літери",
                         'assert count_vowels("AEIOU") == 5'),
                    code("порожній рядок",
                         'assert count_vowels("") == 0'),
                    code("без голосних",
                         'assert count_vowels("rhythm") == 0'),
                    code("фраза з пробілами",
                         'assert count_vowels("The quick brown fox") == 5'),
                ],
                hints=[
                    hint("як порахувати",
                         "Заведи змінну-лічильник = 0 і цикл for по літерах "
                         "рядка. Якщо літера у \"aeiou\" — збільшуй "
                         "лічильник на 1."),
                    hint("коротший варіант",
                         "Генератор усередині sum(): "
                         "sum(1 for char in text.lower() if char in \"aeiou\"). "
                         "Це той самий цикл, лише в один рядок."),
                    solution('''def count_vowels(text):
    return sum(1 for char in text.lower() if char in "aeiou")'''),
                ],
            ),
        ),
        topic(
            "Налагодження: знайди й виправ баги",
            *DEBUG_TASKS,
        ),
        topic(
            "Робота з кодом як у команді",
            stub("m3-git-branch", "Гілки та merge у Git"),
            stub("m3-github", "Перший проєкт на GitHub з гарним README"),
            stub("m3-docs", "Читання офіційної документації"),
        ),
    ),
)
