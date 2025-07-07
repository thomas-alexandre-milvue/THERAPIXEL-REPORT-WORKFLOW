import re
from pathlib import Path

MODULE = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "b. Templates"
    / "convert_docx_to_md.py"
)
source = MODULE.read_text(encoding="utf-8")

snippet = re.search(
    (
        r"PLACEHOLDER_RE.*?def _convert_placeholders"
        r".*?return PLACEHOLDER_RE\.sub\(repl, text\)"
    ),
    source,
    re.S,
).group()
namespace = {"re": re}
exec(snippet, namespace)
_convert_placeholders = namespace["_convert_placeholders"]


def test_placeholder_conversion():
    text = "Age : [Age]\nOption: [A / B]"
    out = _convert_placeholders(text)
    assert "{{ age }}" in out
    assert "[A / B]" in out
