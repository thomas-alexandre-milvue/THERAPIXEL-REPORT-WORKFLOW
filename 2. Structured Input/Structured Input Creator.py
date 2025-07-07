#!/usr/bin/env python3
"""
Structured Input Creator — strict-schema v1.2
============================================
*   Keeps **only** keys present in `Structured_Input_scheme.json`.
*   De‑duplicates each `rendering_positions` list, preserving **one** copy of each
    unique block (no more repeats).
*   Safe against `null` → falls back to blanks/dicts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

SCHEMA_FILE = "Structured_Input_scheme.json"
ALGO_NAME = "Therapixel MammoScreen"

# ─────────────────────────────────────────────────────────────────────────────
# Schema helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_schema(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"[ERROR] Cannot read schema {path}: {e}")


def _collect_keys(schema: Dict[str, Any], chain: Tuple[str, ...] = ()) -> Dict[str, Set[str]]:
    """Return mapping { dotted_path : set(child_keys) }."""
    out: Dict[str, Set[str]] = {}
    for k, v in schema.items():
        new_chain = chain + (k,)
        dotted = ".".join(new_chain)
        if isinstance(v, dict):
            out[dotted] = set(v.keys())
            out.update(_collect_keys(v, new_chain))
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            out[dotted] = set(v[0].keys())
            out.update(_collect_keys(v[0], new_chain))
    return out

# Base paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent          # project root one level up
SCHEMA_PATH = ROOT / "0. Config" / SCHEMA_FILE

schema = _load_schema(SCHEMA_PATH)
keymap = _collect_keys(schema)

TOP_KEYS = {k for k, v in schema.items() if not isinstance(v, (dict, list))} | {"prior", "views", "findings"}
PRIOR_KEYS = keymap.get("prior", set())
VIEW_KEYS = keymap.get("views", set())
FIND_KEYS = keymap.get("findings", set())
RENDER_KEYS = keymap.get("findings.rendering_positions", set())

# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def _max_score(findings: List[Dict[str, Any]], side: str) -> int:
    return max((f.get("mammoscreen_score", 0) for f in findings if f.get("laterality") == side), default=0)


def _laterality(has_left: bool, has_right: bool) -> str:
    return "B" if has_left and has_right else "L" if has_left else "R" if has_right else ""


def _filter(d: Dict[str, Any], allowed: Set[str]) -> Dict[str, Any]:
    return {k: d.get(k, "") for k in allowed if k in d}


def _dedup(list_of_dicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates while preserving first appearance order."""
    seen: Set[Tuple[Tuple[str, Any], ...]] = set()
    uniq: List[Dict[str, Any]] = []
    for item in list_of_dicts:
        fp = tuple(sorted(item.items()))
        if fp not in seen:
            seen.add(fp)
            uniq.append(item)
    return uniq

# ─────────────────────────────────────────────────────────────────────────────
# Core conversion
# ─────────────────────────────────────────────────────────────────────────────

def _convert_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    findings_raw = raw.get("findings", [])

    left_score = _max_score(findings_raw, "LEFT")
    right_score = _max_score(findings_raw, "RIGHT")

    out = {k: raw.get(k, "") for k in TOP_KEYS if k not in {"prior", "views", "findings"}}
    out.setdefault("manufacturer", ALGO_NAME)
    out["left_mammoscreen_score"] = left_score
    out["right_mammoscreen_score"] = right_score
    out["laterality"] = _laterality(bool(left_score), bool(right_score))

    # prior


    prior_src = raw.get("prior") or {}


    # Ensure all keys required by schema are present; use None when missing


    prior_norm = {k: prior_src.get(k, None) for k in PRIOR_KEYS}


    out["prior"] = prior_norm

    # views
    out["views"] = [_filter(v, VIEW_KEYS) for v in raw.get("views", [])]

    # findings
    norm_findings: List[Dict[str, Any]] = []
    for f in findings_raw:
        nf = _filter(f, FIND_KEYS)
        rp_filtered = [_filter(rp, RENDER_KEYS) for rp in f.get("rendering_positions", [])]
        nf["rendering_positions"] = _dedup(rp_filtered)
        norm_findings.append(nf)
    out["findings"] = norm_findings

    return out

# ─────────────────────────────────────────────────────────────────────────────
# I/O helpers
# ─────────────────────────────────────────────────────────────────────────────

def _out_name(src: Path) -> str:
    return f"{src.stem} Structured Input{src.suffix}"


def _process_file(src: Path, dst_dir: Path) -> None:
    structured = _convert_record(json.loads(src.read_text(encoding="utf-8")))
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / _out_name(src)
    dst.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✔ {src.name} → {dst.relative_to(dst_dir.parent)}")

# ─────────────────────────────────────────────────────────────────────────────
# Bulk
# ─────────────────────────────────────────────────────────────────────────────

def _bulk(inp: Path, out: Path) -> None:
    if not inp.exists():
        sys.exit(f"[ERROR] Input folder not found: {inp}")
    files = sorted(inp.glob("*.json"))
    if not files:
        sys.exit(f"[ERROR] No .json files in {inp}")
    for src in files:
        _process_file(src, out)

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser("Convert MammoScreen JSONs to strict Structured Input schema",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("-i", "--in", dest="inp", type=Path, default=ROOT / "1. Input", help="Raw JSON folder")
    p.add_argument("-o", "--out", dest="out", type=Path, default=ROOT / "2. Structured Input", help="Output folder")
    args = p.parse_args()
    _bulk(args.inp, args.out)


if __name__ == "__main__":
    main()
