#!/usr/bin/env python3
"""CLI entry point for the report generator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

try:  # When executed as part of a package
    from .select_assets import select_for_case
    from .gemini_reporter import generate_report
except ImportError:  # Fallback when run as a standalone script
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from select_assets import select_for_case
    from gemini_reporter import generate_report


def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate clinical report from structured input",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "-i",
        "--input",
        dest="inp",
        type=Path,
        help="Structured input JSON",
    )
    p.add_argument(
        "-o",
        "--output",
        dest="out",
        type=Path,
        help="Output Markdown file",
    )
    p.add_argument(
        "-t",
        "--template",
        dest="template",
        type=Path,
        help="Template text file",
    )
    args = p.parse_args()

    if args.inp is None:
        default_dir = ROOT / "2. Structured Input"
        files = sorted(default_dir.glob("*.json"))
        if not files:
            p.error(f"No .json files found in {default_dir}")
        print("Select structured input:")
        for i, f in enumerate(files, 1):
            print(f"{i}) {f.name}")
        while True:
            choice = input("Enter number: ")
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                args.inp = files[int(choice) - 1]
                break
            print("Invalid selection")

    case = json.loads(args.inp.read_text(encoding="utf-8"))
    prompt_path, templates = select_for_case(case)

    if args.template is None:
        print("Select template:")
        for i, t in enumerate(templates, 1):
            print(f"{i}) {t.name}")
        while True:
            choice = input("Enter number: ")
            if choice.isdigit() and 1 <= int(choice) <= len(templates):
                args.template = templates[int(choice) - 1]
                break
            print("Invalid selection")
    else:
        args.template = Path(args.template)

    if args.out is None:
        out_dir = (
            ROOT
            / "3. Report Generator"
            / "d. Gemini Output MD"
            / args.inp.stem
        )
        args.out = out_dir / f"{Path(args.template).stem}.md"

    report = generate_report(
        case, prompt_path, [args.template]
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"✔ Saved report → {args.out}")


if __name__ == "__main__":
    main()
