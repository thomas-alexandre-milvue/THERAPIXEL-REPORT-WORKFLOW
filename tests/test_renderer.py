import importlib.util
from pathlib import Path
import pytest

# Dynamically import jinja_renderer
MOD_PATH = Path(__file__).resolve().parents[1] / "3. Report Generator" / "c. Generator" / "jinja_renderer.py"
spec = importlib.util.spec_from_file_location("renderer", MOD_PATH)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def test_parse_response_invalid():
    with pytest.raises(ValueError):
        renderer._parse_response("not json")
