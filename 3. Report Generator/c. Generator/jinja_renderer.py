"""Gemini caller and Jinja template renderer."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

try:  # Optional dependencies when only CLI help is required
    import google.generativeai as genai
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    genai = None
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    yaml = None
try:
    from jinja2 import Template
except ModuleNotFoundError:  # pragma: no cover - handled at runtime
    Template = None

DEFAULT_API_KEY = "AIzaSyDZ6Z6xaRLpQDY-lucjfp8f8Z45mEbn1cs"

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "0. Config" / "query_configs.yaml"


def _load_config() -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML is required for this operation")
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}


def _parse_response(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if match:
        text = match.group(1)
    return json.loads(text)


def query_gemini(structured: Dict[str, Any], prompt: str, templates: List[str]) -> Dict[str, Any]:
    if genai is None:
        raise ImportError("google-generativeai package is required")
    cfg = _load_config()
    api_key = os.environ.get("GOOGLE_API_KEY", DEFAULT_API_KEY)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "models/gemini-1.5-pro-latest",
        system_instruction=prompt,
    )
    user_payload = json.dumps(
        {"pre_report": structured, "templates": templates},
        ensure_ascii=False,
    )
    resp = model.generate_content(
        user_payload,
        generation_config={
            "top_p": cfg.get("top_p", 0.8),
            "max_output_tokens": cfg.get("max_output_tokens", 2048),
        },
    )
    return _parse_response(resp.text)


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    if Template is None:
        raise ImportError("Jinja2 is required for this operation")
    return Template(template_text).render(**context)


def generate_reports(
    structured: Dict[str, Any],
    prompt_path: Path,
    template_paths: List[Path],
) -> Dict[str, str]:
    """Return rendered reports for all templates."""
    prompt = prompt_path.read_text(encoding="utf-8")
    templates = [p.read_text(encoding="utf-8") for p in template_paths]
    context = query_gemini(structured, prompt, templates)
    return {
        p.stem: render_template(t_text, context)
        for p, t_text in zip(template_paths, templates)
    }


def generate_report(
    structured: Dict[str, Any],
    prompt_path: Path,
    template_paths: List[Path],
) -> str:
    reports = generate_reports(structured, prompt_path, template_paths)
    return reports[next(iter(reports))]
