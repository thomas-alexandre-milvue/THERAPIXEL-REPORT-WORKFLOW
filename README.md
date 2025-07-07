# Radiology-to-Report Pipeline  
*A modular workflow that converts vendor breast‑imaging JSON into polished, template‑based clinical reports.*

---

## Table of Contents
1. [Key Features](#key-features)  
2. [Folder Layout](#folder-layout)  
3. [Quick‑start](#quick-start)  
4. [Step‑by‑step Workflow](#step-by-step-workflow)  
5. [Templates & Prompts](#templates--prompts)  
6. [Configuration Files](#configuration-files)  
7. [Developer Guide](#developer-guide)  
8. [Testing](#testing)  
9. [Troubleshooting FAQ](#troubleshooting-faq)  
10. [Contributing & Licence](#contributing--licence)

---

## Key Features
| Stage | Purpose | Highlights |
|-------|---------|------------|
| **Step 0 – Config** | Central location for schema & tuning knobs | Single‑source YAML files |
| **Step 1 – Input** | Stores raw vendor dumps for audit | Zero mutation of originals |
| **Step 2 – Structured Input** | Normalises diverse vendor JSON into a strict schema | `Structured Input Creator.py` auto‑fills mandatory keys |
| **Step 3 – Report Generator** | <ul><li>Selects the right prompt + template</li><li>Calls Gemini (Google Generative AI)</li><li>Renders Jinja → Markdown (or DOCX)</li></ul> | • Hot‑swappable prompts  <br>• Clinician‑editable templates |
| **Cross‑cutting** | Tests, helper CLIs, Pandoc utilities | Works on Windows / macOS / Linux |

---

## Folder Layout
```
repo-root/
│ README.md
│ pandoc-3.7.0.2-windows-x86_64.msi
├── 0. Config/
│   ├── Structured_Input_scheme.json
│   ├── modality_map.yaml
│   └── query_configs.yaml
├── 1. Input/
│   └── <vendor>.json
├── 2. Structured Input/
│   ├── Structured Input Creator.py
│   └── *.json
└── 3. Report Generator/
    ├── a. Prompts/
    │   └── Templator Prompt.yaml
    ├── b. Templates/
    │   ├── convert_docx_to_md.py
    │   ├── DOCX Source/
    │   │   └── TEMPLATE *.docx
    │   └── MarkDown/
    │       └── TEMPLATE *.md
    ├── c. Generator/
    │   ├── __init__.py
    │   ├── cli.py
    │   ├── jinja_renderer.py
    │   └── select_assets.py
```

---

## Quick‑start
```bash
# 1  Clone & create a virtual env
git clone https://github.com/<org>/rad-report-pipeline.git
cd rad-report-pipeline
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2  Install python deps
pip install -r requirements.txt

# 3  Export your Gemini API key
export GOOGLE_API_KEY=AIzaSyDZ6Z6xaRLpQDY-lucjfp8f8Z45mEbn1cs

# 4  Convert Word templates → Markdown (one‑off)
python "3. Report Generator/b. Templates/convert_docx_to_md.py"

# 5  Create structured input from raw case
python "2. Structured Input/Structured Input Creator.py"        "1. Input/Therapixel - Case 1 Test.json"        -o "2. Structured Input/"

# 6  Generate the clinical report
python "3. Report Generator/c. Generator/cli.py"        -i "2. Structured Input/Therapixel - Case 1 Test Structured Input.json"        -o "4. Reports/Case1_report.md"
# 7  Generate reports for all test cases
python "3. Report Generator/c. Generator/batch_cli.py"        -o "3. Report Generator/d. Tests"
# Windows users: run each line separately (don't paste two commands on one line).
```

---

## Step‑by‑step Workflow

### 1️⃣  Normalise raw JSON  
`Structured Input Creator.py` ingests vendor‑specific keys, enforces the schema in **0. Config/Structured_Input_scheme.json**, and inserts defaults (e.g. `prior.study_date: null`).

### 2️⃣  Select assets  
`select_assets.py` looks up **modality_map.yaml** to pair each case with:
* a system prompt (`a. Prompts/…`)
* a Markdown template (`b. Templates/MarkDown/…`)

### 3️⃣  Call Gemini  
`jinja_renderer.py` sends the full structured JSON as *user* content, with the modality‑specific prompt as *system* instruction.  
The prompt tells Gemini to reply with a compact JSON payload (`patient_name`, `birads`, etc.).

### 4️⃣  Render via Jinja  
Jinja2 merges the LLM payload into the chosen template → Markdown.  
Need DOCX? Simply run Pandoc:

```bash
pandoc report.md -o report.docx   --reference-doc="3. Report Generator/b. Templates/DOCX Source/reference.docx"
```

---

## Templates & Prompts
| Asset | Edited by | Location |
|-------|-----------|----------|
| **Word master templates** | Radiologists | `b. Templates/DOCX Source/*.docx` |
| **Markdown templates** | Devs + radiologists familiar with Git | `b. Templates/MarkDown/*.md` |
| **System prompts** | Prompt‑engineer | `a. Prompts/*.yaml` |

**Add a new template**

1. Drop a DOCX in *DOCX Source*.
2. Run `convert_docx_to_md.py` – this converts `[PLACEHOLDER]` tags to `{{ placeholder }}`.
3. Review the generated `.md`, tweak placeholder names if needed, commit.

---

## Configuration Files

| File | Purpose |
|------|---------|
| **Structured_Input_scheme.json** | JSON schema enforced by step 2. |
| **modality_map.yaml** | Maps `modality` → `{prompt, templates}`. |
| **query_configs.yaml** | Model, temperature, prompt file, max‑tokens, etc. |

Example `modality_map.yaml`
```yaml
mammography:
  prompt: 3. Report Generator/a. Prompts/Templator Prompt.yaml  # overridden by query_configs.yaml
  templates: 3. Report Generator/b. Templates/MarkDown
```

Example `query_configs.yaml`
```yaml
model_name: models/gemini-1.5-pro-latest
temperature: 0.4
top_p: 0.1
max_output_tokens: 6000
prompt_file: 3. Report Generator/a. Prompts/Templator Prompt - Modified for Mammo.yaml
```

---

## Developer Guide

### Style & tooling
* **Black** + **Ruff** enforced by pre‑commit.  
* Absolute imports (`from report_generator.c.Generator import …`) keep paths explicit.

### Secrets
`.env` (git‑ignored):
```env
GOOGLE_API_KEY=AIzaSyDZ6Z6xaRLpQDY-lucjfp8f8Z45mEbn1cs
```

### Add a new modality
1. Supply a prompt + template set.  
2. Append entry to `modality_map.yaml`.  
3. (Optional) extend `select_assets.py` inference.  

No pipeline code rewrite needed.

---

## Testing
```bash
pytest -q
```

---

## Troubleshooting FAQ
| Symptom | Remedy |
|---------|--------|
| `WinError 2` “pandoc not found” | Install Pandoc or `pip install pypandoc[binary]`. |
| `Unknown option --atx-headers` | Pandoc ≥ 3.0 – script auto‑detects this flag. |
| `couldn't unpack docx container` | Source file isn’t real `.docx` – re‑save from Word or run the converter helper. |
| Gemini `PermissionDenied` | Check API key and billing quota. |
| Missing variables in output | Ensure prompt JSON names match Jinja placeholders. |

---

## Contributing & Licence
* **Authors**: Milvue Product Team.

---

*Happy reporting!*  Create an issue or ping **@maintainer** if you get stuck.
