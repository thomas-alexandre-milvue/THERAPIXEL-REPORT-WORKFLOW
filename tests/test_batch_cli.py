import importlib.util
import json
import sys
from pathlib import Path

# Dynamically import batch_cli
GEN_DIR = Path(__file__).resolve().parents[1] / "3. Report Generator" / "c. Generator"
MOD_PATH = GEN_DIR / "batch_cli.py"
spec = importlib.util.spec_from_file_location("batch_cli", MOD_PATH)
batch_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch_cli)


def test_batch_cli(monkeypatch, tmp_path):
    # Setup temporary input and asset files
    inp = tmp_path / "inp"
    inp.mkdir()
    case = {"views": [{"image_modality": "mammo"}]}
    (inp / "c.json").write_text(json.dumps(case))

    out = tmp_path / "out"
    jdir = tmp_path / "json"

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("p")
    tmpl = tmp_path / "t.txt"
    tmpl.write_text("T")

    def fake_select(c):
        assert c == case
        return prompt, [tmpl]

    def fake_generate(c, pp, ts, *, json_dir=None):
        assert pp == prompt
        assert ts == [tmpl]
        if json_dir:
            json_dir.mkdir(parents=True, exist_ok=True)
            (json_dir / f"{tmpl.stem}.json").write_text("{}")
        return {tmpl.stem: "md"}

    monkeypatch.setattr(batch_cli, "select_for_case", fake_select)
    monkeypatch.setattr(batch_cli, "generate_reports", fake_generate)

    monkeypatch.setattr(sys, "argv", ["batch_cli", "-i", str(inp), "-o", str(out), "-j", str(jdir)])

    batch_cli.main()

    assert (out / "c" / "t.md").read_text() == "md"
    assert (jdir / "c" / "t.json").read_text() == "{}"
