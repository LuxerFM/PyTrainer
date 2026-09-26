"""Launch-mode picker: window, running someone else's code, self-test.

The order here is deliberate. Service modes are checked **before** importing
PySide6, and that is not a micro-optimisation:

* `--exec-runner` runs user code, i.e. a separate launch per check. In the
  built `.exe` each such launch also unpacks the PyInstaller archive, so a
  needless Qt import would add a noticeable fraction of a second to every
  check;
* `--self-test` checks exactly those launches — and in CI, where Qt may not
  be needed at all, it must not drag the UI along.

A plain launch (no flags) goes to `trainer/app.py`.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)

    if "--version" in argv or "-V" in argv:
        from .core.crashlog import version_line

        print(version_line())
        return 0

    # First — the data folder: the db path is computed at import time of
    # `trainer.core.db`, so `--data-dir` must be applied earlier.
    from .paths import apply_data_dir

    apply_data_dir(argv)

    from .core.exec_runner import FLAG as RUN_FLAG, main as run_main

    if RUN_FLAG in argv:
        return run_main(argv)

    from .core.selfcheck import FLAG as TEST_FLAG, main as test_main

    if TEST_FLAG in argv:
        from .core.crashlog import setup_crashlog

        setup_crashlog()
        return test_main(argv)

    from .app import main as window_main

    return window_main(argv)


__all__ = ["main"]
