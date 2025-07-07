"""Gemini caller and Jinja template renderer."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any

import google.generativeai as genai
import yaml
from jinja2 import Template

DEFAULT_API_KEY = "AIzaSyDZ6Z6xaRLpQDY-lucjfp8f8Z45mEbn1cs"

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "0. Config" / "query_configs.yaml"


def _load_config() -> Dict[str, Any]:
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}


def _parse_response(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if match:
        text = match.group(1)
    return json.loads(text)


def query_gemini(structured: Dict[str, Any], prompt: str, templates: List[str]) -> Dict[str, Any]:
    cfg = _load_config()
    api_key = os.environ.get("GOOGLE_API_KEY", DEFAULT_API_KEY)
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("models/gemini-1.5-pro-latest")
    user_payload = json.dumps({"pre_report": structured, "templates": templates}, ensure_ascii=False)
    resp = model.generate_content([
        {"role": "system", "parts": [prompt]},
        {"role": "user", "parts": [user_payload]},
    ], generation_config={
        "top_p": cfg.get("top_p", 0.8),
        "max_output_tokens": cfg.get("max_output_tokens", 2048),
    })
    return _parse_response(resp.text)


def render_template(template_text: str, context: Dict[str, Any]) -> str:
    return Template(template_text).render(**context)


def generate_report(structured: Dict[str, Any], prompt_path: Path, template_paths: List[Path]) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    templates = [p.read_text(encoding="utf-8") for p in template_paths]
    context = query_gemini(structured, prompt, templates)
    # Use first template for now
    return render_template(templates[0], context)
