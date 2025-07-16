import importlib.util
import json
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


def common_setup(monkeypatch):
    monkeypatch.setattr(renderer, "_load_config", lambda: {})


def test_generate_reports(monkeypatch, tmp_path):
    common_setup(monkeypatch)
    outputs = iter([
        {"lines": ["one"]},
        {"lines": ["two"]},
    ])
    calls = []

    def fake_query(structured, prompt, templates):
        calls.append(templates)
        return next(outputs)

    monkeypatch.setattr(renderer, "query_gemini", fake_query)
    monkeypatch.setattr(
        renderer,
        "render_json_to_md",
        lambda d: " ".join(d["lines"]),
    )
    prompt = tmp_path / "p.txt"
    prompt.write_text("prompt")
    t1 = tmp_path / "a.md"
    t1.write_text("A {name}")
    t2 = tmp_path / "b.md"
    t2.write_text("B {name}")

    result = renderer.generate_reports({}, prompt, [t1, t2])
    assert result == {"a": "one", "b": "two"}
    assert calls == [["A {name}"], ["B {name}"]]


def test_generate_reports_json_dir(monkeypatch, tmp_path):
    common_setup(monkeypatch)
    output = {"lines": ["x"]}

    monkeypatch.setattr(renderer, "query_gemini", lambda *a: output)
    monkeypatch.setattr(renderer, "render_json_to_md", lambda d: "res")

    prompt = tmp_path / "p.txt"
    prompt.write_text("prompt")
    t1 = tmp_path / "a.md"
    t1.write_text("T")
    jdir = tmp_path / "json"

    result = renderer.generate_reports({}, prompt, [t1], json_dir=jdir)

    assert result == {"a": "res"}
    saved = json.loads((jdir / "a.json").read_text())
    assert saved == output
