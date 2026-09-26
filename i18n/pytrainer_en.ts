<?xml version="1.0" encoding="utf-8"?><!DOCTYPE TS><TS version="2.1" language="en">                            
                            <context>                                                        
                                                            <name>Dialogs</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="57"/>                                                                                    
                                                                                            <source>Гарячі клавіші</source>                                                                                    
                                                                                            <translation>Keyboard shortcuts</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="58"/>                                                                                    
                                                                                            <source>Ctrl+Enter — запустити код
F5 — перевірити прихованими тестами
F6 — розібрати свій код (рев'ю)
Ctrl+N — наступна незавершена задача
Ctrl+L — план на сьогодні
Ctrl+R — черга повторень
Ctrl+Shift+R — холодне повторення випадкової задачі
Ctrl+P — прогрес і слабкі місця
Ctrl+Shift+W — тижневий огляд
Ctrl+F — пошук задачі
Ctrl+D — темна / світла тема
Ctrl++ / Ctrl+- / Ctrl+0 — розмір шрифту
Вкладка «Довідка» — шпаргалка з теми задачі
Tab / Shift+Tab — відступ / зменшити відступ
Ctrl+S — зберегти код у файл
F1 — ця довідка</source>                                                                                    
                                                                                            <translation>Ctrl+Enter — run code
F5 — run hidden tests
F6 — review your code
Ctrl+N — next unfinished task
Ctrl+L — today's plan
Ctrl+R — review queue
Ctrl+Shift+R — cold review of a random task
Ctrl+P — progress and weak spots
Ctrl+Shift+W — weekly digest
Ctrl+F — search tasks
Ctrl+D — dark / light theme
Ctrl++ / Ctrl+- / Ctrl+0 — font size
"Reference" tab — cheatsheet for the task topic
Tab / Shift+Tab — indent / outdent
Ctrl+S — save code to a file
F1 — this help</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="86"/>                                                                                    
                                                                                            <source>Тека даних: {folder}</source>                                                                                    
                                                                                            <translation>Data folder: {folder}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="93"/>                                                                                    
                                                                                            <source>Журнал: {target}</source>                                                                                    
                                                                                            <translation>Log: {target}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="98"/>                                                                                    
                                                                                            <source>Про тренажер</source>                                                                                    
                                                                                            <translation>About PyTrainer</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/dialogs.py" line="99"/>                                                                                    
                                                                                            <source>{ver} — тренажер Python з перевіркою коду.

Твій код виконується в окремому процесі Python із таймаутом 5 с і лімітом виводу, тому навіть while True і print у циклі не зашкодять програмі.

Прогрес, XP, підказки й черга повторень зберігаються в SQLite ({dbname}), а Python-Roadmap.md і progress.json оновлюються самі.

Тека даних: {datafolder}
Вона лежить поза синхронізованими теками (OneDrive, Dropbox), бо хмара посеред запису псує базу SQLite. Відкрити її можна з меню «Файл».

Розміри вікон, тема, масштаб шрифту й остання задача запам'ятовуються між запусками (pytrainer.ini).

Журнал і креш-логи: {logfolder}
Якщо вікно «просто закрилось» — останній crash-*.log там.</source>                                                                                    
                                                                                            <translation>{ver} — a Python trainer that runs your code and checks it.

Your code runs in a separate Python process with a 5 s timeout and an output cap, so even while True and print in a loop cannot harm the program.

Progress, XP, hints and the review queue live in SQLite ({dbname}); Python-Roadmap.md and progress.json update themselves.

Data folder: {datafolder}
It sits outside synced folders (OneDrive, Dropbox) — a cloud catching a mid-write corrupts the SQLite database. Open it from the File menu.

Window sizes, theme, font scale and the last task are remembered between runs (pytrainer.ini).

Journal and crash logs: {logfolder}
If the window "just closed" — the latest crash-*.log is there.</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>DigestDialog</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="45"/>                                                                                    
                                                                                            <source>Тижневий огляд</source>                                                                                    
                                                                                            <translation>Weekly digest</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="58"/>                                                                                    
                                                                                            <source>Огляд складається сам: із журналу спроб, черги повторень і журналу помилок. Це не оцінка, а відповідь на питання «що робити далі».</source>                                                                                    
                                                                                            <translation>The digest compiles itself: from the attempt journal, the review queue and the mistake journal. Not a grade — an answer to "what next".</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="73"/>                                                                                    
                                                                                            <source>здано нових</source>                                                                                    
                                                                                            <translation>new passed</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="74"/>                                                                                    
                                                                                            <source>перевірок</source>                                                                                    
                                                                                            <translation>checks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="75"/>                                                                                    
                                                                                            <source>успішних</source>                                                                                    
                                                                                            <translation>successful</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="76"/>                                                                                    
                                                                                            <source>днів із {n}</source>                                                                                    
                                                                                            <translation>days of {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="77"/>                                                                                    
                                                                                            <source>серія днів</source>                                                                                    
                                                                                            <translation>day streak</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="78"/>                                                                                    
                                                                                            <source>XP загалом</source>                                                                                    
                                                                                            <translation>total XP</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="85"/>                                                                                    
                                                                                            <source>ЩО ЗДАНО</source>                                                                                    
                                                                                            <translation>PASSED</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="86"/>                                                                                    
                                                                                            <source>НАЙВАЖЧЕ</source>                                                                                    
                                                                                            <translation>HARDEST</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="87"/>                                                                                    
                                                                                            <source>ПОМИЛКИ</source>                                                                                    
                                                                                            <translation>MISTAKES</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="88"/>                                                                                    
                                                                                            <source>ЩО РОБИТИ ДАЛІ</source>                                                                                    
                                                                                            <translation>WHAT NEXT</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="95"/>                                                                                    
                                                                                            <source>Зберегти звіт…</source>                                                                                    
                                                                                            <translation>Save report…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="98"/>                                                                                    
                                                                                            <source>Markdown-файл — його можна перечитати через місяць, коли цифри в тренажері вже інші</source>                                                                                    
                                                                                            <translation>A markdown file — reread it in a month, when the trainer's numbers are different</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="109"/>                                                                                    
                                                                                            <source>Закрити</source>                                                                                    
                                                                                            <translation>Close</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="164"/>                                                                                    
                                                                                            <source>Нічого — і це нормально, якщо тиждень був важкий.</source>                                                                                    
                                                                                            <translation>Nothing — and that's fine if the week was rough.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="168"/>                                                                                    
                                                                                            <source>⚠  {title} — {n} провалів</source>                                                                                    
                                                                                            <translation>⚠  {title} — {n} fails</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="171"/>                                                                                    
                                                                                            <source>Провалів не було.</source>                                                                                    
                                                                                            <translation>No fails.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="179"/>                                                                                    
                                                                                            <source>За тиждень жодної помилки в журналі.</source>                                                                                    
                                                                                            <translation>No mistakes in the journal this week.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="181"/>                                                                                    
                                                                                            <source>Усе зроблено 🎉</source>                                                                                    
                                                                                            <translation>All done 🎉</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="188"/>                                                                                    
                                                                                            <source>↻  Повторити: {n} задач — вони вже в черзі повторень</source>                                                                                    
                                                                                            <translation>↻  Review: {n} tasks — already in the review queue</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="195"/>                                                                                    
                                                                                            <source>⚠  Слабка тема{topic}: {pick}</source>                                                                                    
                                                                                            <translation>⚠  Weak topic{topic}: {pick}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="200"/>                                                                                    
                                                                                            <source>→  Нова задача: {title}</source>                                                                                    
                                                                                            <translation>→  New task: {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="224"/>                                                                                    
                                                                                            <source>Натисни, щоб відкрити задачу</source>                                                                                    
                                                                                            <translation>Click to open the task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="247"/>                                                                                    
                                                                                            <source>Зберегти тижневий звіт</source>                                                                                    
                                                                                            <translation>Save the weekly report</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="254"/>                                                                                    
                                                                                            <source>Не вдалося зберегти</source>                                                                                    
                                                                                            <translation>Could not save</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="255"/>                                                                                    
                                                                                            <source>Файл не записався.

{err}</source>                                                                                    
                                                                                            <translation>File was not written.

{err}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/digest_page.py" line="257"/>                                                                                    
                                                                                            <source>Збережено: {name}</source>                                                                                    
                                                                                            <translation>Saved: {name}</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>FileSync</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="74"/>                                                                                    
                                                                                            <source>Роадмап оновлено: {name}</source>                                                                                    
                                                                                            <translation>Roadmap updated: {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="87"/>                                                                                    
                                                                                            <source>Прогрес збережено: {name}</source>                                                                                    
                                                                                            <translation>Progress saved: {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="93"/>                                                                                    
                                                                                            <source>Експортувати прогрес</source>                                                                                    
                                                                                            <translation>Export progress</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="101"/>                                                                                    
                                                                                            <source>Прогрес експортовано: {name}</source>                                                                                    
                                                                                            <translation>Progress exported: {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="106"/>                                                                                    
                                                                                            <source>Імпортувати прогрес</source>                                                                                    
                                                                                            <translation>Import progress</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="113"/>                                                                                    
                                                                                            <source>Не вдалося прочитати</source>                                                                                    
                                                                                            <translation>Could not read</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="114"/>                                                                                    
                                                                                            <source>Файл не схожий на progress.json.

{err}</source>                                                                                    
                                                                                            <translation>File doesn't look like progress.json.

{err}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="122"/>                                                                                    
                                                                                            <source>Готово</source>                                                                                    
                                                                                            <translation>Done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="123"/>                                                                                    
                                                                                            <source>Відновлено задач: {n}.
Якщо задача вже була здана — її XP і черга повторень теж підтягнулись.</source>                                                                                    
                                                                                            <translation>Tasks restored: {n}.
Already-passed tasks pulled their XP and review queue along.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="136"/>                                                                                    
                                                                                            <source>Немає копій</source>                                                                                    
                                                                                            <translation>No backups</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="137"/>                                                                                    
                                                                                            <source>Тека копій порожня — відкочувати нічого.
Копії робляться самі при кожному запуску.</source>                                                                                    
                                                                                            <translation>Backup folder is empty — nothing to roll back.
Backups are made automatically on every launch.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="148"/>                                                                                    
                                                                                            <source>Відновити з копії</source>                                                                                    
                                                                                            <translation>Restore from backup</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="148"/>                                                                                    
                                                                                            <source>Копія:</source>                                                                                    
                                                                                            <translation>Backup:</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="155"/>                                                                                    
                                                                                            <source>Підтвердити відкат</source>                                                                                    
                                                                                            <translation>Confirm rollback</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="156"/>                                                                                    
                                                                                            <source>Поточна база буде замінена копією:
{name}

Прогрес, зроблений після цієї копії, зникне з вікна — але спершу він збережеться як окрема страхова копія, її можна повернути так само.

Продовжити?</source>                                                                                    
                                                                                            <translation>The current database will be replaced with the backup:
{name}

Progress made after this backup disappears from view — but first it is saved as a separate safety backup, restorable the same way.

Continue?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="179"/>                                                                                    
                                                                                            <source>Не вдалося відновити</source>                                                                                    
                                                                                            <translation>Could not restore</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="180"/>                                                                                    
                                                                                            <source>База не чіпалась.

{err}</source>                                                                                    
                                                                                            <translation>Database untouched.

{err}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="190"/>                                                                                    
                                                                                            <source>Базу відновлено з копії:
{name}
</source>                                                                                    
                                                                                            <translation>Database restored from backup:
{name}
</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="191"/>                                                                                    
                                                                                            <source>Поточний стан перед відкатом збережено як:
{name}</source>                                                                                    
                                                                                            <translation>Pre-rollback state saved as:
{name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="202"/>                                                                                    
                                                                                            <source>Немає що експортувати</source>                                                                                    
                                                                                            <translation>Nothing to export</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="203"/>                                                                                    
                                                                                            <source>Спершу здай хоча б одну задачу з тестами — і її код буде що експортувати.</source>                                                                                    
                                                                                            <translation>Pass at least one tested task first — then there is code to export.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="209"/>                                                                                    
                                                                                            <source>Куди зберегти розв'язані задачі</source>                                                                                    
                                                                                            <translation>Where to save solved tasks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="241"/>                                                                                    
                                                                                            <source>Експортовано {n} задач у {name}</source>                                                                                    
                                                                                            <translation>Exported {n} tasks to {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/file_sync.py" line="245"/>                                                                                    
                                                                                            <source>Збережено {n} файлів і README.md у папку:
{folder}

Наступний крок із роадмапу — викласти це на GitHub.</source>                                                                                    
                                                                                            <translation>Saved {n} files and README.md to:
{folder}

The roadmap's next step — put it on GitHub.</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>HintsView</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="54"/>                                                                                    
                                                                                            <source>Зняти позначку</source>                                                                                    
                                                                                            <translation>Unmark done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="54"/>                                                                                    
                                                                                            <source>Позначити виконаним</source>                                                                                    
                                                                                            <translation>Mark done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="88"/>                                                                                    
                                                                                            <source>Підказка {n} · {title}</source>                                                                                    
                                                                                            <translation>Hint {n} · {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="115"/>                                                                                    
                                                                                            <source>Вставити розв'язок у редактор</source>                                                                                    
                                                                                            <translation>Insert the solution into the editor</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="170"/>                                                                                    
                                                                                            <source>Розв'язок відкрито після достатньої роботи над задачею. Подивись — і спробуй переписати код своїми руками.</source>                                                                                    
                                                                                            <translation>The solution unlocked after enough work on the task. Take a look — then try rewriting the code by hand.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="180"/>                                                                                    
                                                                                            <source>Підказка {n} · розв'язок — заблоковано</source>                                                                                    
                                                                                            <translation>Hint {n} · solution locked</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="184"/>                                                                                    
                                                                                            <source>Відкриється через {left} активної роботи над задачею (з {total} хв). Працювало: {done}.</source>                                                                                    
                                                                                            <translation>Unlocks after {left} of active work on the task (of {total} min). Worked so far: {done}.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="201"/>                                                                                    
                                                                                            <source>Підказка {n} · недоступна в холодному повторенні</source>                                                                                    
                                                                                            <translation>Hint {n} · unavailable in cold review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="211"/>                                                                                    
                                                                                            <source>Розв'язок повернеться, щойно завершиш холодне повторення.</source>                                                                                    
                                                                                            <translation>The solution comes back once you finish the cold review.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="215"/>                                                                                    
                                                                                            <source>Холодне повторення: спершу згадай сам. Підказки повернуться після спроби.</source>                                                                                    
                                                                                            <translation>Cold review: recall it on your own first. Hints return after the attempt.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="226"/>                                                                                    
                                                                                            <source>Здаси зараз — отримаєш {n} XP</source>                                                                                    
                                                                                            <translation>Pass it now — earn {n} XP</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="230"/>                                                                                    
                                                                                            <source>база {n} XP</source>                                                                                    
                                                                                            <translation>base {n} XP</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="232"/>                                                                                    
                                                                                            <source>підказок відкрито: {n}</source>                                                                                    
                                                                                            <translation>hints opened: {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="248"/>                                                                                    
                                                                                            <source>Підказки 🔒</source>                                                                                    
                                                                                            <translation>Hints 🔒</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/hints_view.py" line="248"/>                                                                                    
                                                                                            <source>Підказки</source>                                                                                    
                                                                                            <translation>Hints</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>HistoryView</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="37"/>                                                                                    
                                                                                            <source>Ще жодного запуску цієї задачі.</source>                                                                                    
                                                                                            <translation>No runs of this task yet.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="40"/>                                                                                    
                                                                                            <source>здано ✓</source>                                                                                    
                                                                                            <translation>passed ✓</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="40"/>                                                                                    
                                                                                            <source>ще не здана</source>                                                                                    
                                                                                            <translation>not passed yet</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="42"/>                                                                                    
                                                                                            <source>Задача: {status} · XP: {xp} · підказок відкрито: {hints} · час над задачею: {time}</source>                                                                                    
                                                                                            <translation>Task: {status} · XP: {xp} · hints opened: {hints} · time on task: {time}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="51"/>                                                                                    
                                                                                            <source>запуск</source>                                                                                    
                                                                                            <translation>run</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/history_view.py" line="56"/>                                                                                    
                                                                                            <source>перевірка</source>                                                                                    
                                                                                            <translation>check</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>MainWindow</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="87"/>                                                                                    
                                                                                            <source>{ver} — тренажер Python</source>                                                                                    
                                                                                            <translation>{ver} — Python trainer</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="143"/>                                                                                    
                                                                                            <source>Файл</source>                                                                                    
                                                                                            <translation>File</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="144"/>                                                                                    
                                                                                            <source>Зберегти код…</source>                                                                                    
                                                                                            <translation>Save code…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="145"/>                                                                                    
                                                                                            <source>Скинути код до заготовки</source>                                                                                    
                                                                                            <translation>Reset code to starter</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="147"/>                                                                                    
                                                                                            <source>Експортувати розв'язані задачі…</source>                                                                                    
                                                                                            <translation>Export solved tasks…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="149"/>                                                                                    
                                                                                            <source>Експортувати прогрес…</source>                                                                                    
                                                                                            <translation>Export progress…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="150"/>                                                                                    
                                                                                            <source>Імпортувати прогрес…</source>                                                                                    
                                                                                            <translation>Import progress…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="151"/>                                                                                    
                                                                                            <source>Відновити з копії…</source>                                                                                    
                                                                                            <translation>Restore from backup…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="153"/>                                                                                    
                                                                                            <source>Відкрити теку з даними</source>                                                                                    
                                                                                            <translation>Open data folder</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="155"/>                                                                                    
                                                                                            <source>Відкрити файл журналу</source>                                                                                    
                                                                                            <translation>Open log file</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="158"/>                                                                                    
                                                                                            <source>Оновити Python-Roadmap.md</source>                                                                                    
                                                                                            <translation>Refresh Python-Roadmap.md</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="161"/>                                                                                    
                                                                                            <source>Вихід</source>                                                                                    
                                                                                            <translation>Quit</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="163"/>                                                                                    
                                                                                            <source>Запуск</source>                                                                                    
                                                                                            <translation>Run</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="164"/>                                                                                    
                                                                                            <source>Запустити</source>                                                                                    
                                                                                            <translation>Run</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="165"/>                                                                                    
                                                                                            <source>Перевірити тестами</source>                                                                                    
                                                                                            <translation>Check with tests</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="166"/>                                                                                    
                                                                                            <source>Розібрати мій код (рев'ю)</source>                                                                                    
                                                                                            <translation>Review my code</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="168"/>                                                                                    
                                                                                            <source>Очистити консоль</source>                                                                                    
                                                                                            <translation>Clear console</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="170"/>                                                                                    
                                                                                            <source>Навчання</source>                                                                                    
                                                                                            <translation>Study</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="171"/>                                                                                    
                                                                                            <source>План на сьогодні</source>                                                                                    
                                                                                            <translation>Today's plan</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="173"/>                                                                                    
                                                                                            <source>На повторення</source>                                                                                    
                                                                                            <translation>For review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="174"/>                                                                                    
                                                                                            <source>Холодне повторення (випадкова задача)</source>                                                                                    
                                                                                            <translation>Cold review (random task)</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="176"/>                                                                                    
                                                                                            <source>Прогрес і слабкі місця</source>                                                                                    
                                                                                            <translation>Progress and weak spots</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="178"/>                                                                                    
                                                                                            <source>Тижневий огляд</source>                                                                                    
                                                                                            <translation>Weekly digest</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="180"/>                                                                                    
                                                                                            <source>Наступна незавершена задача</source>                                                                                    
                                                                                            <translation>Next unfinished task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="182"/>                                                                                    
                                                                                            <source>Знайти задачу</source>                                                                                    
                                                                                            <translation>Find task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="184"/>                                                                                    
                                                                                            <source>Позначити виконаним (зроблено поза тренажером)</source>                                                                                    
                                                                                            <translation>Mark done (completed outside the trainer)</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="187"/>                                                                                    
                                                                                            <source>Скинути прогрес цієї задачі</source>                                                                                    
                                                                                            <translation>Reset this task's progress</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="190"/>                                                                                    
                                                                                            <source>Вигляд</source>                                                                                    
                                                                                            <translation>View</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="191"/>                                                                                    
                                                                                            <source>Темна / світла тема</source>                                                                                    
                                                                                            <translation>Dark / light theme</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="193"/>                                                                                    
                                                                                            <source>Більший шрифт</source>                                                                                    
                                                                                            <translation>Larger font</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="195"/>                                                                                    
                                                                                            <source>Менший шрифт</source>                                                                                    
                                                                                            <translation>Smaller font</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="197"/>                                                                                    
                                                                                            <source>Звичайний розмір шрифту</source>                                                                                    
                                                                                            <translation>Default font size</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="201"/>                                                                                    
                                                                                            <source>Мова: українська</source>                                                                                    
                                                                                            <translation>Language: Ukrainian</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="204"/>                                                                                    
                                                                                            <source>Мова: English</source>                                                                                    
                                                                                            <translation>Language: English</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="207"/>                                                                                    
                                                                                            <source>Довідка</source>                                                                                    
                                                                                            <translation>Help</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="208"/>                                                                                    
                                                                                            <source>Гарячі клавіші</source>                                                                                    
                                                                                            <translation>Keyboard shortcuts</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="209"/>                                                                                    
                                                                                            <source>Про тренажер</source>                                                                                    
                                                                                            <translation>About PyTrainer</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="226"/>                                                                                    
                                                                                            <source>▶  Запустити</source>                                                                                    
                                                                                            <translation>▶  Run</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="230"/>                                                                                    
                                                                                            <source>✓  Перевірити</source>                                                                                    
                                                                                            <translation>✓  Check</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="234"/>                                                                                    
                                                                                            <source>Підказка</source>                                                                                    
                                                                                            <translation>Hint</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="238"/>                                                                                    
                                                                                            <source>↺  Скинути</source>                                                                                    
                                                                                            <translation>↺  Reset</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="251"/>                                                                                    
                                                                                            <source>Сьогодні: 0 запусків</source>                                                                                    
                                                                                            <translation>Today: 0 runs</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="253"/>                                                                                    
                                                                                            <source>На повторення: 0</source>                                                                                    
                                                                                            <translation>For review: 0</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="257"/>                                                                                    
                                                                                            <source>Серія: 0 дн.</source>                                                                                    
                                                                                            <translation>Streak: 0 d</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="304"/>                                                                                    
                                                                                            <source>Ctrl+Enter — запустити · F5 — перевірити тестами</source>                                                                                    
                                                                                            <translation>Ctrl+Enter — run · F5 — check with tests</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="319"/>                                                                                    
                                                                                            <source>Тут з'явиться вивід твоєї програми…</source>                                                                                    
                                                                                            <translation>Your program's output appears here…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="332"/>                                                                                    
                                                                                            <source>КОНСОЛЬ</source>                                                                                    
                                                                                            <translation>CONSOLE</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="336"/>                                                                                    
                                                                                            <source>Очистити</source>                                                                                    
                                                                                            <translation>Clear</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="347"/>                                                                                    
                                                                                            <source>Готово</source>                                                                                    
                                                                                            <translation>Done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="351"/>                                                                                    
                                                                                            <source>Рядок 1, стовпець 1</source>                                                                                    
                                                                                            <translation>Line 1, column 1</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="390"/>                                                                                    
                                                                                            <source>Цей пункт робиться не в тренажері, а у твоєму терміналі — саме там навичка й закріплюється. Зробив? Познач галочкою, щоб вона з'явилась і в Python-Roadmap.md.</source>                                                                                    
                                                                                            <translation>This item is done in your own terminal, not in the trainer — that's where the skill sticks. Done? Tick it off so it shows in Python-Roadmap.md too.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="393"/>                                                                                    
                                                                                            <source>Задачу не знайдено.</source>                                                                                    
                                                                                            <translation>Task not found.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="398"/>                                                                                    
                                                                                            <source>Пункт поза тренажером — познач галочкою, коли зробиш</source>                                                                                    
                                                                                            <translation>Off-trainer item — tick it off when done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="399"/>                                                                                    
                                                                                            <source>Задачу не знайдено</source>                                                                                    
                                                                                            <translation>Task not found</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="436"/>                                                                                    
                                                                                            <source>❄ Холодне повторення: {title}. Підказки й розв'язок недоступні, час — до {mins} хв. Згадай сам — і тисни F5.</source>                                                                                    
                                                                                            <translation>❄ Cold review: {title}. No hints, no solution, up to {mins} min. Recall it on your own — then press F5.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="444"/>                                                                                    
                                                                                            <source>Повторення: {title}</source>                                                                                    
                                                                                            <translation>Review: {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="445"/>                                                                                    
                                                                                            <source>Відкрито: {title}</source>                                                                                    
                                                                                            <translation>Opened: {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="456"/>                                                                                    
                                                                                            <source>Усі задачі, які вже написані, здані 🎉</source>                                                                                    
                                                                                            <translation>All written tasks are passed 🎉</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="472"/>                                                                                    
                                                                                            <source>Холодне повторення — для вже зданих задач. Здай якусь задачу (крім відкритої зараз) — і воно стане доступним.</source>                                                                                    
                                                                                            <translation>Cold review is for already-passed tasks. Pass any task (other than the open one) — and it unlocks.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="483"/>                                                                                    
                                                                                            <source>з черги повторень</source>                                                                                    
                                                                                            <translation>from the review queue</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="484"/>                                                                                    
                                                                                            <source>випадкова зі зданих</source>                                                                                    
                                                                                            <translation>random from passed</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="486"/>                                                                                    
                                                                                            <source>❄ Холодне повторення · {source} · до {mins} хв</source>                                                                                    
                                                                                            <translation>❄ Cold review · {source} · up to {mins} min</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="498"/>                                                                                    
                                                                                            <source>Час вийшов. Допиши думку й тисни F5: краще здати як є, ніж просидіти над задачею до ночі.</source>                                                                                    
                                                                                            <translation>Time's up. Finish the thought and press F5: better to submit as-is than sit on the task till night.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="512"/>                                                                                    
                                                                                            <source>Холодне повторення завершено — підказки знову доступні, якщо захочеш пройти задачу спокійно.</source>                                                                                    
                                                                                            <translation>Cold review finished — hints are available again if you want to walk the task calmly.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="527"/>                                                                                    
                                                                                            <source>Спершу вибери пункт у плані зліва</source>                                                                                    
                                                                                            <translation>First pick an item in the plan on the left</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="532"/>                                                                                    
                                                                                            <source>Зняти позначку?</source>                                                                                    
                                                                                            <translation>Unmark?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="533"/>                                                                                    
                                                                                            <source>«{title}» повернеться в план як незавершений пункт.</source>                                                                                    
                                                                                            <translation>"{title}" returns to the plan as an unfinished item.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="539"/>                                                                                    
                                                                                            <source>Позначку знято: {title}</source>                                                                                    
                                                                                            <translation>Unmarked: {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="543"/>                                                                                    
                                                                                            <source>Позначено виконаним: {title}</source>                                                                                    
                                                                                            <translation>Marked done: {title}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="564"/>                                                                                    
                                                                                            <source>Скинути код?</source>                                                                                    
                                                                                            <translation>Reset code?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="565"/>                                                                                    
                                                                                            <source>Поточний код буде замінено на заготовку. Продовжити?</source>                                                                                    
                                                                                            <translation>Current code will be replaced with the starter. Continue?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="571"/>                                                                                    
                                                                                            <source>Код скинуто до заготовки</source>                                                                                    
                                                                                            <translation>Code reset to starter</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="577"/>                                                                                    
                                                                                            <source>Скинути прогрес задачі?</source>                                                                                    
                                                                                            <translation>Reset task progress?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="578"/>                                                                                    
                                                                                            <source>Прогрес «{title}» буде стерто: спроби, XP, підказки, черга повторень. Далі — як уперше.</source>                                                                                    
                                                                                            <translation>Progress for "{title}" will be wiped: attempts, XP, hints, review queue. Then — as if first time.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="585"/>                                                                                    
                                                                                            <source>Прогрес задачі скинуто</source>                                                                                    
                                                                                            <translation>Task progress reset</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="589"/>                                                                                    
                                                                                            <source>Зберегти код</source>                                                                                    
                                                                                            <translation>Save code</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="595"/>                                                                                    
                                                                                            <source>Збережено: {name}</source>                                                                                    
                                                                                            <translation>Saved: {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="606"/>                                                                                    
                                                                                            <source>Ввід для запуску: {feed}</source>                                                                                    
                                                                                            <translation>Run input: {feed}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="609"/>                                                                                    
                                                                                            <source>У цій задачі є файли: {files}</source>                                                                                    
                                                                                            <translation>This task has files: {files}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="628"/>                                                                                    
                                                                                            <source>У файлі немає рядка {n}</source>                                                                                    
                                                                                            <translation>File has no line {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="640"/>                                                                                    
                                                                                            <source>Рядок {n} — саме тут сталася помилка</source>                                                                                    
                                                                                            <translation>Line {n} — the error happened right here</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="656"/>                                                                                    
                                                                                            <source>Тренуємо тему: {topic}</source>                                                                                    
                                                                                            <translation>Training topic: {topic}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="661"/>                                                                                    
                                                                                            <source>У темі «{topic}» усі задачі здані — час на повторення</source>                                                                                    
                                                                                            <translation>All tasks in "{topic}" are passed — time to review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="701"/>                                                                                    
                                                                                            <source>Спершу вибери задачу з плану зліва</source>                                                                                    
                                                                                            <translation>First pick a task from the plan on the left</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="707"/>                                                                                    
                                                                                            <source>Рев'ю коду: {summary}</source>                                                                                    
                                                                                            <translation>Code review: {summary}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="737"/>                                                                                    
                                                                                            <source>» Рев'ю коду: {phrase} — вкладка «Рев'ю»</source>                                                                                    
                                                                                            <translation>» Code review: {phrase} — the "Review" tab</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="757"/>                                                                                    
                                                                                            <source>Підказка {n} — XP за задачу тепер {xp}</source>                                                                                    
                                                                                            <translation>Hint {n} — task XP now {xp}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="765"/>                                                                                    
                                                                                            <source>Вставити розв'язок?</source>                                                                                    
                                                                                            <translation>Insert solution?</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="766"/>                                                                                    
                                                                                            <source>Код у редакторі буде замінено готовим розв'язком.

XP за цю задачу впаде до {price}, а сама задача потрапить у чергу повторень.

Усе одно спробуй перебрати код руками — інакше на наступній задачі буде так само важко.</source>                                                                                    
                                                                                            <translation>Editor code will be replaced with the ready solution.

Task XP drops to {price}, and the task lands in the review queue.

Still, try retyping the code by hand — otherwise the next task will hurt the same way.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="779"/>                                                                                    
                                                                                            <source>Розв'язок вставлено в редактор. Перепиши його своїми руками — це і є вправа.</source>                                                                                    
                                                                                            <translation>Solution inserted into the editor. Retype it by hand — that is the exercise.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="816"/>                                                                                    
                                                                                            <source>❄ Холодне повторення · лишилось {m}:{s:02d}</source>                                                                                    
                                                                                            <translation>❄ Cold review · {m}:{s:02d} left</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="819"/>                                                                                    
                                                                                            <source>❄ Холодне повторення · час вийшов — здай як є (F5)</source>                                                                                    
                                                                                            <translation>❄ Cold review · time's up — submit as-is (F5)</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="825"/>                                                                                    
                                                                                            <source>Здано ✓ · час над задачею {m} хв</source>                                                                                    
                                                                                            <translation>Passed ✓ · time on task {m} min</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="832"/>                                                                                    
                                                                                            <source>Час над задачею {clock} · розв'язок через {m}:{s:02d}</source>                                                                                    
                                                                                            <translation>Time on task {clock} · solution in {m}:{s:02d}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="837"/>                                                                                    
                                                                                            <source>Час над задачею {clock} · розв'язок відкрито</source>                                                                                    
                                                                                            <translation>Time on task {clock} · solution unlocked</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="919"/>                                                                                    
                                                                                            <source>⏳  Виконується…</source>                                                                                    
                                                                                            <translation>⏳  Running…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="920"/>                                                                                    
                                                                                            <source>⏳  Перевіряю…</source>                                                                                    
                                                                                            <translation>⏳  Checking…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="933"/>                                                                                    
                                                                                            <source>Рядок {line}, стовпець {col}</source>                                                                                    
                                                                                            <translation>Line {line}, column {col}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1053"/>                                                                                    
                                                                                            <source>Тема: {name}</source>                                                                                    
                                                                                            <translation>Topic: {name}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1054"/>                                                                                    
                                                                                            <source>світла</source>                                                                                    
                                                                                            <translation>light</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1054"/>                                                                                    
                                                                                            <source>темна</source>                                                                                    
                                                                                            <translation>dark</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1064"/>                                                                                    
                                                                                            <source>Масштаб шрифту: {n}%</source>                                                                                    
                                                                                            <translation>Font scale: {n}%</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1070"/>                                                                                    
                                                                                            <source>Масштаб шрифту: 100%</source>                                                                                    
                                                                                            <translation>Font scale: 100%</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/main_window.py" line="1078"/>                                                                                    
                                                                                            <source>Мову змінено — перезапусти вікно</source>                                                                                    
                                                                                            <translation>Language changed — restart the window</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>PlanPage</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="38"/>                                                                                    
                                                                                            <source>повторення</source>                                                                                    
                                                                                            <translation>review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="39"/>                                                                                    
                                                                                            <source>слабке місце</source>                                                                                    
                                                                                            <translation>weak spot</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="40"/>                                                                                    
                                                                                            <source>нова задача</source>                                                                                    
                                                                                            <translation>new task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="47"/>                                                                                    
                                                                                            <source>{h} год {m} хв</source>                                                                                    
                                                                                            <translation>{h} h {m} min</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="49"/>                                                                                    
                                                                                            <source>{h} год</source>                                                                                    
                                                                                            <translation>{h} h</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="50"/>                                                                                    
                                                                                            <source>{m} хв</source>                                                                                    
                                                                                            <translation>{m} min</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="64"/>                                                                                    
                                                                                            <source>План на сьогодні</source>                                                                                    
                                                                                            <translation>Today's plan</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="80"/>                                                                                    
                                                                                            <source>Усе написане вже здано 🎉 Наступні блоки плану ще в розробці — а поки що повертайся до слабких тем, щоб не втратити форму.</source>                                                                                    
                                                                                            <translation>Everything written is already passed 🎉 The next plan blocks are still in development — meanwhile revisit weak topics to stay in shape.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="93"/>                                                                                    
                                                                                            <source>План на сьогодні порожній</source>                                                                                    
                                                                                            <translation>Today's plan is empty</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="95"/>                                                                                    
                                                                                            <source>Це не помилка: або все здано, або черга повторень порожня.</source>                                                                                    
                                                                                            <translation>Not an error: either everything is passed or the review queue is empty.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="101"/>                                                                                    
                                                                                            <source>План на сьогодні · {n} кроків · ≈{time}</source>                                                                                    
                                                                                            <translation>Today's plan · {n} steps · ≈{time}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="105"/>                                                                                    
                                                                                            <source>Порядок не випадковий: спершу те, що ось-ось забудеться, потім слабке місце, і аж потім нове.</source>                                                                                    
                                                                                            <translation>The order is deliberate: first what is about to be forgotten, then the weak spot, and only then something new.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/plan_page.py" line="114"/>                                                                                    
                                                                                            <source>хв</source>                                                                                    
                                                                                            <translation>min</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>RefreshView</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="40"/>                                                                                    
                                                                                            <source>сьогодні</source>                                                                                    
                                                                                            <translation>today</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="42"/>                                                                                    
                                                                                            <source>учора</source>                                                                                    
                                                                                            <translation>yesterday</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="55"/>                                                                                    
                                                                                            <source>{date} · прострочено</source>                                                                                    
                                                                                            <translation>{date} · overdue</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="57"/>                                                                                    
                                                                                            <source>{date} · сьогодні</source>                                                                                    
                                                                                            <translation>{date} · today</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="58"/>                                                                                    
                                                                                            <source>{date} · через {n} дн.</source>                                                                                    
                                                                                            <translation>{date} · in {n} d</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="99"/>                                                                                    
                                                                                            <source>перевірка</source>                                                                                    
                                                                                            <translation>review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="101"/>                                                                                    
                                                                                            <source>Закрито з допомогою — згадай задачу холодним повторенням</source>                                                                                    
                                                                                            <translation>Closed with help — recall the task in a cold review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="103"/>                                                                                    
                                                                                            <source>Натисни, щоб повернутися до задачі</source>                                                                                    
                                                                                            <translation>Click to return to the task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="141"/>                                                                                    
                                                                                            <source>{date} · інтервал {n} дн.</source>                                                                                    
                                                                                            <translation>{date} · every {n} d</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="160"/>                                                                                    
                                                                                            <source>На повторення: {n}</source>                                                                                    
                                                                                            <translation>For review: {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="178"/>                                                                                    
                                                                                            <source>Серія: {n} дн.</source>                                                                                    
                                                                                            <translation>Streak: {n} d</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="179"/>                                                                                    
                                                                                            <source>Серія: 1 день</source>                                                                                    
                                                                                            <translation>Streak: 1 day</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="188"/>                                                                                    
                                                                                            <source>Сьогодні: {n} запусків ✓</source>                                                                                    
                                                                                            <translation>Today: {n} runs ✓</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="193"/>                                                                                    
                                                                                            <source>Сьогодні: 0 — не втрать серію</source>                                                                                    
                                                                                            <translation>Today: 0 — keep the streak alive</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/refresh_view.py" line="196"/>                                                                                    
                                                                                            <source>Сьогодні: 0 запусків</source>                                                                                    
                                                                                            <translation>Today: 0 runs</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>ReviewPage</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="41"/>                                                                                    
                                                                                            <source>Задачі повертаються через 1 / 3 / 7 / 30 днів після того, як ти здав їх не з першого разу. Натисни на задачу, щоб повторити.</source>                                                                                    
                                                                                            <translation>Tasks come back 1 / 3 / 7 / 30 days after a non-first-try pass. Click a task to review it.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="48"/>                                                                                    
                                                                                            <source>❄  Холодне повторення: випадкова задача</source>                                                                                    
                                                                                            <translation>❄  Cold review: a random task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="52"/>                                                                                    
                                                                                            <source>Уже здана задача без підказок і розв'язку, з таймером. Вердикт іде в чергу повторень: згадав — інтервал довший, не згадав — задача повертається завтра.</source>                                                                                    
                                                                                            <translation>An already-passed task with no hints and no solution, on a timer. The verdict feeds the review queue: recalled — longer interval, didn't — the task returns tomorrow.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="62"/>                                                                                    
                                                                                            <source>СЬОГОДНІ</source>                                                                                    
                                                                                            <translation>TODAY</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="72"/>                                                                                    
                                                                                            <source>ДАЛІ</source>                                                                                    
                                                                                            <translation>LATER</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="79"/>                                                                                    
                                                                                            <source>Черга порожня. Здавай задачі — і тут з'явиться розклад повторень.</source>                                                                                    
                                                                                            <translation>Queue is empty. Pass tasks — and the review schedule appears here.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="85"/>                                                                                    
                                                                                            <source>ТВОЇ ПОМИЛКИ</source>                                                                                    
                                                                                            <translation>YOUR MISTAKES</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="90"/>                                                                                    
                                                                                            <source>Помилка, на якій спіткнувся, — найкорисніше, що є в цьому тренажері. Натисни, щоб повернутися до задачі.</source>                                                                                    
                                                                                            <translation>The mistake you tripped on is the most useful thing in this trainer. Click to return to the task.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_page.py" line="168"/>                                                                                    
                                                                                            <source>Помилка «висить», доки задачу не здано чистим проходом — без підказок і розв'язку. Жовте «закрито з допомогою» означає, що задачу варто згадати холодним повторенням.</source>                                                                                    
                                                                                            <translation>A mistake "hangs" until the task is passed cleanly — no hints, no solution. Yellow "closed with help" means the task is worth recalling in a cold review.</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>ReviewView</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="47"/>                                                                                    
                                                                                            <source>Рев'ю · {n}</source>                                                                                    
                                                                                            <translation>Review · {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="47"/>                                                                                    
                                                                                            <source>Рев'ю</source>                                                                                    
                                                                                            <translation>Review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="49"/>                                                                                    
                                                                                            <source>Розібрати ще раз</source>                                                                                    
                                                                                            <translation>Review again</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="60"/>                                                                                    
                                                                                            <source>Розібрати код</source>                                                                                    
                                                                                            <translation>Review code</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="87"/>                                                                                    
                                                                                            <source>Рядок {n}</source>                                                                                    
                                                                                            <translation>Line {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/review_view.py" line="96"/>                                                                                    
                                                                                            <source>↪  Рядок {n}</source>                                                                                    
                                                                                            <translation>↪  Line {n}</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>RoadmapTree</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="84"/>                                                                                    
                                                                                            <source>заплановано</source>                                                                                    
                                                                                            <translation>planned</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>RunFlow</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="57"/>                                                                                    
                                                                                            <source>Перевірка тестами</source>                                                                                    
                                                                                            <translation>Checking with tests</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="57"/>                                                                                    
                                                                                            <source>Запуск коду</source>                                                                                    
                                                                                            <translation>Running code</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="60"/>                                                                                    
                                                                                            <source>→ Ввід: {stdin}</source>                                                                                    
                                                                                            <translation>→ Input: {stdin}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="81"/>                                                                                    
                                                                                            <source>(вивід порожній)</source>                                                                                    
                                                                                            <translation>(output empty)</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="83"/>                                                                                    
                                                                                            <source>…вивід обрізано, щоб не з'їсти пам'ять</source>                                                                                    
                                                                                            <translation>…output truncated to save memory</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="102"/>                                                                                    
                                                                                            <source>Код виконано</source>                                                                                    
                                                                                            <translation>Code ran</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="128"/>                                                                                    
                                                                                            <source>Задача здана! +{xp} XP</source>                                                                                    
                                                                                            <translation>Task passed! +{xp} XP</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="130"/>                                                                                    
                                                                                            <source>бонус за повторення +{xp} XP</source>                                                                                    
                                                                                            <translation>review bonus +{xp} XP</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="132"/>                                                                                    
                                                                                            <source>Усі перевірки пройдено · {parts}</source>                                                                                    
                                                                                            <translation>All checks passed · {parts}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="137"/>                                                                                    
                                                                                            <source>❄ Холодне повторення: згадав без підказок ✓</source>                                                                                    
                                                                                            <translation>❄ Cold review: recalled with no hints ✓</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="140"/>                                                                                    
                                                                                            <source>Задача утримана — більше не в черзі повторень 🎯</source>                                                                                    
                                                                                            <translation>Task retained — out of the review queue 🎯</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="145"/>                                                                                    
                                                                                            <source>Пройдено {passed} із {total}</source>                                                                                    
                                                                                            <translation>Passed {passed} of {total}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="152"/>                                                                                    
                                                                                            <source>❄ Холодне повторення: не згадав — задача повернеться в чергу. Це нормально: саме такі прогалини й ловляться.</source>                                                                                    
                                                                                            <translation>❄ Cold review: didn't recall — the task returns to the queue. That's fine: catching gaps like this is the point.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/run_flow.py" line="156"/>                                                                                    
                                                                                            <source>Є помилки — дивись вкладку «Тести»</source>                                                                                    
                                                                                            <translation>There are errors — see the "Tests" tab</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>SideNav</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="219"/>                                                                                    
                                                                                            <source>Шлях: від нуля до перших грошей</source>                                                                                    
                                                                                            <translation>Path: from zero to first earnings</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="232"/>                                                                                    
                                                                                            <source>0 із 0 пройдено</source>                                                                                    
                                                                                            <translation>0 of 0 done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="249"/>                                                                                    
                                                                                            <source>Пошук задачі…</source>                                                                                    
                                                                                            <translation>Search tasks…</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="267"/>                                                                                    
                                                                                            <source>Знайдено задач: {n}</source>                                                                                    
                                                                                            <translation>Tasks found: {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="281"/>                                                                                    
                                                                                            <source>Шлях</source>                                                                                    
                                                                                            <translation>Path</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="281"/>                                                                                    
                                                                                            <source>План від нуля до перших грошей</source>                                                                                    
                                                                                            <translation>Plan from zero to first earnings</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="282"/>                                                                                    
                                                                                            <source>Повтор</source>                                                                                    
                                                                                            <translation>Review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="282"/>                                                                                    
                                                                                            <source>Черга повторень: що час згадати</source>                                                                                    
                                                                                            <translation>Review queue: what's due</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="283"/>                                                                                    
                                                                                            <source>Прогрес</source>                                                                                    
                                                                                            <translation>Progress</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="283"/>                                                                                    
                                                                                            <source>Скільки здано, XP, серія днів, слабкі місця</source>                                                                                    
                                                                                            <translation>Passed count, XP, day streak, weak spots</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="284"/>                                                                                    
                                                                                            <source>План</source>                                                                                    
                                                                                            <translation>Plan</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="284"/>                                                                                    
                                                                                            <source>Що робити сьогодні — готовий план на вечір</source>                                                                                    
                                                                                            <translation>What to do today — an evening plan, ready</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="335"/>                                                                                    
                                                                                            <source>{done} із {total} пройдено</source>                                                                                    
                                                                                            <translation>{done} of {total} done</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="343"/>                                                                                    
                                                                                            <source>Повторення · {n}</source>                                                                                    
                                                                                            <translation>Review · {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="344"/>                                                                                    
                                                                                            <source>Повторення</source>                                                                                    
                                                                                            <translation>Review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="346"/>                                                                                    
                                                                                            <source>Час повторити: {n}</source>                                                                                    
                                                                                            <translation>Due for review: {n}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="347"/>                                                                                    
                                                                                            <source>Черга повторень порожня</source>                                                                                    
                                                                                            <translation>Review queue is empty</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="362"/>                                                                                    
                                                                                            <source>План на сьогодні: {n} кроків, ≈{time} хв</source>                                                                                    
                                                                                            <translation>Today's plan: {n} steps, ≈{time} min</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="364"/>                                                                                    
                                                                                            <source>План на сьогодні порожній</source>                                                                                    
                                                                                            <translation>Today's plan is empty</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/sidebar.py" line="370"/>                                                                                    
                                                                                            <source>Повторень: {reviews} · помилок у журналі: {mistakes}</source>                                                                                    
                                                                                            <translation>Reviews: {reviews} · mistakes in journal: {mistakes}</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>StatsPage</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="161"/>                                                                                    
                                                                                            <source>здано задач</source>                                                                                    
                                                                                            <translation>tasks passed</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="162"/>                                                                                    
                                                                                            <source>утримано</source>                                                                                    
                                                                                            <translation>retained</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="164"/>                                                                                    
                                                                                            <source>серія днів</source>                                                                                    
                                                                                            <translation>day streak</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="165"/>                                                                                    
                                                                                            <source>успішність спроб</source>                                                                                    
                                                                                            <translation>attempt success</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="166"/>                                                                                    
                                                                                            <source>час у тренажері</source>                                                                                    
                                                                                            <translation>time in trainer</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="174"/>                                                                                    
                                                                                            <source>Тижневий огляд · 7 днів</source>                                                                                    
                                                                                            <translation>Weekly digest · 7 days</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="178"/>                                                                                    
                                                                                            <source>Що сталося за тиждень: скільки здано, на чому спіткнувся, що робити далі. Звіт можна зберегти файлом.</source>                                                                                    
                                                                                            <translation>What happened this week: how much passed, what tripped you, what next. The report can be saved to a file.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="191"/>                                                                                    
                                                                                            <source>СЛАБКІ МІСЦЯ</source>                                                                                    
                                                                                            <translation>WEAK SPOTS</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="201"/>                                                                                    
                                                                                            <source>Натисни на тему — тренажер відкриє задачу, на якій її можна підтягнути.</source>                                                                                    
                                                                                            <translation>Click a topic — the trainer opens a task to drill it.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="209"/>                                                                                    
                                                                                            <source>Поки що все рівно. Слабкі теми з'являться, коли буде кілька провалів — і саме їх тренажер підсвітить.</source>                                                                                    
                                                                                            <translation>Even so far. Weak topics appear after a few fails — and the trainer highlights exactly those.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="216"/>                                                                                    
                                                                                            <source>XP ЗА 4 ТИЖНІ</source>                                                                                    
                                                                                            <translation>XP OVER 4 WEEKS</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="223"/>                                                                                    
                                                                                            <source>АКТИВНІСТЬ · 8 ТИЖНІВ</source>                                                                                    
                                                                                            <translation>ACTIVITY · 8 WEEKS</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="229"/>                                                                                    
                                                                                            <source>кожна клітинка — день, насиченіший колір = більше запусків</source>                                                                                    
                                                                                            <translation>each cell is a day, richer color = more runs</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="260"/>                                                                                    
                                                                                            <source>{n} год</source>                                                                                    
                                                                                            <translation>{n} h</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="267"/>                                                                                    
                                                                                            <source>успішних спроб {rate}% ({passes} із {attempts}) · здано {done}/{total}</source>                                                                                    
                                                                                            <translation>{rate}% successful attempts ({passes} of {attempts}) · passed {done}/{total}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="275"/>                                                                                    
                                                                                            <source>Натисни, щоб тренувати цю тему</source>                                                                                    
                                                                                            <translation>Click to drill this topic</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="291"/>                                                                                    
                                                                                            <source>Цього тижня занять ще не було.</source>                                                                                    
                                                                                            <translation>No sessions this week yet.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="295"/>                                                                                    
                                                                                            <source>Тиждень: {checks} {checks_form} ({passes} успішних) · здано {solved} · відкрито {open} {open_form}</source>                                                                                    
                                                                                            <translation>Week: {checks} {checks_form} ({passes} successful) · passed {solved} · opened {open} {open_form}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="298"/>                                                                                    
                                                                                            <source>перевірка</source>                                                                                    
                                                                                            <translation>check</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="299"/>                                                                                    
                                                                                            <source>перевірки</source>                                                                                    
                                                                                            <translation>checks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="299"/>                                                                                    
                                                                                            <source>перевірок</source>                                                                                    
                                                                                            <translation>checks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="302"/>                                                                                    
                                                                                            <source>помилка</source>                                                                                    
                                                                                            <translation>mistake</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="303"/>                                                                                    
                                                                                            <source>помилки</source>                                                                                    
                                                                                            <translation>mistakes</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="303"/>                                                                                    
                                                                                            <source>помилок</source>                                                                                    
                                                                                            <translation>mistakes</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>TaskPanel</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="193"/>                                                                                    
                                                                                            <source>Задача</source>                                                                                    
                                                                                            <translation>Task</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="194"/>                                                                                    
                                                                                            <source>Тести</source>                                                                                    
                                                                                            <translation>Tests</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="195"/>                                                                                    
                                                                                            <source>Рев'ю</source>                                                                                    
                                                                                            <translation>Review</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="196"/>                                                                                    
                                                                                            <source>Довідка</source>                                                                                    
                                                                                            <translation>Reference</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="197"/>                                                                                    
                                                                                            <source>Підказки</source>                                                                                    
                                                                                            <translation>Hints</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="198"/>                                                                                    
                                                                                            <source>Історія</source>                                                                                    
                                                                                            <translation>History</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="257"/>                                                                                    
                                                                                            <source>Ще не перевірялося</source>                                                                                    
                                                                                            <translation>Not checked yet</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="293"/>                                                                                    
                                                                                            <source>Розібрати код</source>                                                                                    
                                                                                            <translation>Review code</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="297"/>                                                                                    
                                                                                            <source>Розбір не оцінює і не перевіряє: він каже, що в коді буде важко читати іншій людині — і як це виправити (F6)</source>                                                                                    
                                                                                            <translation>Review neither grades nor checks: it tells you what another human will find hard to read in your code — and how to fix it (F6)</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="329"/>                                                                                    
                                                                                            <source>Міні-довідка з теми задачі. Можна вибрати будь-яку іншу — це не впливає на XP.</source>                                                                                    
                                                                                            <translation>Mini-reference for the task topic. Pick any other — it doesn't affect XP.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="358"/>                                                                                    
                                                                                            <source>Холодне повторення: підказки й розв'язок недоступні, доки не завершиш спробу. Саме в цьому суть — згадати самому.</source>                                                                                    
                                                                                            <translation>Cold review: hints and solution stay locked until you finish the attempt. That's the point — recall it on your own.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="383"/>                                                                                    
                                                                                            <source>Історії ще немає</source>                                                                                    
                                                                                            <translation>No history yet</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="429"/>                                                                                    
                                                                                            <source>Виконано поза тренажером</source>                                                                                    
                                                                                            <translation>Done outside the trainer</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="429"/>                                                                                    
                                                                                            <source>План</source>                                                                                    
                                                                                            <translation>Plan</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="433"/>                                                                                    
                                                                                            <source>Цей пункт не перевіряється тестами: зроби його у своєму терміналі й познач галочкою.</source>                                                                                    
                                                                                            <translation>This item isn't checked by tests: do it in your own terminal and tick it off.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/task_panel.py" line="629"/>                                                                                    
                                                                                            <source>Джерело задачі: {credit}. Умова переказана українською, перевірки — власні.</source>                                                                                    
                                                                                            <translation>Task source: {credit}. Statement retold in English, checks are our own.</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>TestResults</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="122"/>                                                                                    
                                                                                            <source>перевірка виводу програми</source>                                                                                    
                                                                                            <translation>program output check</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="122"/>                                                                                    
                                                                                            <source>перевірка коду</source>                                                                                    
                                                                                            <translation>code check</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="131"/>                                                                                    
                                                                                            <source>Це пункт поза тренажером</source>                                                                                    
                                                                                            <translation>This is an off-trainer item</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="133"/>                                                                                    
                                                                                            <source>Тут немає прихованих тестів — результат оцінюєш ти сам.</source>                                                                                    
                                                                                            <translation>No hidden tests here — you grade the result yourself.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="138"/>                                                                                    
                                                                                            <source>перевірка</source>                                                                                    
                                                                                            <translation>check</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="139"/>                                                                                    
                                                                                            <source>перевірки</source>                                                                                    
                                                                                            <translation>checks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="140"/>                                                                                    
                                                                                            <source>перевірок</source>                                                                                    
                                                                                            <translation>checks</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="142"/>                                                                                    
                                                                                            <source>Буде {n} {form} — ще не запускались</source>                                                                                    
                                                                                            <translation>{n} {form} — not run yet</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="152"/>                                                                                    
                                                                                            <source>Перевірки приховані: ти бачиш, що саме вони вимагають, але не сам код тесту. Натисни «Перевірити» (F5), щоб прогнати їх.</source>                                                                                    
                                                                                            <translation>Checks are hidden: you see what they demand, but not the test code itself. Press "Check" (F5) to run them.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="174"/>                                                                                    
                                                                                            <source>пройдено</source>                                                                                    
                                                                                            <translation>passed</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="179"/>                                                                                    
                                                                                            <source>Насправді вивела:
{lines}</source>                                                                                    
                                                                                            <translation>Actually printed:
{lines}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="192"/>                                                                                    
                                                                                            <source>Усі перевірки пройдено: {passed} із {total} ✓</source>                                                                                    
                                                                                            <translation>All checks passed: {passed} of {total} ✓</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="198"/>                                                                                    
                                                                                            <source>Пройдено {passed} із {total} — є що виправити</source>                                                                                    
                                                                                            <translation>Passed {passed} of {total} — something to fix</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="205"/>                                                                                    
                                                                                            <source>Код зупинено за таймаутом</source>                                                                                    
                                                                                            <translation>Code stopped on timeout</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="209"/>                                                                                    
                                                                                            <source>Код впав з помилкою</source>                                                                                    
                                                                                            <translation>Code crashed with an error</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="213"/>                                                                                    
                                                                                            <source>Код виконано без помилок</source>                                                                                    
                                                                                            <translation>Code ran with no errors</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="215"/>                                                                                    
                                                                                            <source>Це був звичайний запуск. Натисни «Перевірити» (F5), щоб прогнати приховані тести.</source>                                                                                    
                                                                                            <translation>That was a plain run. Press "Check" (F5) to run the hidden tests.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="230"/>                                                                                    
                                                                                            <source>Так тримати! Наступна задача — у списку зліва (Ctrl+N).</source>                                                                                    
                                                                                            <translation>Keep it up! Next task is in the list on the left (Ctrl+N).</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="235"/>                                                                                    
                                                                                            <source>Перша проблема: {err}</source>                                                                                    
                                                                                            <translation>First problem: {err}</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="236"/>                                                                                    
                                                                                            <source>Подивись, яка саме перевірка впала, вище.</source>                                                                                    
                                                                                            <translation>See which check failed, above.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="243"/>                                                                                    
                                                                                            <source>Що це означає</source>                                                                                    
                                                                                            <translation>What this means</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="249"/>                                                                                    
                                                                                            <source>Помилка — це підказка, а не вирок: Python каже, де саме код розійшовся з твоїм задумом.</source>                                                                                    
                                                                                            <translation>An error is a hint, not a verdict: Python tells you exactly where the code diverged from your intent.</translation>                                                                                    
                                                            </message>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/test_results.py" line="265"/>                                                                                    
                                                                                            <source>↪  Перейти до рядка {n}</source>                                                                                    
                                                                                            <translation>↪  Go to line {n}</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
                            <context>                                                        
                                                            <name>XpChart</name>                                                        
                                                            <message>                                                                                    
                                                                                            <location filename="../trainer/ui/stats_page.py" line="141"/>                                                                                    
                                                                                            <source>найкращий день: {n} XP</source>                                                                                    
                                                                                            <translation>best day: {n} XP</translation>                                                                                    
                                                            </message>                                                        
                            </context>                            
</TS>