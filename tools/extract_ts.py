"""Extracts translatable strings into a Qt .ts file.

pyside6-lupdate ships broken/silent in our venv (prints nothing, creates
nothing — even on `-version`), so this ast-based extractor covers our three
conventions instead:

* `self.tr("...")` inside a QWidget — context is the class name;
* `_tr("...")` module helper — context is read from that helper's own
  `QCoreApplication.translate("CTX", text)` body;
* `QCoreApplication.translate("CTX", "...")` called directly.

Only plain string literals are collected (format placeholders like `{n}`
stay inside — the translator moves them). Dynamic expressions are skipped
with a warning; f-strings are refused on purpose: wrap the literal, then
`.format()` it.

    .venv\\Scripts\\python.exe tools/extract_ts.py   # writes i18n/pytrainer_en.ts

NOTE: the pyside6-lupdate/lrelease shims in .venv\\Scripts are dead weight.
Use the real binaries inside the package, e.g.:
    $py (venv) → import PySide6, os → $p\\lrelease.exe i18n/pytrainer_en.ts
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "i18n" / "pytrainer_en.ts"
SCAN = [ROOT / "trainer", ROOT / "main.py"]


def _strings_from(node: ast.AST) -> list[str] | None:
    """String literals inside a tr() argument, or None if dynamic."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.IfExp):
        left = _strings_from(node.body)
        right = _strings_from(node.orelse)
        if left is not None and right is not None:
            return left + right
        return None
    return None


def _module_tr_context(tree: ast.AST) -> str | None:
    """Context name from the module-level `def _tr` helper, if present."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_tr":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "translate"
                        and sub.args
                        and isinstance(sub.args[0], ast.Constant)):
                    return str(sub.args[0].value)
    return None


def extract(path: Path) -> list[tuple[str, str, int]]:
    """(context, source, lineno) triples found in one file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as error:
        print(f"skip {path}: {error}")
        return []
    module_ctx = _module_tr_context(tree)
    found: list[tuple[str, str, int]] = []

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.classes: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.classes.append(node.name)
            self.generic_visit(node)
            self.classes.pop()

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            context: str | None = None
            arg: ast.AST | None = None
            if (isinstance(func, ast.Attribute) and func.attr == "tr"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "self" and self.classes
                    and node.args):
                context, arg = self.classes[-1], node.args[0]
            elif (isinstance(func, ast.Name) and func.id == "_tr"
                    and module_ctx is not None and node.args):
                context, arg = module_ctx, node.args[0]
            elif (isinstance(func, ast.Attribute) and func.attr == "translate"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "QCoreApplication"
                    and len(node.args) >= 2
                    and isinstance(node.args[0], ast.Constant)):
                context, arg = str(node.args[0].value), node.args[1]
            if context is not None and arg is not None:
                strings = _strings_from(arg)
                if strings is None:
                    print(f"warn {path}:{node.lineno}: dynamic tr() arg skipped")
                else:
                    found.extend((context, text, node.lineno) for text in strings)
            self.generic_visit(node)

    Visitor().visit(tree)
    return found


def load_existing() -> dict[tuple[str, str], str | None]:
    """Translations already in the .ts, so a re-run never wipes work."""
    kept: dict[tuple[str, str], str | None] = {}
    if not TS_PATH.exists():
        return kept
    import xml.dom.minidom
    doc = xml.dom.minidom.parse(str(TS_PATH))
    for context in doc.getElementsByTagName("context"):
        name = context.getElementsByTagName("name")[0].firstChild.data
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild.data
            trans = message.getElementsByTagName("translation")[0]
            text = "".join(node.data for node in trans.childNodes
                           if node.nodeType == node.TEXT_NODE)
            kept[(name, source)] = text or None
    return kept


def write_ts(messages: list[tuple[str, str, Path, int]]) -> None:
    """Writes a valid .ts file (compilable by lrelease)."""
    kept = load_existing()
    by_context: dict[str, list[tuple[str, Path, int]]] = {}
    seen: set[tuple[str, str]] = set()
    for context, source, path, lineno in messages:
        if (context, source) in seen or not source.strip():
            continue
        seen.add((context, source))
        by_context.setdefault(context, []).append((source, path, lineno))
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<!DOCTYPE TS>',
           '<TS version="2.1" language="en">']
    for context in sorted(by_context):
        out.append(f"<context>\n    <name>{escape(context)}</name>")
        for source, path, lineno in by_context[context]:
            rel = path.relative_to(ROOT).as_posix()
            old = kept.get((context, source))
            if old:
                trans = f"        <translation>{escape(old)}</translation>"
            else:
                trans = '        <translation type="unfinished"></translation>'
            out.append(
                f'    <message>\n        <location filename="../{rel}" line="{lineno}"/>\n'
                f"        <source>{escape(source)}</source>\n"
                f"{trans}\n"
                "    </message>")
        out.append("</context>")
    out.append("</TS>")
    TS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TS_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    messages: list[tuple[str, str, Path, int]] = []
    files = 0
    for base in SCAN:
        paths = [base] if base.is_file() else sorted(base.rglob("*.py"))
        for path in paths:
            files += 1
            messages.extend((ctx, src, path, line)
                            for ctx, src, line in extract(path))
    write_ts(messages)
    contexts = len({message[0] for message in messages})
    print(f"{files} files: {len(messages)} strings, "
          f"{contexts} contexts -> {TS_PATH.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
