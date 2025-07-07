import importlib.util
from pathlib import Path
import pytest

# Dynamically import jinja_renderer
GEN_DIR = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "c. Generator"
)
MOD_PATH = GEN_DIR / "jinja_renderer.py"
spec = importlib.util.spec_from_file_location("renderer", MOD_PATH)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_parse_response_invalid():
    # Non-JSON input should be returned as a pre-rendered report
    result = renderer._parse_response("not json")
    assert result == {"report": "not json"}
