import re
import subprocess
import sys
from pathlib import Path


MODULE = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "b. Templates"
    / "convert_docx_to_md.py"
)
source = MODULE.read_text(encoding="utf-8")

snippet = re.search(
    r"PLACEHOLDER_RE.*?def convert\(.*?raise",
    source,
    re.S,
).group()

namespace = {
    "re": re,
    "Path": Path,
    "subprocess": subprocess,
    "sys": sys,
}
# Provide minimal globals used inside snippet
namespace["PANDOC"] = "pandoc"
namespace["ROOT"] = Path(".")
exec(snippet, namespace)
convert = namespace["convert"]


def test_convert_writes_file(monkeypatch, tmp_path):
    cp = subprocess.CompletedProcess(["pandoc"], 0, stdout="Age: **[Age]**\n")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: cp)
    namespace["ROOT"] = tmp_path
    docx = tmp_path / "input.docx"
    docx.write_text("dummy")
    out = tmp_path / "out.md"
    convert(docx, out)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "Age: **[Age]**\n"
