"""Розбір коду користувача: що в ньому не так — і що зроблено добре.

Тренажер перевіряє, чи код працює. Але «працює» і «читається» — різні речі:
`for i in range(len(items))` працює, а `for item in items` читається. Уміння
писати код, який зрозуміє інший (і ти сам за тиждень), — саме те, за що
платять на фрілансі, тому цю навичку треба тренувати, а не лише ловити
AssertionError.

Модуль читає код як уважний колега: не переписує його і не прискіпується до
дрібниць. Правила — це те, на чому справді спотикаються новачки: змінна, яку
ніхто не читає, `== None`, ковтання помилок, чотири поверхи `if`, файл без
`with`, імена не за домовленістю Python.

Тут немає ні Qt, ні знання про задачі: на вході — текст коду, на виході —
`CodeReview` з `Remark`. Тому кожне правило перевіряється тестами буквально
рядком коду.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

# Скільки зауважень показувати за раз: шість виправлень — це вже робота на
# вечір, а двадцять нарікань не читає ніхто
MAX_REMARKS = 6
# З якого рівня вкладеності if/for/while починається лабіринт
DEEP_NESTING = 4
# Скільки рядків у функції — уже забагато
LONG_FUNCTION = 25
# Скільки разів має повторитись одне й те саме число чи рядок, щоб стати константою
REPEATED_LITERAL = 3

ADVICE = "порада"
PRAISE = "добре"

NO_REMARKS = "Жодних зауважень — код читається легко. Так тримати!"
STARTER_REVIEW = (
    "Це ще заготовка задачі — напиши свій код, і я його розберу. Розбирати "
    "чужий каркас немає сенсу: у ньому все «не використовується»."
)
NOT_REVIEWED = (
    "Натисни «Розібрати код» — і я скажу, що в ньому не так (і що зроблено "
    "добре). Це не оцінка: тести перевіряють, чи код працює, а розбір — чи "
    "його зрозуміє інша людина."
)

_FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
_BLOCK_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With)


@dataclass(frozen=True)
class Remark:
    """Одне зауваження (або похвала) до коду."""

    kind: str                    # ключ правила: "unused-name", "praise-names", …
    title: str                   # що саме помітили
    advice: str                  # що з цим робити
    line: int = 0                # рядок у файлі користувача (0 — йдеться про весь код)
    severity: str = ADVICE

    @property
    def is_praise(self) -> bool:
        return self.severity == PRAISE


@dataclass(frozen=True)
class CodeReview:
    """Розбір коду: зауваження, похвала й короткий підсумок для панелі."""

    remarks: tuple[Remark, ...] = ()
    summary: str = NOT_REVIEWED

    @property
    def issues(self) -> tuple[Remark, ...]:
        return tuple(remark for remark in self.remarks if not remark.is_praise)

    @property
    def praises(self) -> tuple[Remark, ...]:
        return tuple(remark for remark in self.remarks if remark.is_praise)

    @property
    def ok(self) -> bool:
        """Зауважень немає (похвала не заважає — це не зауваження)."""
        return not self.issues


EMPTY_REVIEW = CodeReview()


def issues_phrase(count: int) -> str:
    """«1 зауваження», «3 зауваження», «7 зауважень» — щоб текст не різав око."""
    few = count % 10 in (1, 2, 3, 4) and count % 100 not in (11, 12, 13, 14)
    return f"{count} зауваження" if few else f"{count} зауважень"


# --------------------------------------------------------------------------
# дрібні помічники, спільні для правил
# --------------------------------------------------------------------------


def _calls(node: ast.AST, name: str) -> bool:
    """Чи це виклик функції з такою назвою: `open(...)`, `len(...)`."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    )


def _names_used(tree: ast.AST) -> set[str]:
    """Усі імена, які код десь читає (навіть у вкладеній функції)."""
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


