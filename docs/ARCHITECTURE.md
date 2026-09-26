# PyTrainer Architecture

A document for whoever reads the code: how the layers are laid out, why it is
this way, and where to add new features.

## Three layers

```
curriculum/        WHAT to learn           — data that knows nothing of the UI
    month*.py        tasks: statement, starter, checks, hints
    drills1.py       drills: 5–12-minute practice after each week of month 1
    cheatsheets.py   cheatsheets and auto-pick by task topic
trainer/core/      HOW to check            — learning rules, database, code runs
    errors.py        traceback → human explanation (what it is and what to do)
    exec_runner.py   --exec-runner mode: the .exe runs someone else's file by itself
    selfcheck.py     --self-test mode: does the verdict really arrive
    runner.py        running code in a separate process + checks
    review.py        cold review: which passed task to pull from memory
    codereview.py    code review: rules over ast → human remarks
    mistakes.py      mistake journal: what still "hangs" vs closed — and by what exactly
    digest.py        weekly digest: seven days of learning in numbers and a verdict
trainer/ui/        HOW to show it          — Qt widgets and theme
trainer/cli.py     launch-mode picker (flags are parsed before importing Qt)
```

Dependencies go one way only: `ui → core → curriculum`. The core never imports
a PySide6 module, so it can run and be tested with no screen (which is exactly
what the tests do: `QT_QPA_PLATFORM=offscreen`).

## One attempt's flow

```
user presses F5
      │
      ▼
ui/main_window.py ──► core/runner.run_task(task, code)
      │                     │ separate process in a temp folder (Python, and in .exe —
      │                     │ the .exe itself with --exec-runner: there is no other Python there)
      │                     │ 5 s timeout, 64 KB output cap, stdin fixture
      │                     ▼
      │              RunResult(stdout, stderr, checks)
      ▼
core/session.StudySession.record_result(task, result)
      │  decides: how much XP, passed or not, into the review queue or not
      ▼
core/db.Database ──► SQLite (progress / attempts / reviews)
      │
      ▼
ui updates the tree, the test panel, XP, streak, and writes Python-Roadmap.md + progress.json
```

The key point: **learning rules do not live in the UI**. The `StudyUpdate`
returned by the session holds everything needed for drawing (`xp`, `passed`,
`review_days`, `mastered`, `notes`). That is why these rules are covered by
unit tests in `tests/test_session.py` with no window at all.

## Cold review: recall instead of recognition

Ordinary review opens a task the way it was passed: with your code in the
editor and hints at hand. That tests "where what lies" memory more than the
ability to solve. So there is a separate mode that removes the crutches:

```
ui/review_page.py  "Холодне повторення" ("Cold review", or Ctrl+Shift+R)
      │
      ▼
core/review.pick_cold_task(db, exclude=current task)
      │  only PASSED tasks; first the ones already asking for review,
      │  and if the queue is empty — a random one of the passed
      ▼
ui/main_window.start_cold_review()
      │  editor from the starter, panel.set_locked(True) — hints and solution
      │  unavailable, countdown cold_seconds() = 3–10 min
      ▼
F5 → core/session.record_result(..., review_mode=True)
      │  success: interval 1/3/7/30 moves on + XP bonus;
      │  the interval never shrinks — the task leaves the queue
      │  failure: the task returns to the queue (next attempt tomorrow)
      ▼
the mode switches itself off: in the next attempt hints are available again
```

Three details that are easy to break and hard to notice:

- **saved code is not overwritten.** In cold review the editor starts from the
  starter, and that is why `_start_run` and `_tick` do not write it to the
  database: otherwise your real solution would be replaced by the stub, and
  autosave would do it automatically and invisibly;
- **only one attempt counts.** After the verdict the mode switches off: if you
  did not recall — you can calmly walk the task with hints instead of sticking
  in cold mode till midnight;
- **a retained task stays retained.** A successful cold recall of a task that
  already passed all four intervals does not return it to the queue — it gives
  the most generous XP bonus and breaks nothing (see `session._handle_success`).

## Code review: a reader instead of a compiler

