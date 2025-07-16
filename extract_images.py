#!/usr/bin/env python3
"""Export encoded PNG images from raw input JSON files."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW_INPUTS = ROOT / "1. Input"


def _downloads_dir() -> Path:
    d = Path.home() / "Downloads"
    return d if d.exists() else Path.home()


def _find_images(obj) -> list[bytes]:
    images: list[bytes] = []

    def _walk(o):
        if isinstance(o, dict):
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
        elif isinstance(o, str) and len(o) > 50:
            try:
                data = base64.b64decode(o, validate=True)
            except Exception:
                return
            if data.startswith(b"\x89PNG"):
                images.append(data)

    _walk(obj)
    return images


def export(dest: Path) -> None:
    for js in RAW_INPUTS.glob("*.json"):
        case_dir = dest / js.stem
        case_dir.mkdir(parents=True, exist_ok=True)
        data = json.loads(js.read_text())
        images = _find_images(data)
        for idx, img in enumerate(images, 1):
            (case_dir / f"img_{idx}.png").write_bytes(img)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Copy decoded images from raw inputs to Downloads"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output directory (default: Downloads)"
    )
    args = parser.parse_args()

    root_dir = (args.output or _downloads_dir()) / "Raw JSON Images"
    root_dir.mkdir(parents=True, exist_ok=True)
    export(root_dir)
    print(f"Images exported to {root_dir}")


if __name__ == "__main__":
    main()
