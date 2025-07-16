#!/usr/bin/env python3
"""
convert_docx_to_md.py
--------------------
Batch-convert every Word template under
  3. Report Generator/b. Templates/DOCX Source/
into UTF-8 Markdown files in
  3. Report Generator/b. Templates/Text/
"""

from __future__ import annotations
import re
import subprocess, sys, shutil, textwrap
from pathlib import Path

# ── Locate folders ────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent
DOCX_DIR = ROOT / "DOCX Source"
MD_DIR  = ROOT / "Text"

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

# ── Placeholder helpers ───────────────────────────────────────────────────────
# ❶ Match optional back-slash + [label]
PLACEHOLDER_RE = re.compile(r"\\?\[([^\]\n]+)\]")

# ── Promote ad-hoc bold headings ('**CONCLUSION**') ──────────────────────────
BOLD_HEADING_RE = re.compile(r"^\*\*(.+?)\*\*(?:\\)?\s*$")


def _promote_bold_headings(text: str) -> str:
    """Turn full-line bold text into level-2 Markdown headings."""
    return "\n".join(
        ("## " + m.group(1).strip()) if (m := BOLD_HEADING_RE.match(ln.strip())) else ln
        for ln in text.splitlines()
    )

# ── Drop stray blank lines *inside* a section block ──────────────────────────
LIST_BULLET_RE = re.compile(r"^(?:[-*+] |\d+[.)] )")
PLACEHOLDER_ONLY_RE = re.compile(r"^\\?\[[^\]\n]+\]$")


def _collapse_inner_blanks(text: str) -> str:
    """Remove a single blank line that sits between two ordinary paragraphs."""

    lines, out, i = text.splitlines(), [], 0
    while i < len(lines):
        ln = lines[i]
        if (
            ln.strip() == ""  # this line is blank
            and i > 0
            and i + 1 < len(lines)
            and lines[i - 1].strip()
            and lines[i + 1].strip()
            and not lines[i - 1].lstrip().startswith("#")
            and not lines[i + 1].lstrip().startswith("#")
            and not LIST_BULLET_RE.match(lines[i - 1])
            and not LIST_BULLET_RE.match(lines[i + 1])
            and not PLACEHOLDER_ONLY_RE.match(lines[i - 1])
            and not PLACEHOLDER_ONLY_RE.match(lines[i + 1])
        ):
            i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out) + "\n"


def _cleanup_blank_lines(text: str) -> str:
    """Collapse extra blank lines around placeholder-only paragraphs."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Skip blank lines before a placeholder
        if not line.strip() and i + 1 < len(lines) and PLACEHOLDER_RE.fullmatch(lines[i + 1].strip()):
            i += 1
            continue
        out.append(line)
        # Skip blank line right after a placeholder
        if PLACEHOLDER_RE.fullmatch(line.strip()) and i + 1 < len(lines) and not lines[i + 1].strip():
            i += 2
        else:
            i += 1
    return "\n".join(out) + "\n"




def _convert_placeholders(text: str) -> str:
    """Return text with placeholders untouched (remove escape backslashes)."""

    def repl(match: re.Match) -> str:
        return match.group(0).lstrip("\\")

    return PLACEHOLDER_RE.sub(repl, text)

# ── Keep heading spacing tidy ────────────────────────────────────────────────
HEADING_RE = re.compile(r"^#{1,6}\s")


def _normalize_headings(text: str) -> str:
    """Normalize blank lines around headings."""

    out: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if HEADING_RE.match(line):
            while out and out[-1].strip() == "":
                out.pop()
            if out:
                out.append("")
            out.append(line)
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out) + "\n"

# ── Conversion ────────────────────────────────────────────────────────────────
def convert(docx: Path, md: Path) -> None:
    md.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        PANDOC,
        str(docx),
        "-t",
        "markdown",
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
        text = _promote_bold_headings(text)      # ① fake→real headings
        text = _cleanup_blank_lines(text)
        text = _normalize_headings(text)         # ② heading spacing
        text = _collapse_inner_blanks(text)      # ③ no gaps inside block
        text = re.sub(r"\n{3,}", "\n\n", text)   # squeeze 3+ blank lines
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

    print(f"Converting {len(files)} template(s)…\n")
    for docx in files:
        convert(docx, MD_DIR / f"{docx.stem}.md")
    print("\nDone.")

if __name__ == "__main__":
    main()
