"""PyTrainer — тренажер Python. Дивись README.md.

Запуск:  python main.py        (або: python -m trainer)

Службові режими (див. trainer/cli.py) — без вікна й без Qt:
    python main.py --self-test [звіт.json]     перевірити, що код і тести працюють
    python main.py --exec-runner файл.py       виконати чужий файл (так робить .exe)
"""

from trainer.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
