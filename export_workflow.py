#!/usr/bin/env python3
"""Export pipeline artifacts to the user's Downloads folder."""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "0. Config" / "query_configs.yaml"

RAW_INPUTS = ROOT / "1. Input"
STRUCTURED_INPUTS = ROOT / "2. Structured Input"
TEMPLATES = ROOT / "3. Report Generator" / "b. Templates" / "Text"
RESPONSES = ROOT / "3. Report Generator" / "d. Gemini Markdown Responses"
FINAL_MD = ROOT / "3. Report Generator" / "e. Final Report"


def _load_model_name() -> str:
    """Return the model name without path prefixes."""
    if CONFIG.exists():
        cfg = yaml.safe_load(CONFIG.read_text())
        model = cfg.get("model_name", "unknown_model")
        return Path(model).name.replace("/", "-")
    return "unknown_model"


def _downloads_dir() -> Path:
    d = Path.home() / "Downloads"
    return d if d.exists() else Path.home()


def _copy_tree(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)


def export(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    _copy_tree(RAW_INPUTS, dest / "1. Raw Therapixel Inputs")
    _copy_tree(STRUCTURED_INPUTS, dest / "2. Structured Inputs")
    reports = dest / "3. Reports"
    reports.mkdir(exist_ok=True)
    _copy_tree(TEMPLATES, reports / "a. Templates")
    _copy_tree(RESPONSES, reports / "b. Gemini Markdown")
    _copy_tree(FINAL_MD, reports / "c. Final MD")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy pipeline artifacts to Downloads for traceability"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: Downloads)",
    )
    args = parser.parse_args()

    model = _load_model_name()
    ts = dt.datetime.now().strftime("%Y-%m-%d_%H-%M")
    root_dir = (
        args.output or _downloads_dir()
    ) / f"Therapixel Workflow_{model}_{ts}"
    export(root_dir)
    print(f"Artifacts copied to {root_dir}")


if __name__ == "__main__":
    main()
