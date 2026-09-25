"""Службовий скрипт для розробки.

Складає один HTML з одного або кількох PNG-знімків (вбудованих у base64),
щоб показати їх у панелі Preview без окремого веб-сервера.

    .venv\\Scripts\\python.exe tools/preview_screenshot.py screenshots/main.png screenshots/progress.png
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

STYLE = """
    :root { color-scheme: dark; }
    body { margin: 0; background: #08090c; color: #dfe3ea;
           font-family: 'Segoe UI', system-ui, sans-serif; }
    header { padding: 14px 22px; border-bottom: 1px solid #272b36; }
    h1 { font-size: 15px; margin: 0 0 4px 0; font-weight: 600; }
    p { margin: 0; color: #8a92a3; font-size: 12px; }
    main { padding: 18px; display: grid; gap: 22px; }
    figure { margin: 0; }
    figcaption { font-size: 12px; color: #8a92a3; margin-bottom: 8px; }
    img { width: 100%; border: 1px solid #272b36; border-radius: 10px;
          box-shadow: 0 18px 40px rgba(0,0,0,.45); }
"""

CAPTIONS = {
    "01-roadmap": "Головне вікно: план зліва, редактор по центру, умова й перевірки справа",
    "02-checks": "Перевірка коду: приховані тести, вердикт і консоль із виводом",
    "03-progress": "Режим «Прогрес»: здано / утримано, XP, серія днів, слабкі місця",
    "04-reviews": "Режим «Повторення»: черга задач, які час згадати",
    "05-error-help": "Пояснення помилки українською: що це означає і що робити",
    "06-cheatsheet": "Міні-довідка з теми задачі — вкладка «Довідка»",
    "07-light": "Світла тема й масштаб тексту (меню «Вигляд»)",
    "main": "Головне вікно",
    "progress": "Екран прогресу",
    "reviews": "Черга повторень",
}


def build_html(paths: list[Path], out: Path | None = None) -> Path:
    figures = []
    total_kb = 0
    for path in paths:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        total_kb += path.stat().st_size // 1024
        caption = CAPTIONS.get(path.stem, path.stem)
        figures.append(
            f'<figure><figcaption>{caption}</figcaption>'
            f'<img src="data:image/png;base64,{data}" alt="{caption}"></figure>'
        )

    html = f"""<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<title>PyTrainer — вигляд застосунку</title>
<style>{STYLE}</style>
</head>
<body>
<header>
  <h1>PyTrainer — вигляд застосунку</h1>
  <p>{len(paths)} знімки · {total_kb} КБ · це реальний рендер вікна, не макет</p>
</header>
<main>{''.join(figures)}</main>
</body>
</html>
"""
    target = out or paths[0].with_suffix(".html")
    target.write_text(html, encoding="utf-8")
    return target


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Вкажи шлях хоча б до одного PNG")
    written = build_html([Path(arg) for arg in sys.argv[1:]])
    print(written)
