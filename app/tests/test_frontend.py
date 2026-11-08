"""Streamlit UI smoke test (needs the API running on API_URL; skipped otherwise)."""
from __future__ import annotations

import os

import httpx
import pytest

API = os.environ.get("API_URL", "http://127.0.0.1:8000")
try:
    httpx.get(API + "/health", timeout=2)
    UP = True
except Exception:
    UP = False

pytestmark = pytest.mark.skipif(not UP, reason="API not running")
APP = os.path.join(os.path.dirname(__file__), "..", "frontend", "app.py")


def _at():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(APP, default_timeout=60)


def _to_quote(at, text="I run a kirana in Lucknow with 2 staff, need billing and CCTV"):
    # AppTest cannot click form-submit buttons, so seed the session with a real advisor reply.
    out = httpx.post(API + "/api/advise", json={"profile": {}, "message": text, "lang": "en"}, timeout=30).json()
    at.session_state["advice"] = out
    at.session_state["profile"] = out["profile"]
    at.session_state["page"] = "quote"
    at.run()
    return at


def price(at) -> str:
    return next(m.value for m in at.markdown if "class='price'" in m.value)


def test_toggle_reprices():
    at = _to_quote(_at())
    assert "2,694" in price(at)
    cctv = next(t for t in at.toggle if "CCTV" in t.label)
    assert cctv.value is True
    cctv.set_value(False).run()
    assert "2,296" in price(at), price(at)
    assert next(t for t in at.toggle if "CCTV" in t.label).value is False
    next(t for t in at.toggle if "Website" in t.label).set_value(True).run()
    assert "2,595" in price(at)


def test_hindi_labels():
    at = _at()
    at.session_state["lang"] = "hi"
    at.run()
    assert any("मेरा बंडल सुझाएँ" in b.label for b in at.button)
    at = _to_quote(_at())
    at.session_state["lang"] = "hi"
    at.run()
    assert "प्रति माह" in price(at)