Tests check whether code works. Code review (the "Рев'ю"/"Review" tab, `F6`)
checks something else: whether a human will understand it. It is the same split
as between `runner.py` and `codereview.py` — the first runs code, the second
reads it.

```
ui/task_panel.py  "Рев'ю" ("Review") tab: remark cards + "Рядок N" ("Line N") button
      │  F6 or the "Розібрати код" ("Review code") button; after every run — quietly by itself
      ▼
core/codereview.review_code(code, keep=…)
      │  ast.parse → RULES rules → Remark(kind, title, advice, line)
      │  keep — names read by the task's hidden checks
      ▼
CodeReview(remarks, summary) ─► cards in the panel, • "Рев'ю · N" ("Review · N") header
```

Decisions that are easy to break:

- **review must not crash on user code.** Code that does not compile returns a
  single line "fix the syntax first"; every rule runs inside `try` so that one
  broken rule does not kill the whole review;
- **`keep` is not politeness, it is truth.** Checks run in the same file, so
  they can read the human's variables (`BASE_URL` in network tasks). Without
  that list the review would advise deleting what the task cannot pass without;
- **six-card cap.** Six fixes is an evening of work; nobody reads twenty
  complaints. The summary shows how many there are in total;
- **`elif` is not a new floor.** In `ast` the `else` branch is a statement
  list, and `elif` is that same `if` inside `orelse`, so a calculator with six
  `elif`s would look like six nesting levels;
- **the starter is never reviewed.** The student did not write it, and
  "unused variables" in it are not their mistake.

Rules live in `RULES` — a list of `(tree, keep) → list[Remark]` functions.
To add your own: append a function with a detailed docstring and add it to
`RULES`. No detailed check — no remark.

## Weekly digest: a meta-look once a week

The day plan answers "what to do today". The weekly digest (`digest.py`)
answers "and what came of it?". Without it learning turns into a todo ribbon:
tasks get passed, mistakes pile up, and whether it got easier is nowhere to
see.

```
db.attempts_between(start, end) ─┐
db.solved_between(start, end)   ─┤
db.task_results()               ─┼─► core/digest.weekly_digest(db, today) ─► WeeklyDigest
db.due_reviews(last)            ─┤        knows no Qt: only/verdict/markdown
db.streak(), db.total_xp()      ─┘                    │
                                                     ├─► ui/stats_page: row + button
                                                     ├─► ui/digest_page.DigestDialog (Ctrl+Shift+W)
                                                     └─► ui/main_window.save_report → markdown file
```

Separately — the mistake journal (`mistakes.py`). It classifies every mistake
by a **double criterion**: whether a success came after it, and whether that
success was clean.

```
mistake_history() ─► task_id + error_kind ─► look at attempts:
     any success after the mistake?  ── no  ──────────────────► OPEN
               │ yes
     was it with a hint/solution? ── yes ─────────────► CLOSED WITH HELP
               │ no
     passed with a clean run ──────────────────────────► CLOSED
```

Decisions that are easy to break:

- **compare by attempt `id`, not by time.** `created_at` has one-second
  precision, and two attempts within one second would share a timestamp — then
  the order is unguessable. The `mistake_history` query returns both `pass_id`
  and `last_id`, and sorts with `m.last_id` as the second key;
- **a clean run means no hints and no solution.** For old databases (the schema
  did not know the `clean` column) there is a fallback: if the task is passed
  and no hint was ever opened — closed. The schema has a mini-migration, so
  the database does not break;
- **three states, not two.** Counting any pass as "closed" means the most
  useful list in the trainer becomes a history of suffering; counting only
  clean passes means an old `NameError` hangs forever. "Closed with help"
  gives the middle and leads to cold review;
- **the verdict is computed from the same data as the numbers.**
  `WeeklyDigest.verdict` is a property, not a separate function, so "empty
  week", "ragged week" and "closed clean" cannot contradict the neighbouring
  cards;
- **the report outlives the week.** `as_markdown()` prints a frozen snapshot:
  in a month the trainer's numbers are different, and rereading how the week
  went is useful — so the text carries its creation date.

## Two exercise levels: tasks and drills

The plan deliberately holds two different-sized units of work side by side.

