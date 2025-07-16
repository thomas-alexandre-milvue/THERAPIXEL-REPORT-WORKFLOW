import importlib.util
from pathlib import Path

GEN_DIR = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "c. Generator"
)
MOD_PATH = GEN_DIR / "gemini_reporter.py"
spec = importlib.util.spec_from_file_location("renderer", MOD_PATH)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_strip_reasoning_removes_section():
    text = "Report text\n\nReasoning: foo"
    assert renderer._strip_reasoning(text) == "Report text"


def test_strip_reasoning_no_change():
    text = "Just the report"
    assert renderer._strip_reasoning(text) == text
