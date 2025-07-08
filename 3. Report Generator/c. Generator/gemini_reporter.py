"""Gemini client returning Markdown reports."""
from __future__ import annotations

import os
import re
import json
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
    """Return JSON payload extracted from Gemini output."""
    text = re.split(r"\n+Reasoning", text, 1)[0]
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("No JSON object found in response")
    return json.loads(match.group(0))


def render_json_to_md(data: Dict[str, Any]) -> str:
    """Return Markdown string from Gemini JSON output."""
    lines = data.get("lines")
    if isinstance(lines, list):
        return "\n".join(lines).strip() + "\n"
    raise ValueError("Unsupported JSON structure")


def query_gemini(structured: Dict[str, Any], prompt: str, templates: List[str]) -> Dict[str, Any]:
    if genai is None:
        raise ImportError("google-generativeai package is required")
    cfg = _load_config()
    api_key = os.environ.get("GOOGLE_API_KEY", DEFAULT_API_KEY)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        cfg.get("model_name", "models/gemini-1.5-pro-latest"),
        system_instruction=prompt,
    )
    user_payload = json.dumps(
        {"pre_report": structured, "templates": templates},
        ensure_ascii=False,
    )
    resp = model.generate_content(
        user_payload,
        generation_config={
            "temperature": cfg.get("temperature", 0.4),
            "top_p": cfg.get("top_p", 0.8),
            "max_output_tokens": cfg.get("max_output_tokens", 2048),
        },
    )
    return _parse_response(resp.text)


def generate_reports(
    structured: Dict[str, Any],
    prompt_path: Path | None,
    template_paths: List[Path],
) -> Dict[str, str]:
    """Return rendered reports for all templates."""
    cfg = _load_config()
    if prompt_path is None:
        prompt_path = ROOT / cfg.get("prompt_file", "")
    prompt = prompt_path.read_text(encoding="utf-8")

    reports: Dict[str, str] = {}
    for path in template_paths:
        template_text = path.read_text(encoding="utf-8")
        data = query_gemini(structured, prompt, [template_text])
        reports[path.stem] = render_json_to_md(data)

    return reports


def generate_report(
    structured: Dict[str, Any],
    prompt_path: Path | None,
    template_paths: List[Path],
) -> str:
    reports = generate_reports(structured, prompt_path, template_paths)
    return reports[next(iter(reports))]
