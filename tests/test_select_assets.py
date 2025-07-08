import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "3. Report Generator"
    / "c. Generator"
    / "select_assets.py"
)
spec = importlib.util.spec_from_file_location("sel", MODULE_PATH)
sel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sel)


def test_prompt_override(monkeypatch, tmp_path):
    # Create mapping and config under temporary root
    root = tmp_path
    config_dir = root / "0. Config"
    config_dir.mkdir()
    map_file = config_dir / "modality_map.yaml"
    map_file.write_text(
        "mammography:\n  prompt: a.yaml\n  templates: templates",
        encoding="utf-8",
    )
    cfg_file = config_dir / "query_configs.yaml"
    cfg_file.write_text(
        "prompt_file: override.yaml",
        encoding="utf-8",
    )
    tmpl_dir = root / "templates"
    tmpl_dir.mkdir()
    t = tmpl_dir / "t.md"
    t.write_text("T", encoding="utf-8")

    monkeypatch.setattr(sel, "ROOT", root)
    monkeypatch.setattr(sel, "MAP_FILE", map_file)
    monkeypatch.setattr(sel, "CONFIG_FILE", cfg_file)
    monkeypatch.setattr(
    sel,
    "load_mapping",
    lambda path=map_file: sel.yaml.safe_load(
        map_file.read_text()
    )
)

    case = {"views": [{"image_modality": "mammography"}]}
    prompt, templates = sel.select_for_case(case)
    assert prompt == root / "override.yaml"
    assert templates == [t]
