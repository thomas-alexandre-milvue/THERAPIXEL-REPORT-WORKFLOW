#!/usr/bin/env python3
"""CLI entry point for the report generator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:  # When executed as part of a package
    from .select_assets import select_for_case
    from .jinja_renderer import generate_report
except ImportError:  # Fallback when run as a standalone script
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from select_assets import select_for_case
    from jinja_renderer import generate_report


def main() -> None:
    p = argparse.ArgumentParser(description="Generate clinical report from structured input")
    p.add_argument("-i", "--input", dest="inp", type=Path, required=True, help="Structured input JSON")
    p.add_argument("-o", "--output", dest="out", type=Path, required=True, help="Output Markdown file")
    args = p.parse_args()

    case = json.loads(args.inp.read_text(encoding="utf-8"))
    prompt_path, templates = select_for_case(case)
    report = generate_report(case, prompt_path, templates)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"✔ Saved report → {args.out}")


if __name__ == "__main__":
    main()
