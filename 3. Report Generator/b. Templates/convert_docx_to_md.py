#!/usr/bin/env python3
"""
convert_docx_to_md.py
---------------------
Batch-convert every Word template under
  3. Report Generator/b. Templates/DOCX Source/
into UTF-8 Markdown files in
  3. Report Generator/b. Templates/MarkDown/
"""

from __future__ import annotations
import re
import subprocess, sys, shutil, textwrap
from pathlib import Path

# ── Locate folders ────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
DOCX_DIR = ROOT / "DOCX Source"
MD_DIR   = ROOT / "MarkDown"

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
PLACEHOLDER_RE = re.compile(r"\[([^\]|\n]+)\]")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _convert_placeholders(text: str) -> str:
    """Replace [PLACEHOLDER] tags with Jinja {{ placeholder }}."""

    def repl(match: re.Match) -> str:
        label = match.group(1).strip()
        if any(sep in label for sep in ("/", "|", ";")):
            return match.group(0)
        return f"{{{{ {_slugify(label)} }}}}"

    return PLACEHOLDER_RE.sub(repl, text)

# ── Conversion ────────────────────────────────────────────────────────────────
def convert(docx: Path, md: Path) -> None:
    md.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        PANDOC,
        str(docx),
        "-t",
        "markdown" if USE_ATX else "gfm",
        "-o",
        "-",
        "--wrap=none",
        "--columns=120",
    ]
    if USE_ATX:
        cmd.insert(-2, "--atx-headers")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        text = _convert_placeholders(result.stdout)
        md.write_text(text, encoding="utf-8")
        print(f"✓  {docx.name} → {md.relative_to(ROOT)}")
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

    print(f"Converting {len(files)} template(s)…  (ATX headings: {'yes' if USE_ATX else 'no'})\n")
    for docx in files:
        convert(docx, MD_DIR / f"{docx.stem}.md")
    print("\nDone.")

if __name__ == "__main__":
    main()