| | Task | Drill |
|---|---|---|
| How long | 10–25 min | 5–12 min |
| How many skills | one or two, often with new theory | exactly one, already familiar |
| How many checks | 3–7, sometimes `stdout` and `code` | 2–4, usually on **different inputs** |

Drills appeared after an honest count: 18 month-1 tasks are 230 minutes —
several evenings for a "basics" month. A drill solves it differently than just
adding more tasks: it is short enough that starting it is not scary, and its
checks are deliberately composed so that **typing the answer by hand fails**
(three different inputs for digit sums, three number sets for max, three
different words for vowels).

A drill's topic stands in the plan right after its week — so `plan.py`
naturally leads to training while the skill is still hot, and per-topic stats
separately show what exactly limps.

## Plan data model

```python
Month(title, subtitle, topics=[Topic(title, tasks=[Task, ...])])

Task(id, title, statement, starter, level, checks, hints,
     stdin, files, entrypoint, minutes, stub,
     source, source_url, cheatsheet)
```

- `checks` — a list of `Check`: either `code` (assert code after the user's
  code) or `stdout_*` (what the program printed for the given input).
- `hints` — hints; the last one with `solution=True` opens on a timer.
- `files` — extra project files (e.g. `utils.py`) that appear next to the
  solution in the temp folder.
- `stub=True` — a plan item done outside the trainer (venv, Git, pytest);
  it can be ticked manually.
- `source` / `source_url` — where the task comes from (LeetCode, Codewars).
  The task shows it in the statement, and the checks are always home-written.
- `cheatsheet` — a mini-reference key from `curriculum/cheatsheets.py`. Empty —
  the cheatsheet is picked by words in the topic and task titles.

## The info layer in the task panel

The right panel has six tabs, each answering its own beginner question:

| Tab | Question it answers |
|---|---|
| Task ("Задача") | "What do they want from me?" — statement, topic, task number, time estimate |
| Tests ("Тести") | "What exactly will be checked, and what came out?" — check list before a run, results after |
| Review ("Рев'ю") | "Will another human understand this?" — code review via `ast` |
| Reference ("Довідка") | "How is this written?" — cheatsheet matched to the topic |
| Hints ("Підказки") | "Where to look?" — three levels, solution on a timer |
| History ("Історія") | "How am I moving?" — all runs, XP, time on the task |

Error explanations are a separate layer, not part of the UI: `core/errors.py`
parses a traceback (or a short string from a hidden check) and returns
`Explanation(kind, message, meaning, advice, line, source)`. That means the
same module can be used in a CLI or web version with zero changes.

The `task()`, `code()`, `stdout()`, `hint()`, `solution()` constructors keep
the data files readable: a task reads almost like prose.

## SQLite tables

| Table | Purpose |
|---|---|
| `progress` | task state: `status`, `best_xp`, `bonus_xp`, `hints_used`, `solution_used`, `active_seconds`, saved code |
| `attempts` | every run: time, verdict, whether it was a check run and whether the pass was clean (`clean`). Streak, calendar, mistake journal and weekly digest come from here |
| `reviews` | review queue: `due_date`, `interval_index` |

The schema has mini-migrations (`Database._migrate`), so a database created by
an older version does not break — new columns are added in place.

## Learning rules (all in `core/scoring.py` and `core/session.py`)

| Rule | Formula |
|---|---|
| XP per task | level base × (1 − 15% per hint), floored at 40% |
| Pasted solution | counts as 3 hints + mandatory review |
| Re-pass | 30% of base XP (added to `best_xp` if larger) |
| XP per review | 20/40/60/80% of base depending on interval depth |
| Intervals | 1 → 3 → 7 → 30 days; the fifth successful review drops the task from the queue |
| Retained | task passed with no review scheduled anymore |
| Streak | days in a row with at least one code run (today not required till evening) |
| Cold review | hints and solution off, time capped; the verdict moves the interval on, and a retained task does not return to the queue |
| Mistake closure | only a clean pass after it; passed with a hint — "closed with help" |

## Where to add new things

