"""Fills English translations into i18n/pytrainer_en.ts from a pairs file.

Pairs file format (UTF-8, one per line):
    CONTEXT ||| SOURCE ||| TRANSLATION
Lines starting with `#` and blank lines are skipped. Literal `\\n` inside
a field becomes a real newline.

Only `<translation type="unfinished">` entries are touched; filled ones get
their `type` attribute removed (finished). Matching is exact on
(context, source); unmatched pairs and still-unfinished counts are reported.

    .venv\\Scripts\\python.exe tools/fill_translations.py i18n/pairs01.txt
"""

from __future__ import annotations

import sys
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TS_PATH = ROOT / "i18n" / "pytrainer_en.ts"


def load_pairs(path: Path) -> list[tuple[str, str, str]]:
    pairs: list[tuple[str, str, str]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [field.replace("\\n", "\n") for field in line.split(" ||| ")]
        if len(parts) != 3:
            print(f"bad line {lineno}: {raw[:60]}")
            continue
        pairs.append((parts[0], parts[1], parts[2]))
    return pairs


def main() -> int:
    pairs = load_pairs(Path(sys.argv[1]))
    doc = xml.dom.minidom.parse(str(TS_PATH))
    index: dict[tuple[str, str], xml.dom.minidom.Element] = {}
    for context in doc.getElementsByTagName("context"):
        name = context.getElementsByTagName("name")[0].firstChild.data
        for message in context.getElementsByTagName("message"):
            source = message.getElementsByTagName("source")[0].firstChild.data
            trans = message.getElementsByTagName("translation")[0]
            if trans.getAttribute("type") == "unfinished":
                index[(name, source)] = trans
    done, missing = 0, 0
    for context, source, translation in pairs:
        element = index.pop((context, source), None)
        if element is None:
            print(f"no match: [{context}] {source[:60]}")
            missing += 1
            continue
        element.removeAttribute("type")
        element.appendChild(doc.createTextNode(translation))
        done += 1
    with TS_PATH.open("w", encoding="utf-8") as handle:
        doc.writexml(handle, addindent="    ", newl="", encoding="utf-8")
    print(f"filled {done}, no-match {missing}, still unfinished {len(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
