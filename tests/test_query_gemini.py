import importlib.util
from pathlib import Path

GEN_DIR = (
    Path(__file__).resolve().parents[1]
    / '3. Report Generator'
    / 'c. Generator'
)
MOD_PATH = GEN_DIR / 'gemini_reporter.py'
spec = importlib.util.spec_from_file_location('reporter', MOD_PATH)
reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporter)


class Part:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate_content(self, *a, **kw):
        self.calls += 1
        return next(self.responses)


def fake_candidate(parts=None, finish_reason=0):
    class Content:
        def __init__(self, parts):
            self.parts = parts or []

    class Candidate:
        def __init__(self, parts, finish_reason):
            self.content = Content(parts)
            self.finish_reason = finish_reason

    class Response:
        def __init__(self, parts, finish_reason):
            self.candidates = [Candidate(parts, finish_reason)]
    return Response(parts, finish_reason)


def common(monkeypatch):
    monkeypatch.setattr(reporter, '_load_config', lambda: {'retries': 2})
    monkeypatch.setattr(
        reporter,
        'genai',
        type(
            'G',
            (),
            {
                'configure': lambda *a, **k: None,
                'GenerativeModel': lambda *a, **k: None,
            },
        ),
    )


def test_query_gemini_retries(monkeypatch):
    common(monkeypatch)
    responses = [
        fake_candidate([], 2),
        fake_candidate([], 2),
        fake_candidate([Part('ok')], 0),
    ]
    model = FakeModel(responses)
    monkeypatch.setattr(
        reporter,
        'genai',
        type(
            'G',
            (),
            {
                'configure': lambda *a, **k: None,
                'GenerativeModel': lambda *a, **k: model,
            },
        ),
    )
    out = reporter.query_gemini({}, 'p', ['t'])
    assert out == 'ok'
    assert model.calls == 3


def test_query_gemini_fail(monkeypatch):
    common(monkeypatch)
    responses = [
        fake_candidate([], 2),
        fake_candidate([], 2),
        fake_candidate([], 2),
    ]
    model = FakeModel(responses)
    monkeypatch.setattr(
        reporter,
        'genai',
        type(
            'G',
            (),
            {
                'configure': lambda *a, **k: None,
                'GenerativeModel': lambda *a, **k: model,
            },
        ),
    )
    try:
        reporter.query_gemini({}, 'p', ['t'])
    except RuntimeError as e:
        assert 'no content' in str(e)
    else:
        assert False, 'expected RuntimeError'
    assert model.calls == 3


def test_generation_config(monkeypatch):
    cfg = {"retries": 0}
    monkeypatch.setattr(reporter, "_load_config", lambda: cfg)
    captured = {}

    class Model:
        def generate_content(self, payload, generation_config=None):
            captured.update(generation_config)
            return fake_candidate([Part('x')], 0)

    monkeypatch.setattr(
        reporter,
        "genai",
        type(
            "G",
            (),
            {
                "configure": lambda *a, **k: None,
                "GenerativeModel": lambda *a, **k: Model(),
            },
        ),
    )
    out = reporter.query_gemini({}, "p", ["t"])
    assert out == "x"
    assert captured == {
        "temperature": 0.4,
        "top_p": 0.8,
        "max_output_tokens": 2048,
        "response_mime_type": "application/json",
    }


def test_generation_config_nested(monkeypatch):
    cfg = {
        "retries": 0,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.3,
            "maxOutputTokens": 999,
        },
    }
    monkeypatch.setattr(reporter, "_load_config", lambda: cfg)
    captured = {}

    class Model:
        def generate_content(self, payload, generation_config=None):
            captured.update(generation_config)
            return fake_candidate([Part('n')], 0)

    monkeypatch.setattr(
        reporter,
        "genai",
        type(
            "G",
            (),
            {
                "configure": lambda *a, **k: None,
                "GenerativeModel": lambda *a, **k: Model(),
            },
        ),
    )
    out = reporter.query_gemini({}, "p", ["t"])
    assert out == "n"
    assert captured == {
        "temperature": 0.7,
        "top_p": 0.3,
        "max_output_tokens": 999,
        "response_mime_type": "application/json",
    }
