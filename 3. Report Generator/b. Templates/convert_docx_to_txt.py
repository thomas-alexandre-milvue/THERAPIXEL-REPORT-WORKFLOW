#!/usr/bin/env python3
"""
convert_docx_to_txt.py
---------------------
Batch-convert every Word template under
  3. Report Generator/b. Templates/DOCX Source/
into UTF-8 plain-text files in
  3. Report Generator/b. Templates/Text/
"""

from __future__ import annotations
import re
import subprocess, sys, shutil, textwrap
from pathlib import Path

# ── Locate folders ────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
DOCX_DIR = ROOT / "DOCX Source"
TXT_DIR  = ROOT / "Text"

# ── Find or download Pandoc ───────────────────────────────────────────────────
def ensure_pandoc() -> str:
    """Return a path to a working pandoc executable (download if needed)."""
    try:
        import pypandoc
        try:
            return pypandoc.get_pandoc_path()
        except OSError:
            print("Downloading embedded pandoc (~25 MB)…")
            pypandoc.download_pandoc()
            return pypandoc.get_pandoc_path()
    except ImportError:
        exe = shutil.which("pandoc") or shutil.which("pandoc.exe")
        if exe:
            return exe
        sys.exit(
            textwrap.dedent(
                """\
                Pandoc not found.
                • Install it from <https://pandoc.org/install>  –or–
                • pip install pypandoc[binary]"""
            )
        )

PANDOC = ensure_pandoc()

# ── Helper: does this pandoc accept --atx-headers? ────────────────────────────
def supports_atx_headers() -> bool:
    result = subprocess.run(
        [PANDOC, "--atx-headers", "-t", "markdown", "-o", "-"],
        input="Test", text=True, capture_output=True
    )
    return result.returncode == 0

USE_ATX = supports_atx_headers()

# ── Placeholder helpers ───────────────────────────────────────────────────────
# ❶ Match optional back-slash + [label]
PLACEHOLDER_RE = re.compile(r"\\?\[([^\]\n]+)\]")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _convert_placeholders(text: str) -> str:
    """
    Replace [PLACEHOLDER] with Jinja {{ placeholder }}.
    • Keeps complex tags like [Dose (mGy)/kg] unchanged.
    • Removes Pandoc’s escaping back-slash if present.
    """
    # Rendering step: jinja_template.render(context) must replace all
    # {{ placeholder }} before the clinician sees the report.

    def repl(match: re.Match) -> str:
        raw = match.group(0).lstrip("\\")          # kill leading back-slash
        label = match.group(1).strip()
        if any(sep in label for sep in ("/", "|", ";")):
            return raw                              # leave complex labels verbatim
        return f"{{{{ {_slugify(label)} }}}}"       # simple → Jinja

    return PLACEHOLDER_RE.sub(repl, text)

# ── Conversion ────────────────────────────────────────────────────────────────
def convert(docx: Path, txt: Path) -> None:
    txt.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        PANDOC,
        str(docx),
        "-t",
        "plain",
        "-o",
        "-",
        "--wrap=none",
        "--columns=120",
    ]


    try:
        # ❷ Decode Pandoc’s UTF-8 correctly
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        text = _convert_placeholders(result.stdout)
        txt.write_text(text, encoding="utf-8")
        print(f"✓  {docx.name} → {txt.relative_to(ROOT)}")
    except subprocess.CalledProcessError:
        print(f"✗  Pandoc failed on {docx.name}", file=sys.stderr)
        raise

# ── CLI ───────────────────────────────────────────────────────────────────────
def main() -> None:
    if not DOCX_DIR.exists():
        sys.exit(f"Folder not found: {DOCX_DIR}")

    files = sorted(DOCX_DIR.rglob("*.doc*"))
    if not files:
        sys.exit("No DOCX templates found.")

    print(f"Converting {len(files)} template(s)…\n")
    for docx in files:
        convert(docx, TXT_DIR / f"{docx.stem}.txt")
    print("\nDone.")

if __name__ == "__main__":
    main()