def _assign_targets(tree: ast.AST) -> list[ast.Name]:
    """Змінні, яким щось присвоюють (не цілі циклів: про них говорить своє правило)."""
    targets: list[ast.Name] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = node.value
            if value is None:                       # `x: int` без значення
                continue
            for target in ([node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign))
                           else node.targets):
                targets.extend(
                    inner for inner in ast.walk(target) if isinstance(inner, ast.Name)
                )
        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    targets.extend(
                        inner for inner in ast.walk(item.optional_vars)
                        if isinstance(inner, ast.Name)
                    )
    return targets


_TO_SNAKE = re.compile(r"(?<!^)(?=[A-Z])")


def _is_camel(name: str) -> bool:
    """`totalSum`, `AvgOfMarks` — але не `MAX_SIZE` і не `_private`."""
    if name.startswith("_") or name.isupper():
        return False
    return any(character.isupper() for character in name[1:])


def _snake(name: str) -> str:
    return _TO_SNAKE.sub("_", name).lower()


# --------------------------------------------------------------------------
# правила
# --------------------------------------------------------------------------


def _unused_names(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Присвоєння, яке ніхто не читає: `total = 0` і жодного `total` далі."""
    used = _names_used(tree) | keep
    remarks: list[Remark] = []
    seen: set[str] = set()

    for target in _assign_targets(tree):
        name = target.id
        if name in used or name in seen or name.startswith("_"):
            continue
        seen.add(name)
        remarks.append(Remark(
            kind="unused-name",
            title=f"`{name}` ніде не використовується",
            advice=(
                "Прибери цей рядок або доведи роботу до кінця: зайва змінна "
                "змушує читача шукати, де вона мала б використатись. Якщо "
                "значення не потрібне — його не варто й рахувати."
            ),
            line=target.lineno,
        ))
    return remarks


def _unused_imports(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """`import math` і жодного `math.` далі — імпорт обіцяє те, чого немає."""
    bound: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound.setdefault(alias.asname or alias.name.split(".")[0], node)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    return []      # `from x import *` — не вгадуємо, що звідти взялось
                bound.setdefault(alias.asname or alias.name, node)

    used = _names_used(tree) | keep
    return [
        Remark(
            kind="unused-import",
            title=f"Імпорт `{name}` не використовується",
            advice=(
                "Прибери рядок. Зайвий імпорт — це обіцянка, яку код не "
                "виконує: читач шукає модуль, а його ніде немає."
            ),
            line=node.lineno,
        )
        for name, node in bound.items()
        if name not in used and not name.startswith("_")
    ]


def _naming(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Імена: у Python прийнято snake_case, а функція `f` не розповідає нічого."""
    remarks: list[Remark] = []

    def complain(name: str, node: ast.AST, what: str) -> None:
        remarks.append(Remark(
            kind="naming",
            title=f"{what} `{name}` названо не за домовленістю Python",
            advice=(
                f"У Python прийнято snake_case — `{_snake(name)}`. Так код "
                "виглядає однаково у всіх проєктах, і чуже око читає його без "
                "звикання."
            ),
            line=getattr(node, "lineno", 0),
        ))

    for node in ast.walk(tree):
        if isinstance(node, _FUNCTION_NODES):
            if _is_camel(node.name):
                complain(node.name, node, "функцію")
            elif len(node.name) == 1:
                remarks.append(Remark(
                    kind="short-function-name",
                    title=f"функція `{node.name}` — це не назва",
                    advice=(
                        "Назва функції — це дієслово, яке описує результат: "
                        "`average_marks`, `print_total`. Однолітерні назви "
                        "годяться лише для змінних у циклі."
                    ),
                    line=node.lineno,
                ))
            for argument in (
                list(node.args.posonlyargs) + list(node.args.args)
                + list(node.args.kwonlyargs)
                + ([node.args.vararg] if node.args.vararg else [])
                + ([node.args.kwarg] if node.args.kwarg else [])
            ):
                if _is_camel(argument.arg):
                    complain(argument.arg, argument, "параметр")
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if _is_camel(node.id):
                complain(node.id, node, "змінну")
    return remarks


def _range_len(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """`for i in range(len(items))` — довший шлях, ніж показує Python.

    Саме `range(len(...))` і `range(0, len(...))`: цикл від якогось іншого
    числа (наприклад `range(start, len(items))`) — це вже робота з індексами,
    а не спроба обійти список.
    """
    remarks: list[Remark] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Name):
            continue
        if not _calls(node.iter, "range"):
            continue
        arguments = node.iter.args
        if not arguments or not _calls(arguments[0], "len"):
            starts_at_zero = (
                isinstance(arguments[0], ast.Constant) and arguments[0].value == 0
            )
            if not (starts_at_zero and len(arguments) > 1
                    and _calls(arguments[1], "len")):
                continue
        index = node.target.id
        remarks.append(Remark(
            kind="range-len",
            title=f"`for {index} in range(len(...))` — довший шлях, ніж треба",
            advice=(
                "Потрібен сам елемент — `for item in items:`; потрібні і номер, "
                f"і елемент — `for {index}, item in enumerate(items):`. Так код "
                "читається як речення, а не як адреси в пам'яті."
            ),
            line=node.lineno,
        ))
    return remarks


def _comparisons(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """`== True`, `!= None` — порівняння, які роблять не те, що здається."""
    advice_by_case = {
        (True, "eq"): "Напиши просто умову: `if умова:` — True і так істинне.",
        (True, "ne"): "Напиши `if not умова:` — зайве порівняння з True плутає.",
        (False, "eq"): "Напиши `if not умова:` — False і так хибне.",
        (False, "ne"): "Напиши `if умова:` — зайве порівняння з False плутає.",
        (None, "eq"): "Для None є `is`: `if value is None:`.",
        (None, "ne"): "Для None є `is not`: `if value is not None:`.",
    }

    remarks: list[Remark] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        pairs = zip([node.left, *node.comparators[:-1]], node.ops, node.comparators)
        for _left, operator, right in pairs:
            if not isinstance(right, ast.Constant):
                continue
            value = right.value
            # саме identity: `0 == False` і `1 == True`, тому `in` тут не годиться
            if value is not True and value is not False and value is not None:
                continue
            kind = "eq" if isinstance(operator, ast.Eq) else \
                "ne" if isinstance(operator, ast.NotEq) else None
            if kind is None:
                continue
            advice = advice_by_case[(value, kind)]
            shown = {True: "True", False: "False", None: "None"}[value]
            operator_text = "==" if kind == "eq" else "!="
            remarks.append(Remark(
                kind="compare-to-literal",
                title=f"Порівняння з `{shown}` через `{operator_text}`",
                advice=advice,
                line=node.lineno,
            ))
    return remarks


def _bare_except(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """`except:` і `except Exception: pass` — так помилка зникає разом із багом."""
    remarks: list[Remark] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        swallows = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
        if node.type is None:
            remarks.append(Remark(
                kind="bare-except",
                title="`except:` без типу ловить усе — навіть помилку в собі",
                advice=(
                    "Лови конкретне: `except ValueError:`. Голий `except` "
                    "перехоплює й друкарські помилки у твоєму ж коді, тому "
                    "баг перетворюється на загадку."
                ),
                line=node.lineno,
            ))
        elif swallows:
            remarks.append(Remark(
                kind="silent-except",
                title="Помилку спіймано й мовчки проковтнуто (`pass`)",
                advice=(
                    "Якщо код справді має продовжити — скажи про це вголос: "
                    '`print("не вдалось прочитати файл")`. Мовчазний `pass` '
                    "ховає проблему доти, доки вона не стане більшою."
                ),
                line=node.lineno,
            ))
    return remarks


def _open_without_with(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Файл, відкритий без `with`, лишається відкритим до кінця програми."""
    in_with = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        for item in node.items
        for inner in ast.walk(item.context_expr)
    }

    remarks: list[Remark] = []
    seen_lines: set[int] = set()
    for node in ast.walk(tree):
        if not _calls(node, "open") or id(node) in in_with or node.lineno in seen_lines:
            continue
        seen_lines.add(node.lineno)
        remarks.append(Remark(
            kind="open-without-with",
            title="Файл відкрито без `with`",
            advice=(
                "`with open(...) as f:` закриває файл сам — навіть якщо "
                "посеред роботи станеться помилка. Без `with` файл лишається "
                "відкритим, і на Windows це згодом заважає його "
                "перейменувати, скопіювати чи видалити."
            ),
            line=node.lineno,
        ))
    return remarks


def _first_deep_statement(statements: list[ast.stmt], level: int) -> ast.stmt | None:
    """Перший блок глибше за DEEP_NESTING.

    У `ast` гілка `else` — це список операторів, а `elif` — той самий `if`
    усередині `orelse`. Тому ланцюжок `if/elif/elif` — це один поверх, а не
    чотири: інакше найзвичайніший калькулятор виглядав би лабіринтом.
    """
    for statement in statements:
        if isinstance(statement, _FUNCTION_NODES):
            found = _first_deep_statement(statement.body, 1)
            if found is not None:
                return found
            continue
        if isinstance(statement, ast.Match):
            for case in statement.cases:
                found = _first_deep_statement(case.body, level + 1)
                if found is not None:
                    return found
            continue
        if not isinstance(statement, _BLOCK_NODES):
            continue
        if level >= DEEP_NESTING:
            return statement

        found = _first_deep_statement(statement.body, level + 1)
        if found is not None:
            return found

        orelse = list(getattr(statement, "orelse", []))
        is_elif = (
            isinstance(statement, ast.If)
            and len(orelse) == 1
            and isinstance(orelse[0], ast.If)
        )
        found = _first_deep_statement(orelse, level if is_elif else level + 1)
        if found is not None:
            return found

        if isinstance(statement, ast.Try):
            for handler in statement.handlers:
                found = _first_deep_statement(handler.body, level + 1)
                if found is not None:
                    return found
            found = _first_deep_statement(statement.finalbody, level + 1)
            if found is not None:
                return found
    return None


def _deep_nesting(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Чотири поверхи `if`/`for` — це вже лабіринт, а не логіка."""
    block = _first_deep_statement(tree.body, 1)
    if block is None:
        return []
    return [Remark(
        kind="deep-nesting",
        title=f"Вкладеність {DEEP_NESTING} рівнів — тут легко загубитись",
        advice=(
            "Винеси внутрішній блок у функцію з назвою: замість четвертого "
            "поверху `if` — `if student_passed(marks):`. Кожна функція тоді "
            "читається як один абзац."
        ),
        line=block.lineno,
    )]


def _repeated_literals(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Однакове число чи рядок у коді — це вже константа, якій бракує назви."""
    buckets: dict[object, list[ast.Constant]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
            continue
        value = node.value
        # маленькі числа та круглі десятки самі собою зрозумілі: `// 100` —
        # це розряди числа, а не магія; скаржитись на них — шум
        if isinstance(value, int) and (abs(value) < 3 or abs(value) in (10, 100, 1000)):
            continue
        if isinstance(value, float) and abs(value) in (0.0, 1.0):
            continue
        if isinstance(value, str) and len(value.strip()) < 2:
            continue
        if isinstance(value, (int, float, str)):
            buckets.setdefault(value, []).append(node)

    remarks: list[Remark] = []
    for value, nodes in buckets.items():
        if len(nodes) < REPEATED_LITERAL:
            continue
        shown = f'"{value}"' if isinstance(value, str) else str(value)
        remarks.append(Remark(
            kind="repeated-literal",
            title=f"{shown} повторюється {len(nodes)} рази",
            advice=(
                "Дай цьому значенню назву в одному місці (наприклад "
                "`max_marks = 5`) і посилайся на неї. Тоді в коді буде видно "
                "задум, а щоб змінити число — не доведеться шукати його по "
                "всьому файлу."
            ),
            line=nodes[0].lineno,
        ))
    return remarks


def _long_functions(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """Функція на три екрани — це вже не функція, а програма."""
    remarks: list[Remark] = []
    for node in ast.walk(tree):
        if not isinstance(node, _FUNCTION_NODES):
            continue
        length = (node.end_lineno or node.lineno) - node.lineno + 1
        if length < LONG_FUNCTION:
            continue
        remarks.append(Remark(
            kind="long-function",
            title=f"Функція `{node.name}` розтягнулась на {length} рядків",
            advice=(
                "Розбий її на кроки з назвами — так само, як ти розповідав би "
                "цей алгоритм уголос: «зібрати оцінки», «порахувати середнє», "
                "«надрукувати звіт». Кожен крок стає функцією на 5–10 рядків."
            ),
            line=node.lineno,
        ))
    return remarks


def _constant_return(body: list[ast.stmt]) -> bool | None:
    """`return True` — і нічого більше (None, якщо тіло складніше)."""
    if len(body) != 1 or not isinstance(body[0], ast.Return):
        return None
    value = body[0].value
    if isinstance(value, ast.Constant) and value.value in (True, False):
        return bool(value.value)
    return None


def _boolean_returns(tree: ast.AST, keep: set[str]) -> list[Remark]:
    """`if умова: return True else: return False` — це просто `return умова`."""
    remarks: list[Remark] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not node.orelse:
            continue
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            continue          # elif — це продовження ланцюжка, не пара True/False
        when_true = _constant_return(node.body)
        when_false = _constant_return(node.orelse)
        if when_true is None or when_false is None or when_true == when_false:
            continue
        remarks.append(Remark(
            kind="boolean-return",
            title="Пара `return True` / `return False` навколо умови",
            advice=(
                "Напиши `return умова` — воно й так дає True або False."
                if when_true else
                "Напиши `return not умова` — інвертувати в return коротше, "
                "ніж описувати дві гілки."
            ),
            line=node.lineno,
        ))
    return remarks


def _praises(tree: ast.AST, code: str) -> list[Remark]:
    """Одна похвала за те, що вже зроблено як у справжніх проєктах.

    Похвала потрібна не для настрою: вона показує, який саме звичний прийом
    людина вже засвоїла, щоб вона впізнавала його й далі.
    """
    functions = [node for node in ast.walk(tree) if isinstance(node, _FUNCTION_NODES)]
    documented = [node for node in functions if ast.get_docstring(node)]
    if documented:
        return [Remark(
            kind="praise-docstring",
            severity=PRAISE,
            title=f"`{documented[0].name}` описана в рядку документації",
            advice=(
                "Так роблять у справжніх проєктах: через місяць цей опис "
                "згадає за тебе, що функція робить."
            ),
            line=documented[0].lineno,
        )]

    if functions and all(
        len(node.name) >= 4 and node.name.islower() for node in functions
    ):
        return [Remark(
            kind="praise-names",
            severity=PRAISE,
            title="Функції названі зрозуміло",
            advice=(
                "Назви на кшталт `average_marks` читаються без коду — це "
                "головна ознака коду, який легко підтримувати."
            ),
            line=functions[0].lineno,
        )]

    opens = [node for node in ast.walk(tree) if _calls(node, "open")]
    in_with = {
        id(inner)
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        for item in node.items
        for inner in ast.walk(item.context_expr)
    }
    if opens and all(id(node) in in_with for node in opens):
        return [Remark(
            kind="praise-with",
            severity=PRAISE,
            title="Файл відкривається через `with`",
            advice=(
                "Це найкоротший шлях до безпечної роботи з файлами: файл "
                "закриється сам, навіть якщо всередині станеться помилка."
            ),
            line=0,
        )]
    return []


# Порядок правил = порядок показу, коли зауваження в одному рядку.
RULES: tuple[Callable[[ast.AST, set[str]], list[Remark]], ...] = (
    _unused_imports,
    _unused_names,
    _range_len,
    _comparisons,
    _bare_except,
    _open_without_with,
    _deep_nesting,
    _repeated_literals,
    _boolean_returns,
    _long_functions,
    _naming,
)


def _sort_key(remark: Remark) -> tuple[int, int]:
    """Спершу зауваження з рядками (за порядком у файлі), потім решта."""
    return (1 if remark.line else 0, remark.line)


def names_used_in(snippets: Iterable[str]) -> set[str]:
    """Імена, які згадуються в шматках коду (наприклад у прихованих перевірках).

    Навіщо: тренажер бачить лише те, що в редакторі, а перевірки виконуються в
    тому ж файлі. Тому `from fake_api import BASE_URL` у мережевих задачах
    виглядає як зайвий імпорт, хоч він потрібен перевірці. Дорікати за таке —
    найгірше, що може зробити розбір, тому цей список винятків потрібен.
    """
    names: set[str] = set()
    for snippet in snippets:
        for candidate in (snippet, f"assert {snippet}"):
            try:
                tree = ast.parse(candidate)
            except (SyntaxError, ValueError):
                continue
            names |= _names_used(tree)
            break
    return names


def review_code(code: str, *, limit: int = MAX_REMARKS,
                keep: Iterable[str] = ()) -> CodeReview:
    """Розбирає код і повертає зауваження, найважливіші — першими.

    `keep` — імена, які код читає поза редактором (приховані перевірки). Їх не
    рахуємо «невикористаними».

    Код, який не компілюється, теж розбирається — але одним рядком: спершу
    треба виправити синтаксис, бо решта зауважень була б ворожінням на каві.
    """
    reserved = set(keep)
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        line = error.lineno or 0
        return CodeReview(
            remarks=(Remark(
                kind="syntax",
                title=f"Код не компілюється: рядок {line}",
                advice=(
                    "Спершу виправ синтаксис — вкладка «Тести» пояснить "
                    "помилку людською мовою. Розбір коду почнеться після цього."
                ),
                line=line,
            ),),
            summary=f"Код не компілюється — дивись вкладку «Тести» (рядок {line}).",
        )

    if not tree.body:
        return CodeReview(summary="Редактор порожній — нема чого розбирати.")

    findings: list[Remark] = []
    for rule in RULES:
        try:
            findings.extend(rule(tree, reserved))
        except (SyntaxError, ValueError, RecursionError, AttributeError):
            # Одне зламане правило не має ламати весь розбір: код користувача
            # буває який завгодно, і падати на ньому — найгірший варіант.
            continue
    findings.extend(_praises(tree, code))

    issues = sorted((r for r in findings if not r.is_praise), key=_sort_key)
    shown = issues[:max(0, limit)]
    praises = [r for r in findings if r.is_praise][:1]

    return CodeReview(
        remarks=tuple(shown + praises),
        summary=_summary(issues, shown),
    )


def _summary(issues: list[Remark], shown: list[Remark]) -> str:
    if not issues:
        return NO_REMARKS
    if len(shown) < len(issues):
        return (
            f"Зауважень: {len(issues)} — тут перші {len(shown)}. Виправ їх і "
            "натисни «Розібрати ще раз»."
        )
    return f"{issues_phrase(len(issues)).capitalize()} — виправ і здай задачу."


__all__ = [
    "ADVICE",
    "CodeReview",
    "DEEP_NESTING",
    "EMPTY_REVIEW",
    "LONG_FUNCTION",
    "MAX_REMARKS",
    "NOT_REVIEWED",
    "PRAISE",
    "REPEATED_LITERAL",
    "RULES",
    "NO_REMARKS",
    "Remark",
    "STARTER_REVIEW",
    "issues_phrase",
    "names_used_in",
    "review_code",
]
