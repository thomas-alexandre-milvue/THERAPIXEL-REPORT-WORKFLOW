"""Utility functions for selecting prompts and templates based on study modality."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, List, Any

try:  # Optional dependency when only CLI help is required
    import yaml
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
MAP_FILE = ROOT / "0. Config" / "modality_map.yaml"


def load_mapping(path: Path = MAP_FILE) -> Dict[str, Dict[str, str]]:
    """Return modality mapping from yaml."""
    if yaml is None:
        raise ImportError("PyYAML is required for this operation")
    return yaml.safe_load(path.read_text())


def select_for_case(case: Dict[str, Any]) -> Tuple[Path, List[Path]]:
    """Return the prompt file and list of template files for the given case."""
    mapping = load_mapping()
    modality = case.get("views", [{}])[0].get("image_modality", "").lower()
    if not modality:
        raise ValueError("Cannot determine modality from structured input")
    info = mapping.get(modality)
    if not info:
        raise KeyError(f"Unknown modality: {modality}")
    prompt = ROOT / info["prompt"]
    templates_dir = ROOT / info["templates"]
    templates = sorted(p for p in templates_dir.rglob("*.md"))
    if not templates:
        raise FileNotFoundError(f"No templates under {templates_dir}")
    return prompt, templates
