import importlib.util
from pathlib import Path

import pytest

# Helper fixture to import the conversion function
@pytest.fixture(scope="module")
def convert_record():
    path = Path(__file__).resolve().parents[1] / "2. Structured Input" / "Structured Input Creator.py"
    spec = importlib.util.spec_from_file_location("creator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._convert_record


def test_laterality_fallback(convert_record):
    raw = {"laterality": "B", "findings": []}
    converted = convert_record(raw)
    assert converted["laterality"] == "B"
