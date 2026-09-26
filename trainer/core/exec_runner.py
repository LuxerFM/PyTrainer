"""Running someone else's file with the same interpreter — the `--exec-runner` mode.

Why a separate mode. User code always runs in a **separate** process: otherwise
`while True` in a solution would hang the whole trainer. While the app launches
from code, a separate process is just `python`. But in the built `.exe`
`sys.executable` points at **the trainer itself**, and then the usual launch
does the wrong thing: a second PyTrainer window starts instead of the solution.
The verdict never arrives, the process outlives the timeout and holds temp
files, so they cannot even be cleaned up.

So the `.exe` launches itself with `--exec-runner`: this mode runs the given
file as `__main__` — with the embedded interpreter, no Qt, no window — and
returns its exit code. The runner sees no difference: where `python` was, now
is `.exe`, and user code works the same.

See also `trainer/cli.py` — the order in which this mode is checked ahead of
the PySide6 import, and `ensure_streams()` — why without the encoding fix
Ukrainian output in the `.exe` turns to garbage.
"""

from __future__ import annotations

import io
import os
import runpy
import sys
import traceback

from ..paths import is_frozen

FLAG = "--exec-runner"


def script_from(argv: list[str]) -> str:
    """The file to run (empty string if none was given)."""
    if FLAG not in argv:
        return ""
    for item in argv[argv.index(FLAG) + 1:]:
        if not item.startswith("-"):
            return item
    return ""


def _attach(index: int, mode: str) -> object:
    """A text stream on the real descriptor 0, 1 or 2."""
    try:
        buffering = 1 if mode == "w" else -1
        return os.fdopen(index, mode, encoding="utf-8", buffering=buffering, closefd=False)
    except OSError:
        return open(os.devnull, mode, encoding="utf-8")


def ensure_streams() -> None:
    """Makes std streams UTF-8 — otherwise Cyrillic turns to garbage.

    Two different troubles with one root. A windowed `.exe` may leave
    `sys.stdout` empty — then `print` in user code just vanishes instead of
    landing in the file the runner reads. And if not left, PyInstaller
    attaches streams with the system ANSI encoding (here cp1251) — and then
    all Ukrainian output turns into "??????". The runner reads that output as
    UTF-8, so the encodings must match **always**: otherwise "code prints the
    wrong thing" would look like a solution bug that is not there.

    Encoding is fixed only in the built `.exe`: in a console run from code it
    is its own and correct, and forcing it to UTF-8 at random would corrupt
    Cyrillic in an old Windows console window.
    """
    frozen = is_frozen()
    for index, name, mode in ((0, "stdin", "r"), (1, "stdout", "w"), (2, "stderr", "w")):
        stream = getattr(sys, name, None)
        if stream is None:
            setattr(sys, name, _attach(index, mode))
            continue
        encoding = getattr(stream, "encoding", None)
        if not frozen or encoding is None:
            continue
        if encoding.lower().replace("-", "_") in ("utf_8", "utf8"):
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="strict")
        except (AttributeError, OSError, ValueError, io.UnsupportedOperation):
            # Not a text stream that can reconfigure (tests, swapped streams) —
            # leave as is; that is not the case we are healing.
            pass


def _exit_code(code: object) -> int:
    """Exit code from `SystemExit` — the way CPython does it."""
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    print(code, file=sys.stderr or sys.stdout)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Runs the `--exec-runner` file and returns its exit code."""
    argv = list(sys.argv if argv is None else argv)
    script = script_from(argv)
    ensure_streams()
    if not script:
        print(f"{FLAG}: не вказано файл для виконання", file=sys.stderr)
        return 2

    # Just like a plain `python file.py`: absolute path in sys.argv[0],
    # the file's folder first in sys.path (so `import utils` from its own
    # folder works) and the same folder as working dir.
    arguments = [item for item in argv[argv.index(FLAG) + 1:] if not item.startswith("-")]
    script = os.path.abspath(script)
    folder = os.path.dirname(script)
    sys.argv = [script] + arguments[1:]
    if folder not in sys.path:
        sys.path.insert(0, folder)
    os.chdir(folder)

    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as stop:
        return _exit_code(stop.code)
    except BaseException:
        # We print the error ourselves instead of letting it "out": in the
        # built windowed .exe an unhandled exception becomes a dialog with an
        # "OK" button. The dialog would wait for a click, so an ordinary
        # solution error would look like a timeout — with no explanation.
        traceback.print_exc()
        return 1
    return 0


__all__ = ["FLAG", "ensure_streams", "main", "script_from"]
