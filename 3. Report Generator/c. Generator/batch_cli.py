#!/usr/bin/env python3
"""Batch report generator for all structured input cases."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # When executed as part of a package
    from .select_assets import select_for_case
    from .gemini_reporter import generate_reports
except ImportError:  # Fallback when run as a standalone script
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from select_assets import select_for_case
    from gemini_reporter import generate_reports

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate clinical reports for all structured inputs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "-i",
        "--input",
        dest="inp",
        type=Path,
        default=ROOT / "2. Structured Input",
        help="Folder of structured input JSON files",
    )
    p.add_argument(
        "-o",
        "--out",
        dest="out",
        type=Path,
        default=ROOT / "3. Report Generator" / "d. Tests",
        help="Destination folder for generated reports",
    )
    args = p.parse_args()

    files = sorted(args.inp.glob("*.json"))
    if not files:
        p.error(f"No .json files found in {args.inp}")

    for src in files:
        case = json.loads(src.read_text(encoding="utf-8"))
        prompt_path, templates = select_for_case(case)
        reports = generate_reports(case, prompt_path, templates)
        case_dir = args.out / src.stem
        case_dir.mkdir(parents=True, exist_ok=True)
        for t in templates:
            out_path = case_dir / f"{t.stem}.md"
            out_path.write_text(reports[t.stem], encoding="utf-8")
        print(f"✔ {src.name} → {case_dir.relative_to(args.out)}")


if __name__ == "__main__":
    main()
