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
| **Step 3 – Report Generator** | <ul><li>Selects the right prompt + template</li><li>Calls Gemini (Google Generative AI)</li><li>Outputs Markdown reports</li></ul> | • Hot‑swappable prompts  <br>• Clinician‑editable templates |
| **Cross‑cutting** | Tests, helper CLIs, Pandoc utilities | Works on Windows / macOS / Linux |

---

## Folder Layout
```
repo-root/
├── .github/
├── .flake8
├── .gitignore
├── 0. Config/
├── 1. Input/
├── 2. Structured Input/
├── 3. Report Generator/
├── project_meta/
├── tests/
└── README.md
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
pip install -r project_meta/requirements.txt

# 3  Export your Gemini API key
export GOOGLE_API_KEY=AIzaSyDZ6Z6xaRLpQDY-lucjfp8f8Z45mEbn1cs

# 4  Convert Word templates → plain text (one‑off)
python "3. Report Generator/b. Templates/convert_docx_to_md.py"

# 5  Create structured input from raw case
python "2. Structured Input/Structured Input Creator.py"        "1. Input/Therapixel - Case 1 Test.json"        -o "2. Structured Input/"

# 6  Generate the clinical report
# choose structured input and template interactively
python "3. Report Generator/c. Generator/cli.py"
# or specify paths directly
# output folder defaults to `3. Report Generator/e. Final Report/<case>/`
python "3. Report Generator/c. Generator/cli.py" \
       -i "2. Structured Input/Therapixel - Case 1 Test Structured Input.json" \
       -o "3. Report Generator/e. Final Report/Case1_report.md"
#   Raw Gemini Markdown is saved automatically under `3. Report Generator/d. Gemini Markdown Responses`
#   Use -j to choose a different folder
python "3. Report Generator/c. Generator/cli.py" \
       -i "2. Structured Input/Therapixel - Case 1 Test Structured Input.json" \
       -o "3. Report Generator/e. Final Report/Case1_report.md" \
       -j "3. Report Generator/d. Gemini Markdown Responses"

# 7  Generate reports for all test cases
python "3. Report Generator/c. Generator/batch_cli.py"        -o "3. Report Generator/e. Final Report"
#   Markdown replies are stored in `3. Report Generator/d. Gemini Markdown Responses` by default
#   Use -j to choose a different folder
python "3. Report Generator/c. Generator/batch_cli.py"        -o "3. Report Generator/e. Final Report"        -j "3. Report Generator/d. Gemini Markdown Responses"
# Windows users: run each line separately (don't paste two commands on one line).

# 8  Collect all artifacts to Downloads
python export_workflow.py
#   Use -o to choose a different destination
```

---

## Step‑by‑step Workflow

### 1️⃣  Normalise raw JSON  
`Structured Input Creator.py` ingests vendor‑specific keys, enforces the schema in **0. Config/Structured_Input_scheme.json**, and inserts defaults (e.g. `prior.study_date: null`).

### 2️⃣  Select assets  
`select_assets.py` looks up **modality_map.yaml** to pair each case with:
* a system prompt (`a. Prompts/…`)
* a text template (`b. Templates/Text/…`)

This mapping file is required by the batch CLI; removing it will result in
errors when generating reports.

### 3️⃣  Call Gemini
`gemini_reporter.py` sends the structured JSON and template snippets to Gemini.
The model replies with a JSON block containing a list of Markdown lines:
`{"lines": ["..."]}`.
`gemini_reporter.py` joins these lines into the final Markdown report ready for clinicians.

### 4️⃣  (Optional) Convert to DOCX
If needed, Jinja or Pandoc can reformat the Markdown into a DOCX report:

```bash
pandoc report.md -o report.docx   --reference-doc="3. Report Generator/b. Templates/DOCX Source/reference.docx"
```

### 5️⃣  Export workflow artifacts
`export_workflow.py` copies raw inputs, structured JSON, templates, Gemini Markdown responses and final Markdown to your Downloads folder. Use `-o` to pick a different destination.

---

## Templates & Prompts
| Asset | Edited by | Location |
|-------|-----------|----------|
| **Word master templates** | Radiologists | `b. Templates/DOCX Source/*.docx` |
| **Text templates** | Devs + radiologists familiar with Git | `b. Templates/Text/*.md` |
| **System prompts** | Prompt‑engineer | `a. Prompts/*.yaml` |

**Add a new template**

1. Drop a DOCX in *DOCX Source*.
2. Run `convert_docx_to_md.py` – placeholders stay `[PLACEHOLDER]`; escape backslashes are removed.
3. Review the generated `.md`, tweak placeholder names if needed, commit.

---

## Configuration Files

| File | Purpose |
|------|---------|
| **Structured_Input_scheme.json** | JSON schema enforced by step 2. |
| **modality_map.yaml** | Maps `modality` → `{prompt, templates}`. |
| **query_configs.yaml** | Model, temperature, prompt file, max‑tokens, response type, etc. |

Example `modality_map.yaml`
```yaml
mammography:
  prompt: 3. Report Generator/a. Prompts/Templator Prompt.yaml  # overridden by query_configs.yaml
  templates: 3. Report Generator/b. Templates/Text
```

Example `query_configs.yaml`
```yaml
model_name: models/gemini-2.5-pro
generationConfig:
  temperature: 0.4
  topP: 0.1
  maxOutputTokens: 6000
  response_mime_type: application/json
prompt_file: 3. Report Generator/a. Prompts/Templator Prompt - Modified for Mammo.yaml
thinkingConfig:
  thinkingBudget: 3000  # cap hidden reasoning tokens
  includeThoughts: true # add a reasoning block after the JSON
```


---

## Developer Guide

### Style & tooling
* **Black** and **Ruff** optional; CI runs **flake8**.
* Modules loaded directly from `3. Report Generator/c. Generator` using `importlib`.

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
| Gemini returns plain text instead of JSON | Add `response_mime_type: application/json` under `generationConfig` in `0. Config/query_configs.yaml`. |

---

## Contributing & Licence
* **Authors**: Milvue Product Team.

---

*Happy reporting!*  Create an issue or ping **@maintainer** if you get stuck.
