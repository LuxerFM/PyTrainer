# PyTrainer: what it is now, what is missing, what to do next

Updated 26.09.2026 (commit `c465c03`). Lives in the repository so the
description does not drift from the code; the numbers below are verifiable with
the commands from README.

## What it is now

PyTrainer is a desktop Python trainer in Ukrainian (PySide6/Qt 6, SQLite,
everything else is the standard library; the only external dependency is
PySide6==6.11.2). The goal is set inside the product itself: in 9 months from
zero to first freelance money.

Today it is no longer a prototype: 464 tests, ~95% coverage, a 40.6 MB built
`.exe` needing no Python, no internet and no admin rights, with progress kept
in the system service folder rather than next to the `.exe` (why exactly —
see "UI and data").

## Content: 108 tasks, 80 ready

| Block | Ready / total | What it is |
|---|---|---|
| Months 1–2 | 31 of 35 | basics: variables, conditions, loops, strings, lists, dicts, functions, files, errors, OOP, Git, venv |
| Drills of weeks 1–4 | 20 of 20 | 5–12 minutes per single skill, checks on several inputs — "typing the answer in" does not work |
| Months 3–4 | 24 of 29 | LeetCode/Codewars 7 kyu – medium, network with a fake_api fixture, bug hunts |
| Months 5–6 | 5 of 14 | data work, tests, first project tasks (several files, real `import`) |
| Months 7–9 | 0 of 10 | future-block markers (stub): tickable only |
| **Total** | **80 of 108** | 28 stubs (stub) spread over months 2–9 |

Ready material is 1063 minutes (~18 hours) by task estimates. 347 checks in
total: 282 code, the other 65 output (`contains`, `not_contains`, `equals`,
`lines`). 35 tasks name a source, 10 bring extra project files. By difficulty:
18 easy, 45 medium, 11 hard, 6 project. Material is written 2–3 weeks ahead —
deliberately, never invented upfront.

## Check engine

Code runs in a separate process in a temp folder: 5 s timeout killing the whole
process tree, 64 KB output cap, stdin as fixture, multi-file tasks with a real
`import`. In the `.exe` the trainer launches itself with `--exec-runner`
(because `sys.executable` there is the trainer itself).

Stdout checks now run **in parallel** (up to 3 threads, answer order
preserved), and the child interpreter **warms up** ahead in a background
thread: on three checks 3361 ms → 1419 ms in the built `.exe`, first child
launch 1228 ms, warmed-up 1063–1118 ms.

22 error types explained in Ukrainian: what it means, which line, what to do,
with a "go to line" button.

Code review is 11 rules over `ast` that read not "does it work" but "will a
human understand"; review never blocks, never lowers XP, and knows about hidden
checks.

## Learning rules (all in the core, not in the UI)

XP by task level, minus 15% per hint (floored at 40%); a pasted solution = 3
hints + mandatory review.
Third hint level after 10 minutes of active work (20–25 for projects); only
in-focus time counts.
Reviews at 1 / 3 / 7 / 30 with separate XP per interval depth; the fifth
successful review drops the task from the queue ("retained" is the headline
progress number).
Cold review: a random passed task from its stub, no hints, 3–10 min timer.
Weekly digest: a seven-day summary, weak topics, three next steps, a markdown
report; the mistake journal closes only on a clean pass.
Day plan (reviews → weak topic → new task) with a 100-minute budget; day
streak; active time; a 4-week XP chart and an 8-week calendar.

## UI and data

Six task-panel tabs (task, tests, review, reference, hints, history), four
sidebar modes (Path / Reviews / Progress / Plan), 18 cheatsheets matched to
the task, dark and light themes, text scaling, 15+ hotkeys.

Data is split by purpose, and that is not cosmetic:

| Where | What is there | Why exactly there |
|---|---|---|
| `%LOCALAPPDATA%\PyTrainer` (or the `--data-dir` folder) | `pytrainer.db`, `backups/` (last 7), `pytrainer.lock` | the desktop on this machine syncs to OneDrive, and SQLite in a synced folder rots sooner or later |
| next to the `.exe` | `progress.json`, `Python-Roadmap.md`, `pytrainer.ini` | readable progress history, generated plan, window state |

