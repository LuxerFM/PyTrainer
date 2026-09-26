"""PyTrainer — Python trainer. See README.md.

Run:  python main.py        (or: python -m trainer)

Service modes (see trainer/cli.py) — no window, no Qt:
    python main.py --self-test [report.json]   check that code and tests work
    python main.py --exec-runner file.py       run someone else's file (as .exe does)
"""

from trainer.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
