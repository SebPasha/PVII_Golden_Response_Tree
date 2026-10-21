"""A stand-in model client and document, and a data tree of each test's own.

Nothing here touches the network, the source library or the real data/ folder: every test
writes under tmp_path, and the client answers what the test tells it to.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pvii import config, llm  # noqa: E402


class FakeClient:
    """Answers per step from `answers[step]`: a function of the prompt, or a fixed value."""

    def __init__(self, answers=None, dry_run=False):
        self.answers = answers or {}
        self.dry_run = dry_run
        self.ledger = llm.Ledger(100.0, 100000, dry_run=dry_run)
        self.prompts = {}

    def call(self, stage, prompt, expect="object", **_):
        self.prompts.setdefault(stage, []).append(prompt)
        a = self.answers.get(stage)
        return a(prompt) if callable(a) else json.loads(json.dumps(a))

    def map(self, stage, items, build_prompt, label="item", expect="object", **_):
        results, errors = [], []
        for i, it in enumerate(items):
            try:
                results.append(self.call(stage, build_prompt(it), expect=expect))
            except Exception as e:          # noqa: BLE001 - counted, as llm.map does
                results.append(None)
                errors.append((i, str(e)))
        return results, errors


class FakeDoc:
    def __init__(self, paragraphs, markdown=""):
        self.paragraphs = paragraphs
        self.markdown = markdown or "\n\n".join(p["content"] for p in paragraphs)
        self.page_count = max([p.get("page", 1) for p in paragraphs] or [0])
        self.name = "Test Plan"


def para(i, text, page=1, section=""):
    return {"ref": "Test Plan · p.%d · §%d" % (page, i), "page": page, "index": i,
            "role": None, "section": section, "content": text}


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    return tmp_path / "data"


@pytest.fixture
def configs(tmp_path, monkeypatch):
    d = tmp_path / "configs"
    d.mkdir()
    cfg = {"slug": "testland", "country": "Testland", "documents": [
        {"file": "data/sources/testland/plan_a.pdf", "doc_type": "ndp", "start": 2017,
         "end": 2021, "language": "en", "title": "Second Plan", "edition": "2nd"},
        {"file": "data/sources/testland/plan_b.pdf", "doc_type": "ndp", "start": 2022,
         "end": 2026, "language": "en", "title": "Third Plan", "edition": "3rd"},
        {"file": "data/sources/testland/sector.pdf", "doc_type": "sector", "start": 2022,
         "end": 2026, "language": "th", "title": "Health Plan"},
        {"file": "data/sources/testland/mystery.pdf", "doc_type": "other", "start": None,
         "end": None, "language": "en", "title": "mystery", "skip": "unidentified"},
        {"file": "data/sources/testland/open.pdf", "doc_type": "sector", "start": 2024,
         "end": None, "language": "en", "title": "Open Plan", "needs": "period"}]}
    (d / "testland.json").write_text(json.dumps(cfg))
    monkeypatch.setattr(config, "CONFIGS_DIR", str(d))
    return d