| What you want | Where to look |
|---|---|
| new tasks | `curriculum/month*.py` |
| new drill for a week | `curriculum/drills1.py` (and `WEEKn_DRILLS` in `month1.py`) |
| new cheatsheet | `curriculum/cheatsheets.py` (+ key in the task) |
| explanation for one more error | `core/errors.EXPLANATIONS` |
| new XP or interval rules | `core/scoring.py` (+ test in `tests/test_scoring.py`) |
| cold-review rules (whom we take, how much time) | `core/review.py` (+ test in `tests/test_review.py`) |
| new code-review rule | `core/codereview.RULES` (+ test in `tests/test_codereview.py`) |
| new weekly-digest section or sentence | `core/digest.py` (+ `tests/test_digest.py`) |
| mistake-closure rule | `core/mistakes.py` (+ `tests/test_mistakes.py`) |
| new reaction to a result | `core/session.py`, then `ui/main_window._render_update` |
| new check kinds | `curriculum/schema.Check` and `core/runner.py` |
| new service mode/flag | `trainer/cli.py` (+ `main.py` in the docs) |
| verify the code-running path | `core/selfcheck.py` — the `--self-test` steps |
| change the look | `ui/theme.py` (QSS), `ui/task_panel.py` (statement and reference text) |
| new screenshot for README | `tools/make_screenshots.py` (the `SHOTS` list) |
| change paths for the built `.exe` | `trainer/paths.py` |
| another interface (CLI, web) | plug in `core/` — it does not depend on Qt |

## Paths, data and the built .exe

The nastiest difference between running from code and running the build is
where files are looked up. `trainer/paths.py` solves it with three functions:

| Function | Plain run | Built `.exe` |
|---|---|---|
| `app_folder()` | project root | folder holding the `.exe` itself |
| `data_folder()` | system service folder (`%LOCALAPPDATA%\PyTrainer`, `~/.local/share/PyTrainer`) or `--data-dir` / `PYTRAINER_DATA_DIR` |
| `resource(*parts)` | project root | unpack folder `sys._MEIPASS` |
| `is_frozen()` | `False` | `True` |

The risk here is not cosmetic: `--onefile` unpacks the program into a temp
folder and removes it on exit, so anything kept **inside** would vanish after
every window close.

Then comes the second, less obvious risk. On this machine the desktop is
redirected to OneDrive, so "next to the .exe" means "in a synced folder", and
**SQLite in a synced folder is a broken database sooner or later**: the cloud
reads and writes the file whenever it feels like it, possibly mid-transaction.
So files are split by purpose:

```
%LOCALAPPDATA%\PyTrainer\        (or the --data-dir folder)
    pytrainer.db      progress
    pytrainer.lock    lock: no second window on the same database
    backups/          quiet database copies (last 7)

next to the .exe (or next to the code)
    progress.json     progress in readable form — kept in Git
    pytrainer.ini     theme, text scale, window layout
    Python-Roadmap.md generated plan
```

Moving from the old folder is done by `paths.migrate_data()` once per launch:
first it **copies**, then renames the old file to `*.moved`. The order is
exactly so that an interrupted copy does not cost progress; hence the worst
case of a move is two copies instead of none.

