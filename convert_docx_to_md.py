"""Convenience wrapper for tests.

This module exposes a simplified `convert()` function
that returns the Markdown text generated from a DOCX template.
It delegates all heavy lifting to the actual converter located in
`3. Report Generator/b. Templates/convert_docx_to_md.py`.
"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
IMPL_PATH = (
    HERE
    / "3. Report Generator"
    / "b. Templates"
    / "convert_docx_to_md.py"
)

_spec = importlib.util.spec_from_file_location("cdm_impl", IMPL_PATH)
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)  # type: ignore[attr-defined]


def convert(docx: str | Path) -> str:
    """Return the Markdown produced from *docx*."""
    docx = Path(docx)
    with tempfile.NamedTemporaryFile(
        dir=_impl.ROOT, delete=False, suffix=".md"
    ) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _impl.convert(docx, tmp_path)
        text = tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink(missing_ok=True)
    return text
