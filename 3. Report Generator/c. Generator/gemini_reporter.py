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
    # Direct Markdown via list of lines
    lines = data.get("lines")
    if isinstance(lines, list):
        return "\n".join(str(l).strip() for l in lines).strip() + "\n"
    if isinstance(lines, str):
        return lines.strip() + ("\n" if not lines.endswith("\n") else "")

    # Support alternate key names or nested dicts
    for key in ("markdown", "text", "report", "final_report", "content"):
        if key in data:
            value = data[key]
            if isinstance(value, dict):
                try:
                    return render_json_to_md(value)
                except ValueError:
                    pass
            if isinstance(value, list):
                return "\n".join(str(v).strip() for v in value).strip() + "\n"
            if isinstance(value, str):
                return value.strip() + ("\n" if not value.endswith("\n") else "")

    # Handle typical sectioned structures
    sections = []
    for key in (
        "title",
        "views",
        "technique",
        "findings",
        "conclusion",
        "birads",
        "impression",
    ):
        if key in data:
            value = data[key]
            if isinstance(value, list):
                value = "\n".join(str(v).strip() for v in value)
            elif isinstance(value, dict):
                try:
                    value = render_json_to_md(value).strip()
                except ValueError:
                    continue
            elif not isinstance(value, str):
                continue
            sections.append(str(value).strip())
    if sections:
        return "\n".join(s for s in sections if s).strip() + "\n"

    # Nested sections container
    for key in ("sections", "section", "parts"):
        if key in data:
            value = data[key]
            if isinstance(value, dict):
                try:
                    return render_json_to_md(value)
                except ValueError:
                    pass
            if isinstance(value, list):
                out = []
                for item in value:
                    if isinstance(item, dict):
                        try:
                            out.append(render_json_to_md(item).strip())
                        except ValueError:
                            continue
                    else:
                        out.append(str(item).strip())
                if out:
                    return "\n".join(out).strip() + "\n"

    # Fallback: first string value in dict
    for value in data.values():
        if isinstance(value, str):
            return value.strip() + ("\n" if not value.endswith("\n") else "")
        if isinstance(value, list):
            return "\n".join(str(v).strip() for v in value).strip() + "\n"
        if isinstance(value, dict):
            try:
                return render_json_to_md(value)
            except ValueError:
                continue

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
    # `.text` can raise an exception when Gemini returns an empty candidate.
    # Build the response text manually to handle safety blocks or other errors.
    candidate = resp.candidates[0]
    parts = getattr(candidate.content, "parts", [])
    if not parts:
        raise RuntimeError(
            f"Gemini returned no content (finish_reason={candidate.finish_reason})"
        )
    text = "".join(getattr(p, "text", str(p)) for p in parts)
    return _parse_response(text)


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
        If provided, raw JSON responses from Gemini are written here with one
        file per template name.
    """
    cfg = _load_config()
    if prompt_path is None:
        prompt_path = ROOT / cfg.get("prompt_file", "")
    prompt = prompt_path.read_text(encoding="utf-8")

    reports: Dict[str, str] = {}
    for path in template_paths:
        template_text = path.read_text(encoding="utf-8")
        data = query_gemini(structured, prompt, [template_text])
        if json_dir is not None:
            json_dir.mkdir(parents=True, exist_ok=True)
            out = json.dumps(data, ensure_ascii=False, indent=2)
            (json_dir / f"{path.stem}.json").write_text(out, encoding="utf-8")
        reports[path.stem] = render_json_to_md(data)

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
