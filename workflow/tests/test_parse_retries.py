"""Lifted from PV2 tests/unit/test_retries.py (the Document Intelligence half).

A dropped connection retries with backoff; a client error raises at once.

WHAT THIS ASSERTS
    Document Intelligence retries a transient error with backoff and raises a client error at
    once.

WHAT IT IS BLIND TO
    Whether the service ever answers. The analyser is a stand-in.
"""
import os

import pytest

from pvii import parse as P


class _Transient(Exception):
    pass


@pytest.mark.unit
def test_document_intelligence_retries_transient_errors_then_succeeds(monkeypatch):
    calls, slept = [], []
    ServiceRequestError = type("ServiceRequestError", (Exception,), {})

    def fake(path, endpoint, key):
        calls.append(1)
        if len(calls) < 3:
            raise ServiceRequestError("resolver hiccup")
        return {"markdown": "ok", "page_count": 1}
    monkeypatch.setattr(P, "_analyze", fake)
    out = P._analyze_with_retry("x.pdf", "e", "k", attempts=5, sleep=slept.append)
    assert out["markdown"] == "ok" and len(calls) == 3 and slept == [2, 4]


@pytest.mark.unit
def test_a_client_error_raises_at_once(monkeypatch):
    class HttpResponseError(Exception):
        status_code = 400
    calls = []

    def fake(path, endpoint, key):
        calls.append(1)
        raise HttpResponseError("bad request")
    monkeypatch.setattr(P, "_analyze", fake)
    with pytest.raises(HttpResponseError):
        P._analyze_with_retry("x.pdf", "e", "k", attempts=5, sleep=lambda s: None)
    assert len(calls) == 1


@pytest.mark.unit
def test_a_parse_pv2_paid_for_is_copied_in_and_its_cache_left_alone(tmp_path, monkeypatch):
    import json
    from pvii import config
    doc = tmp_path / "plan.pdf"
    doc.write_bytes(b"%PDF plan")
    old, new = tmp_path / "pv2cache", tmp_path / "cache"
    old.mkdir()
    name = "di_%s.json" % P.file_hash(str(doc))
    raw = {"paragraphs": [{"content": "The plan will build roads in every province.", "page": 1}],
           "markdown": "The plan will build roads in every province.", "page_count": 1}
    (old / name).write_text(json.dumps(raw))
    monkeypatch.setattr(config, "PARSE_CACHE_FALLBACK", str(old))
    monkeypatch.setattr(P, "_analyze", lambda *a: pytest.fail("must not call the service"))
    d = P.parse_document(str(doc), cache_dir=str(new))
    assert d.paragraphs[0]["content"].startswith("The plan will build roads")
    assert (new / name).exists() and sorted(os.listdir(old)) == [name]
