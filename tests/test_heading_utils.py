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
    r"BOLD_HEADING_RE.*?def _promote_bold_headings.*?for ln in text\.splitlines\(\).*?\)",
    source,
    re.S,
).group()

snippet2 = re.search(
    (
        r"HEADING_RE.*?def _normalize_headings.*?"
        r"return \"\\n\".join\(out\) \+ \"\\n\""
    ),
    source,
    re.S,
).group()

namespace = {"re": re}
exec(snippet, namespace)
exec(snippet2, namespace)
_promote_bold_headings = namespace["_promote_bold_headings"]
_normalize_headings = namespace["_normalize_headings"]


def test_normalize_headings_basic():
    text = "# H1\n\n\nPara\n\n## H2\n\nText\n"
    out = _normalize_headings(text)
    assert out == "# H1\nPara\n\n## H2\nText\n"


def test_promote_bold_headings():
    text = "Intro\n\n**SECTION**\nText"
    out = _promote_bold_headings(text)
    assert out == "Intro\n\n## SECTION\nText"