Moving from the old folder is done by `paths.migrate_data()`: first copy, then
rename the old file to `*.moved` — an interrupted move costs two copies, not
progress. The database opens with `journal_mode=WAL`, `busy_timeout=5000` and
`PRAGMA quick_check()`; a broken file is not erased but slid aside to
`pytrainer.db.broken-<date>`. No second window opens on the same database —
`QLockFile` with a PID, and a corrupted lock no longer blocks launch forever.
Demo mode on a temp database never touches your progress.

## Infrastructure

464 tests, 95% coverage (CI gate at 90%), of which the most valuable runs every
course solution against its own checks and separately verifies the starter
does not pass. Separate guard tests watch the README numbers (tests, tasks,
screenshots) so they never drift from the truth.

The CI workflow is written: unit tests on Python 3.11 and 3.13, coverage, a
`.exe` build with a self-check (code really runs — 3/3 steps), release on tag.
**26.09.2026 CI green for the first time** (units 3.11/3.13, coverage, build +
self-test of the .exe, release v0.2.1). On the way we cured 3 bugs visible
only in live CI: the throttle skipped the first write (`monotonic` in a fresh
container < 180 s), the Windows runner's cp1252 console (`PYTHONUTF8: 1`), the
windowed `.exe` not blocking the shell (`Start-Process -Wait`). Repo:
`LuxerFM/PyTrainer`, branch master.

10 README screenshots are generated by a script and verified by a test; the
code-run vs `.exe`-run screenshots are pixel-compared — 0 differing pixels out
of 1,361,600.

## What already holds up as production

Third-party code execution safety (process, timeout, cap, process tree),
progress persistence (folder outside the cloud, WAL, `busy_timeout`,
`quick_check`, broken-file retreat, 7 copies via `Connection.backup`),
lossless data moves, one process per database, database migrations, self-test,
deterministic screenshots, architecture docs, full offline work, zero network
requests, no data collection.

Closed 26.09.2026 (commit `b420f0f`): data move out of OneDrive, `WAL` +
`busy_timeout` + `quick_check`, one process per database (with corrupted-lock
healing), parallel checks and interpreter warm-up.
Closed 26.09.2026: crash log and version — `--version`, version in the window
title, `logs/pytrainer.log` + `logs/crash-*.log` with version and argv, build
date.
Closed 26.09.2026: `progress.json` portability — version-2 snapshot/restore
carries `attempts` (mistake journal, digest, streak and XP stats travel with
the progress; re-import creates no duplicates, v1 files still read).
Closed 26.09.2026: restore from backup via UI — "Файл → Відновити з копії…"
("File → Restore from backup…") with a `backups/` list, confirmation and a
`*-pre-restore-*.db` safety copy; a broken backup never touches the live base.

## What is missing (by priority)

### P0 — before giving it to anyone else

| Gap | Why it hurts | Effort |
|---|---|---|
| `progress.json` portability | ✅ Closed 26.09.2026: snapshot v2 carries `attempts`, restore merges without duplicates | — |
| Crash log and version | ✅ Closed 26.09.2026: `--version`, version in the window title and "About", `logs/pytrainer.log` + `logs/crash-*.log`, build date from `tools/build_exe.py` | — |
| Restore from backup via UI | ✅ Closed 26.09.2026: "Файл → Відновити з копії…" ("File → Restore from backup…"), `*-pre-restore-*.db` safety copy, broken backup leaves the base alone | — |
| First CI run | ✅ Closed 26.09.2026: remote exists, CI green, release v0.2.1 with `.exe` | — |
| `.exe` reputation | SmartScreen warns about an unknown publisher; no signature, no installer, no update | 1 day+ (certificate, Inno Setup) |

### P1 — quality and life

- ✅ Closed 26.09.2026: the split is done — `main_window.py` ~1500→891
  (`ui/file_sync.py`, `ui/run_flow.py`, `ui/refresh_view.py`, `ui/dialogs.py`),
  `task_panel.py` ~1100→554 (`ui/test_results.py`, `ui/review_view.py`,
  `ui/hints_view.py`, `ui/history_view.py`). Behaviour and method names
  unchanged, test count identical at every slice.
- ✅ Closed 26.09.2026: safer writes — `paths.atomic_write_text()` (tmp +
  `os.replace`) for `progress.json`, the roadmap, digests and exports;
  background writes at most every 3 min (`FILES_WRITE_INTERVAL`), explicit
  actions and close always write.
