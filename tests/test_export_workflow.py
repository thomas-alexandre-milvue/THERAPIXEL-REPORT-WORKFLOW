import importlib.util
from pathlib import Path
import json

MODULE_PATH = Path(__file__).resolve().parents[1] / "export_workflow.py"
spec = importlib.util.spec_from_file_location("exp", MODULE_PATH)
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


def setup_tmp(tmp_path):
    root = tmp_path / "proj"
    root.mkdir()
    cfg_dir = root / "0. Config"
    cfg_dir.mkdir()
    (cfg_dir / "query_configs.yaml").write_text(
        "model_name: test-model",
        encoding="utf-8",
    )
    (root / "1. Input").mkdir()
    (root / "1. Input" / "raw.json").write_text("{}", encoding="utf-8")
    (root / "2. Structured Input").mkdir()
    (root / "2. Structured Input" / "struct.json").write_text(
        "{}",
        encoding="utf-8",
    )
    tmpl_dir = root / "3. Report Generator" / "b. Templates" / "Text"
    tmpl_dir.mkdir(parents=True)
    (tmpl_dir / "t.md").write_text("T", encoding="utf-8")
    json_dir = root / "3. Report Generator" / "d. Gemini Output JSON"
    json_dir.mkdir(parents=True)
    (json_dir / "r.json").write_text(json.dumps({}), encoding="utf-8")
    final_dir = root / "3. Report Generator" / "e. Final Report"
    final_dir.mkdir(parents=True)
    (final_dir / "f.md").write_text("F", encoding="utf-8")
    return root


def test_export(tmp_path):
    root = setup_tmp(tmp_path)
    out = tmp_path / "out"
    # patch constants
    exp.ROOT = root
    exp.CONFIG = root / "0. Config" / "query_configs.yaml"
    exp.RAW_INPUTS = root / "1. Input"
    exp.STRUCTURED_INPUTS = root / "2. Structured Input"
    exp.TEMPLATES = root / "3. Report Generator" / "b. Templates" / "Text"
    exp.JSONS = root / "3. Report Generator" / "d. Gemini Output JSON"
    exp.FINAL_MD = root / "3. Report Generator" / "e. Final Report"

    exp.export(out)

    assert (out / "Raw Therapixel Inputs" / "raw.json").exists()
    assert (out / "Structured Inputs" / "struct.json").exists()
    assert (out / "Reports" / "Templates" / "t.md").exists()
    assert (out / "Reports" / "Gemini JSONs" / "r.json").exists()
    assert (out / "Reports" / "Final MD" / "f.md").exists()
