"""Pure-Python i18n helper (no GNU gettext needed — works on Windows).

    python scripts/i18n.py extract   # list msgids missing from scripts/translations_en.py
    python scripts/i18n.py build     # write locale/en/LC_MESSAGES/django.po and compile django.mo

Source strings are Arabic (the default language); English translations live in
``scripts/translations_en.py`` as a plain dict, which is easy to review and edit.
"""
import ast
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

TEMPLATE_RE = re.compile(r'{%\s*(?:translate|trans)\s+"((?:[^"\\]|\\.)*)"')
PY_FUNCS = {"_", "_l", "gettext", "gettext_lazy", "pgettext", "ngettext"}


def iter_files():
    for path in (ROOT / "templates").rglob("*"):
        if path.suffix in {".html", ".txt"}:
            yield path
    for path in (ROOT / "apps").rglob("*.py"):
        if "migrations" not in path.parts:
            yield path
    yield ROOT / "config" / "settings" / "base.py"


def extract():
    found = {}
    for path in iter_files():
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in PY_FUNCS
                        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    found.setdefault(node.args[0].value, str(path.relative_to(ROOT)))
        else:
            for m in TEMPLATE_RE.finditer(text):
                found.setdefault(m.group(1).replace('\\"', '"'), str(path.relative_to(ROOT)))
    return found


def po_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def write_mo(pairs, path):
    """Minimal GNU .mo writer (same format msgfmt produces)."""
    pairs = sorted(pairs.items())
    ids = b"".join(k.encode() + b"\0" for k, _ in pairs)
    strs = b"".join(v.encode() + b"\0" for _, v in pairs)
    n = len(pairs)
    koffsets, voffsets, o = [], [], 0
    for k, _ in pairs:
        koffsets.append((len(k.encode()), o))
        o += len(k.encode()) + 1
    o = 0
    for _, v in pairs:
        voffsets.append((len(v.encode()), o))
        o += len(v.encode()) + 1
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    output = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
    for length, off in koffsets:
        output += struct.pack("ii", length, off + keystart)
    for length, off in voffsets:
        output += struct.pack("ii", length, off + valuestart)
    path.write_bytes(output + ids + strs)


def build():
    from translations_en import EN

    header = "Content-Type: text/plain; charset=UTF-8\nLanguage: en\nPlural-Forms: nplurals=2; plural=(n != 1);\n"
    msgs = {k: v for k, v in EN.items() if v}
    out_dir = ROOT / "locale" / "en" / "LC_MESSAGES"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ['msgid ""', 'msgstr ""', f'"{po_escape(header)}"', ""]
    for k, v in sorted(msgs.items()):
        lines += [f'msgid "{po_escape(k)}"', f'msgstr "{po_escape(v)}"', ""]
    (out_dir / "django.po").write_text("\n".join(lines), encoding="utf-8")
    write_mo({"": header, **msgs}, out_dir / "django.mo")
    missing = [m for m in extract() if m not in msgs]
    print(f"Compiled {len(msgs)} English strings. Missing: {len(missing)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "extract"
    if cmd == "build":
        build()
    else:
        try:
            from translations_en import EN
        except ImportError:
            EN = {}
        missing = {k: v for k, v in extract().items() if k not in EN}
        for k in missing:
            print(repr(k))
        print(f"# {len(missing)} missing", file=sys.stderr)
