"""Gemini client returning Markdown reports."""
from __future__ import annotations

import os
import re
import json
import logging
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

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "0. Config" / "query_configs.yaml"


def _load_config() -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML is required for this operation")
    if CONFIG.exists():
        return yaml.safe_load(CONFIG.read_text())
    return {}



def _strip_reasoning(text: str) -> str:
    """Return the text without any trailing reasoning section."""
    return re.split(r"\n+Reasoning", text, 1)[0].rstrip()


def query_gemini(structured: Dict[str, Any], prompt: str, templates: List[str]) -> str:
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
    retries = cfg.get("retries", 2)
    last_reason = None
    defaults = {
        "temperature": 0.4,
        "top_p": 0.8,
        "max_output_tokens": 2048,
        "response_mime_type": "text/plain",
    }
    gcfg = cfg.get("generationConfig") or cfg.get("generation_config") or {}
    gen_cfg = {
        "temperature": gcfg.get(
            "temperature", cfg.get("temperature", defaults["temperature"])
        ),
        "top_p": gcfg.get(
            "topP", gcfg.get("top_p", cfg.get("top_p", defaults["top_p"]))
        ),
        "max_output_tokens": gcfg.get(
            "maxOutputTokens",
            gcfg.get(
                "max_output_tokens",
                cfg.get("max_output_tokens", defaults["max_output_tokens"]),
            ),
        ),
        "response_mime_type": gcfg.get(
            "responseMimeType",
            gcfg.get(
                "response_mime_type",
                cfg.get("response_mime_type", defaults["response_mime_type"]),
            ),
        ),
    }
    gen_cfg["response_mime_type"] = gcfg.get(
        "response_mime_type",
        cfg.get("response_mime_type", defaults["response_mime_type"]),
    )

    for attempt in range(retries + 1):
        resp = model.generate_content(
            user_payload,
            generation_config=gen_cfg,
        )
        candidate = resp.candidates[0]
        parts = getattr(candidate.content, "parts", [])
        if parts:
            text = "".join(getattr(p, "text", str(p)) for p in parts)
            return _strip_reasoning(text)
        last_reason = candidate.finish_reason
        print(
            f"[query_gemini] Empty response (finish_reason={last_reason}), retrying {attempt + 1}/{retries}",
            flush=True,
        )

    raise RuntimeError(f"Gemini returned no content (finish_reason={last_reason})")


def generate_reports(
    structured: Dict[str, Any],
    prompt_path: Path | None,
    template_paths: List[Path],
    *,
    json_dir: Path | None = None,
) -> Dict[str, str]:
    """Return rendered reports for all templates.

    Parameters
    ----------
    structured : Dict[str, Any]
        Normalised input data.
    prompt_path : Path | None
        Path to the system prompt text.
    template_paths : List[Path]
        Report templates to feed Gemini.
    json_dir : Path | None, optional
        If provided, raw responses from Gemini are written here with one
        file per template name.
    """
    cfg = _load_config()
    if prompt_path is None:
        prompt_path = ROOT / cfg.get("prompt_file", "")
    prompt = prompt_path.read_text(encoding="utf-8")

    reports: Dict[str, str] = {}
    for path in template_paths:
        template_text = path.read_text(encoding="utf-8")
        text = query_gemini(structured, prompt, [template_text])
        if json_dir is not None:
            json_dir.mkdir(parents=True, exist_ok=True)
            (json_dir / f"{path.stem}.md").write_text(text, encoding="utf-8")
        reports[path.stem] = text

    return reports


def generate_report(
    structured: Dict[str, Any],
    prompt_path: Path | None,
    template_paths: List[Path],
    *,
    json_dir: Path | None = None,
) -> str:
    reports = generate_reports(
        structured, prompt_path, template_paths, json_dir=json_dir
    )
    return reports[next(iter(reports))]