- Writes next to the `.exe`: placed in `Program Files`, writes without admin
  rights may fail — either move those files to the data folder or show an
  honest message.
- First-launch speed: every child-process launch re-unpacks `--onefile`
  (measured 1228 ms cold, 1063–1118 ms warmed). `--onedir` or a process pool
  would remove it; budgets (window, RAM) should also be measured, recorded
  and kept from degrading.
- Pixel "code ↔ `.exe`" comparison as a CI step: zero difference already
  proven, making it automatic is what is left.
- English localisation (Qt `.qm` + string extraction), high-DPI,
  accessibility: full keyboard navigation, contrast, screen reader.
- Metrics instead of scores: time to solve, attempts to clean, "residual
  knowledge".
- Rhythm: reminders (tray/notifications), a streak grace day, the 20–30
  minute rule from the plan.

### P2 — product

Concept tags instead of topics; "fix readability" exercises; mutation
exercises; several profiles; mentor export; web/mobile client on the same
core; privacy and licences (PySide6 is LGPL: fine for a desktop app, but worth
a note; task sources are already credited).

## Brainstorm: ideas that would really move the product

1. **"Freelance readiness" — an exam every 4 weeks.** The most valuable thing
   missing now: the trainer measures effort (XP, tasks, streak) but not
   capability. Once a month — 5 tasks from zero, no hints and no review, on a
   timer, random from the passed. The result is a separate readiness curve and
   an honest verdict of "what exactly blocks the first order". Impact: high,
   effort: medium, risk: the exam may demotivate — so a safe tone and no XP.
2. **Personal intervals instead of 1/3/7/30.** Intervals are fixed now
   (`scoring.INTERVALS`), though the database already holds every review's
   history. An SM-2-like model (each task with its own "easiness factor") buys
   more knowledge for the same time: easy tasks return rarer, slippery ones
   more often. Impact: high, effort: medium, risk: less predictability —
   compensated by "why exactly today" text.
3. **A project thread instead of 80 isolated tasks.** The biggest architectural
   change: one own CLI app growing month by month, with tasks becoming "add a
   feature to your code". Then checks run against a real project, the
   portfolio assembles itself, and how much code you wrote is visible. Impact:
   high (that is what clients are shown), effort: large (curriculum gains
   project stages, the runner gains checks against files), risk: harder error
   diagnostics.
4. **A code-reading exercise generator.** Code review already recognises
   patterns — the same engine can create exercises: take a course solution,
   apply a mutation (change `range(n)` to `range(1, n)`, swap `and`/`or`), show
   the code and ask to find the bug. The exercise pool becomes infinite with no
   manual content — and that is what usually limits any homemade course.
   Impact: medium-high, effort: medium (generator + "found the spot"
   comparison), risk: mutations must be verified to really change behaviour.
5. **A local "code phrasebook".** Close the "found → taught → verified" loop:
   if review sees `range(len())` a third time in a week, the digest offers a
   5-minute drill on exactly `enumerate`, not a general topic. The cheapest way
   to make learning truly adaptive — with no model at all, only on its own
   data (the review engine exists, 20 drills already). Impact: high, effort:
   small-medium.
6. **A thinner client on the same core.** The core knows no Qt — so a web UI
   (stdlib local server) or CLI is possible, and the same 80 tasks, rules and
   reports would work in a browser, on a phone, on a work laptop. Impact:
   medium now, high if the product ever becomes "for others"; effort: large.

## Simplifications worth making sooner or later

- 28 stub tasks are not tasks but a 5-block checklist; a separate category in
  the tree and stats adds noise.
- "Topic" is too broad a notion for diagnostics (concept tags would give
  precision).
- The panel already has **six** tabs (history joined) — past the "five" limit:
  attempt history belongs merged into "Tests" or "Review" rather than a
  seventh tab.
- `progress.json` and `Python-Roadmap.md` are in Git now: progress history is
  nice, but every verdict dirties the working copy. Either keep deliberately
  or unindex and keep progress in the database only.
- `pytrainer.db.moved` and `backups.moved/` in the project root serve nothing
  anymore — the copy sits in the new folder, the old files can go.
