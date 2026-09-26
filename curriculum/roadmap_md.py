"""Генератор Python-Roadmap.md із навчального плану.

Роадмап більше не редагують руками: галочки ставить застосунок, коли ти здаєш
задачу. Хочеш власні нотатки — веди їх у README.md, цей файл перезапишеться.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import CURRICULUM, all_tasks, study_tasks
from .schema import Month

HEADER = """# 🗺️ Python Roadmap: від нуля до перших грошей за 9 місяців

> Темп: 1,5–2 години щодня. Ключ — регулярність, а не марафони.
> ⚡ Твій темп: ПРИСКОРЕНИЙ. Ідете своїм темпом, уроки видаються по готовності.
>
> 🤖 **Цей файл генерує PyTrainer** — галочки тут ставляться самі, коли ти здаєш
> задачу у тренажері (`.venv\\Scripts\\python.exe main.py`).
> Ручні правки в цьому файлі будуть перезаписані: власні нотатки веди в README.md.
"""

BIG_PICTURE = """
## 📊 Загальна картина

```
Місяці 1–2   → База Python (пишете РУКАМИ, без ШІ)
Місяці 3–4   → Інструменти + перші проєкти на GitHub
Місяці 5–6   → Спеціалізація під гроші (боти/парсинг/AI)
Місяці 7–9   → Портфоліо + перші замовлення на фрілансі
```
"""

RESOURCES = """
---

## 📚 РЕСУРСИ (все безкоштовне)

### 🇺🇦 Українською
| Ресурс | Що це | Лінк |
|---|---|---|
| Prometheus | «Основи Python» — класика | prometheus.org.ua |
| ITVDN | Python Starter + Essential безкоштовно | itvdn.com/ua |
| Hillel Max | Відеокурс Python Start | max.ithillel.ua |
| Mate academy | Python, гранти / «платиш після працевлаштування» | mate.academy |
| EPAM Campus | Python Development Program (конкурс) | campus.epam.com |

### 🌍 Англійською (найсильніші у світі)
- ⭐ **CS50P** (Гарвард) — найкращий безкоштовний курс Python: cs50.harvard.edu/python
- **freeCodeCamp** — Python сертифікація: freecodecamp.org
- ⭐ **«Automate the Boring Stuff with Python»** — безкоштовна книга онлайн. Ідеально під фріланс: парсинг, автоматизація, файли

### 💪 Практика (щодня!)
- **Codewars** — задачки 8–7 kyu на старті
- **CheckiO** — гра-головоломка на Python (українська розробка 🇺🇦)
- **Exercism** — задачі з менторством
- **roadmap.sh/python** — інтерактивна карта прогресу
"""

RULES = """
---

## 🤖 ПРАВИЛА ГРИ З ШІ

1. **Місяці 1–2 — ШІ тільки як вчитель.** Питаєте «поясни, чому не працює», а не «напиши за мене». Код — руками.
2. **Місяць 3+ — правило 20–30 хвилин.** Спершу самі, потім ШІ.
3. **Після місяця 4 ШІ — прискорювач.** Ваш досвід з ШІ стане перевагою над іншими джунами.
4. **У тренажері розв'язок відкривається лише після 10 хвилин роботи над задачею.** Це не обмеження, а захист від «подивлюсь і зрозумію».
"""

PRICES = """
---

## 💰 ЩО ЗАМОВЛЯЮТЬ НА ФРІЛАНСІ (орієнтовні ціни)

| Задача | Ціна |
|---|---|
| Telegram-бот для бізнесу | $50–300 |
| Парсер сайту / збір даних | $30–150 |
| Автоматизація рутини (Excel, звіти) | $50–200 |
| AI-інтеграція в процеси клієнта | $100–500+ |

**Платформи:** Freelancehunt, Freelance.ua, Upwork, Fiverr, телеграм-чати із замовленнями.
"""


def _task_line(task, status: str, indent: str = "") -> str:
    mark = "x" if status == "done" else " "
    if task.stub:
        return f"{indent}- [{mark}] {task.title} — _заплановано_"
    return f"{indent}- [{mark}] {task.title} · {task.level} · {task.base_xp} XP"


def _month_block(month: Month, statuses: dict[str, str]) -> str:
    lines = [f"\n---\n\n## 📆 {month.title.upper()}\n"]
    if month.subtitle:
        lines.append(f"_{month.subtitle}_\n")

    for topic in month.topics:
        lines.append(f"\n### {topic.title}\n")
        for task in topic.tasks:
            lines.append(_task_line(task, statuses.get(task.id, "todo")))

    real = [t for topic in month.topics for t in topic.tasks if not t.stub]
    done = [t for t in real if statuses.get(t.id) == "done"]
    if real:
        lines.append(f"\n**Прогрес: {len(done)} із {len(real)} задач.**")
    month_done = "x" if real and len(done) == len(real) else " "
    lines.append(f"\n- [{month_done}] {month.title} завершено")
    return "\n".join(lines) + "\n"


def _tracker(statuses: dict[str, str], stats: dict | None) -> str:
    stats = stats or {}
    milestones = [
        ("Місяць 1 завершено", _month_complete(CURRICULUM[0], statuses)),
        ("Місяць 2 завершено", _month_complete(CURRICULUM[1], statuses)),
        ("Перший проєкт на GitHub", False),
        ("Спеціалізацію обрано: ___________", False),
        ("Перший проєкт спеціалізації", False),
        ("Портфоліо готове", False),
        ("Перший безкоштовний відгук", False),
        ("Перше замовлення взято! 🎉", False),
        ("Перший зароблений $ 🤑", False),
    ]
    lines = ["\n---\n\n## 📈 ТРЕКЕР ПРОГРЕСУ\n"]
    lines.append(
        f"- Пройдено задач: **{stats.get('done', 0)} із {stats.get('total', 0)}**"
    )
    lines.append(f"- XP: **{stats.get('xp', 0)}**")
    lines.append(f"- Серія днів поспіль: **{stats.get('streak', 0)}**")
    lines.append("")
    for title, value in milestones:
        lines.append(f"- [{'x' if value else ' '}] {title}")
    return "\n".join(lines) + "\n"


def _month_complete(month: Month, statuses: dict[str, str]) -> bool:
    real = [t for topic in month.topics for t in topic.tasks if not t.stub]
    if not real:
        return False
    return all(statuses.get(t.id) == "done" for t in real)


def render(statuses: dict[str, str], stats: dict | None = None) -> str:
    """Збирає весь текст роадмапу."""
    real = study_tasks()
    done = sum(1 for task in real if statuses.get(task.id) == "done")
    summary = {
        "done": done,
        "total": len(real),
        "xp": (stats or {}).get("xp", 0),
        "streak": (stats or {}).get("streak", 0),
    }

    parts = [HEADER, BIG_PICTURE, f"\n_Оновлено: {date.today().strftime('%d.%m.%Y')}_\n"]
    parts.append(
        f"\n**Задач у тренажері: {len(all_tasks())}** "
        f"(з них готові до розв'язання: {len(real)})\n"
    )
    for month in CURRICULUM:
        parts.append(_month_block(month, statuses))
    parts.append(_tracker(statuses, summary))
    parts.append(RESOURCES)
    parts.append(RULES)
    parts.append(PRICES)
    return "".join(parts)


def write(path: str | Path, statuses: dict[str, str], stats: dict | None = None) -> Path:
    """Пише файл роадмапу (перезаписує, атомарно)."""
    from trainer.paths import atomic_write_text

    return atomic_write_text(path, render(statuses, stats))
