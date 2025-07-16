import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "extract_images.py"
spec = importlib.util.spec_from_file_location("mod", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def setup_tmp(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    raw = root / "1. Input"
    raw.mkdir()
    base64_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+AAAADwAte8T2QAAAABJRU5ErkJggg=="
    )
    (raw / "case.json").write_text('{"img": "%s"}' % base64_png, encoding="utf-8")
    return root


def test_export(tmp_path):
    root = setup_tmp(tmp_path)
    out = tmp_path / "out"
    mod.ROOT = root
    mod.RAW_INPUTS = root / "1. Input"
    mod.export(out)
    files = list(out.rglob("*.png"))
    assert files and files[0].read_bytes().startswith(b"\x89PNG")
