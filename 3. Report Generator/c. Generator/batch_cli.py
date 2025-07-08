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
        default=ROOT / "3. Report Generator" / "e. Final Report",
        help="Destination folder for generated Markdown reports",
    )
    p.add_argument(
        "-j",
        "--json-dir",
        dest="json_dir",
        type=Path,
        default=ROOT / "3. Report Generator" / "d. Gemini Output JSON",
        help="Folder to store raw Gemini JSON responses",
    )
    args = p.parse_args()

    files = sorted(args.inp.glob("*.json"))
    if not files:
        p.error(f"No .json files found in {args.inp}")

    for src in files:
        print(f"\nProcessing {src.name}…")
        case = json.loads(src.read_text(encoding="utf-8"))
        prompt_path, templates = select_for_case(case)
        case_dir = args.out / src.stem
        case_dir.mkdir(parents=True, exist_ok=True)
        json_dir = args.json_dir / src.stem if args.json_dir else None
        reports = generate_reports(
            case, prompt_path, templates, json_dir=json_dir
        )
        for t in templates:
            out_path = case_dir / f"{t.stem}.md"
            out_path.write_text(reports[t.stem], encoding="utf-8")
            print(f"  ✔ saved {out_path.relative_to(args.out)}")
        print(f"✔ Completed {src.name}\n")


if __name__ == "__main__":
    main()
