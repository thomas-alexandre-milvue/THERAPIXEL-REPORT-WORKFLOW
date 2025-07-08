import importlib.util
from pathlib import Path

# Dynamically import gemini_reporter
GEN_DIR = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "c. Generator"
)
MOD_PATH = GEN_DIR / "gemini_reporter.py"
spec = importlib.util.spec_from_file_location("renderer", MOD_PATH)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_parse_response_json():
    text = "```json\n{\n  \"lines\": [\"a\", \"b\"]\n}\n```\nReasoning: bla"
    assert renderer._parse_response(text) == {"lines": ["a", "b"]}


def test_render_json_to_md():
    md = renderer.render_json_to_md({"lines": ["a", "b"]})
    assert md == "a\nb\n"


def test_render_json_to_md_string():
    md = renderer.render_json_to_md({"text": "foo\nbar"})
    assert md == "foo\nbar\n"


def test_render_json_to_md_nested():
    md = renderer.render_json_to_md({"markdown": {"lines": ["x", "y"]}})
    assert md == "x\ny\n"