The database opens with three pragmas: `journal_mode=WAL` (writes never block
reads), `busy_timeout=5000` (waiting instead of an instant "database is
locked") and `synchronous=NORMAL`. On start — `PRAGMA quick_check()`; if the
file is broken before opening (`file is not a database`), `app.open_database()`
slides it aside to `pytrainer.db.broken-<date>` and starts a fresh database
instead of dying with a traceback.

The launch lock is `QLockFile`, and that is not the first choice but a
conclusion: `QLocalServer` on Windows calmly lets several processes listen on
the same name (verified), so as a mutex it does not work. `QLockFile` keeps a
PID and cleans up a stale lock from a killed process by itself.

But it too has a blind spot that had to be closed by hand: a lock whose
content Qt cannot read (torn record, corrupted file, someone else's file with
that name) does not look stale — staleness is determined by the **PID inside**,
and there is none there. Such a lock would stay forever, and the app would
never open again with an "already running" message about nobody. So
`InstanceGuard` reads the lock after a failed attempt: no PID means garbage,
and `removeStaleLockFile()` removes it, then the attempt is retried. A live
copy cannot lose its lock this way: its lock reads fine, and Windows does not
let you delete an open file (verified — `removeStaleLockFile()` returns
`false`), so the second launch politely yields.

Before every launch a database copy is made (`db.backup_database`) via
`sqlite3.Connection.backup` — copying the file blindly could catch the
database mid-write.

The build: `tools/build_exe.py` + `pytrainer.spec`. The spec throws out unused
Qt modules (most of PySide6) and English Qt translations — without that a
one-file `.exe` weighs several times more. But it **adds** modules needed not
by the trainer but by task code (`csv`, `datetime`, `sqlite3`, `urllib`, …):
PyInstaller collects only what it found in the code, so without the explicit
list `import csv` in a solution would fail **only** in the `.exe`.

CI builds the `.exe` on every push and runs two different checks on it:
`--demo --screenshot` answers "does the window open", and `--self-test`
answers "does the verdict arrive". These are different questions, and the
first is sometimes "yes" when the second is "no".

A `v*` tag adds an archive to the release.

## When the .exe runs user code

The most dangerous difference between running from code and from the build is
not in paths but in `sys.executable`. The familiar `python` is an interpreter;
the built `.exe` is a program with an interpreter hidden inside. So
`interpreter_command()` in `core/runner.py` builds the command from two
options:

| | Run from code | Built `.exe` |
|---|---|---|
| Command | `python -X utf8 -u solution.py` | `PyTrainer.exe --exec-runner solution.py` |
| Flags | understood by the interpreter | interpreter flags unneeded: already in env |
| Who runs the file | Python itself | `exec_runner.main()` in the same process |

What would happen without this split (and did happen for real):
`PyTrainer.exe -X utf8 -u solution.py` launches a **second trainer window**.
The bootloader ignores unknown flags, so user code never ran at all, no
verdict arrived, the timeout killed only the bootloader while its child lived
on, holding `__stdout.txt` and `__stderr.txt` open — hence WinError 32 while
cleaning the temp folder. Three things fixed it separately, and each is
needed:

- `--exec-runner` — so the file runs instead of a second window opening;
- `_terminate_tree()` — `process.kill()` stops only the direct child, while in
  the `.exe` the real interpreter is the bootloader's child;
- `_remove_dir()` — cleaning the folder is not worth a single check result,
  so it is allowed to fail, not to break the run.

`exec_runner` prints an error in user code **itself** instead of passing it
out: in a windowed `.exe` an unhandled exception becomes a dialog with an "OK"
button, i.e. an ordinary error would look like a timeout.

README screenshots are made by `tools/make_screenshots.py`: it raises the
window on a demo database, waits for a real check result and saves
`window.grab()`. So the README pictures are renders of the app, not mockups.

## Fonts and text

The task panel deliberately uses **two fonts**: prose (statement, explanation,
reference) and monospace (code). `theme.prose_family()` and
`theme.mono_family()` return the first available system font and cache the
result; `_wrap_html()` substitutes it into HTML for `QTextBrowser`.

Hints and cheatsheets are stored as **plain text**, not HTML:
`task_panel.plain_to_html()` decides by itself which lines look like code
(`def` lines, `print(`, assignments) and gathers them into `<pre>`. So text in
the data stays readable, and the look stays tidy.

Two Qt traps already stepped on:

- `line-height` in `QTextDocument` works only in **percent** (120% gives ~21px
  per line at 14px); `line-height: 1.2` gives a surprising result;
- QSS `objectName` changes without repainting — after a change you need
  `style().unpolish()/polish()` (see `TaskPanel._repolish`).

## Deliberate limits

- User code runs with its user's rights: this is a trainer for your own
  learning, not a sandbox for someone else's code.
- One task = one answer file (`entrypoint`) plus immutable helper files;
  editing several files in the editor is not supported yet.
- Network tasks do not use the real internet but a local fixture from the
  standard library (`curriculum/fixtures.py`). That way a task checks out the
  same in tests and in CI, depends on no third-party APIs, and needs no `requests`. The skills are the same: status codes, JSON,
  auth.
