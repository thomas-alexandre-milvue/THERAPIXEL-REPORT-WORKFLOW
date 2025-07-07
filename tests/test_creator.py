import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "2. Structured Input"
    / "Structured Input Creator.py"
)

spec = importlib.util.spec_from_file_location("creator", MODULE_PATH)
creator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(creator)


def test_filter():
    allowed = {"a"}
    assert creator._filter({"a": None}, allowed) == {"a": ""}
    assert creator._filter({"a": 5}, allowed) == {"a": 5}
    assert creator._filter({"b": "x"}, allowed) == {}


def test_convert_record_basic():
    raw = {
        "patient_name": "Alice",
        "patient_dob": None,
        "prior": {"study_date": None},
        "views": [
            {
                "laterality": "LEFT",
                "breast_side": "L",
                "patient_orientation_x": "x",
                "patient_orientation_y": "y",
                "flip_h": True,
                "flip_v": False,
                "flip_slice": None,
                "view_position": "CC",
                "number_of_frames": 1,
                "direction": None,
                "image_modality": "mammo",
            }
        ],
        "findings": [
            {
                "mammoscreen_score": 3,
                "laterality": "LEFT",
                "rendering_positions": [{"finding_size_mm": 12}],
                "depth": "anterior",
                "suspicion_level": "high",
                "quadrant": "upper",
                "evolution": "new",
                "type": "mass",
                "with_calcis": False,
            }
        ],
    }

    result = creator._convert_record(raw)
    # None values should not cause errors
    assert result["prior"]["study_date"] in ("", None)
    # numeric fields preserved
    assert (
        result["findings"][0]["rendering_positions"][0]["finding_size_mm"]
        == 12
    )
    # missing keys still present in output
    assert "patient_dob" in result
