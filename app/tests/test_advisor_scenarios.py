"""The 15 advisor scenarios in advisor_scenarios.yaml, plus checks that apply to every scenario:
- every switched-on or optional item passes every catalogue eligibility rule
- every price equals the catalogue price_min
- the explanation is grounded (template passes the guard; a hallucinating LLM is rejected)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import yaml

from backend.advisor import advise, facts_for_llm, grounding_violations, parse_free_text, template_explanation
from backend.data import catalogue
from backend.rules import apply_toggles, eligibility

SCENARIOS = yaml.safe_load((Path(__file__).parent / "advisor_scenarios.yaml").read_text(encoding="utf-8"))
assert len(SCENARIOS) == 15


def run(sc, llm=None):
    return advise(dict(sc.get("profile") or {}), sc.get("message"), None, llm=llm)


def by_id(rec):
    return {i["product_id"]: i for i in rec["items"]}


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario(sc):
    out = run(sc)
    rec, exp = out["recommendation"], sc["expect"]
    items = by_id(rec)
    on = {k for k, v in items.items() if v["on"]}

    if "bundle_name" in exp:
        assert rec["bundle_name"] == exp["bundle_name"]
    if "segment" in exp:
        assert rec["segment"] == exp["segment"]
    if "gst_status" in exp:
        assert rec["context"]["gst_status"] == exp["gst_status"]
    if "lang" in exp:
        assert out["profile"]["lang"] == exp["lang"]
    if "asked_discount" in exp:
        assert out["asked_discount"] == exp["asked_discount"]
    for k, v in (exp.get("parsed") or {}).items():
        assert out["profile"][k] == v, k
    for pid in exp.get("on", []):
        assert pid in on, f"{pid} should be switched on; on={sorted(on)}"
    for pid in exp.get("off", []):
        assert pid not in on, f"{pid} must not be switched on"
    for pid in exp.get("optional", []):
        assert pid in items and not items[pid]["on"] and items[pid]["role"] == "optional"
    if "locked" in exp:
        assert sorted(x["product_id"] for x in rec["locked"]) == sorted(exp["locked"])
    refused = {r["product_id"]: r for r in rec["refused"]}
    for pid, rule in (exp.get("refused") or {}).items():
        assert pid in refused, f"{pid} should be refused; refused={list(refused)}"
        assert rule in [f["rule"] for f in refused[pid]["reasons"]]
    for pid, sub in (exp.get("substitute") or {}).items():
        assert refused[pid].get("substitute") == sub
    for pid, q in (exp.get("qty") or {}).items():
        assert items[pid]["qty"] == q, pid
    for k, v in (exp.get("totals") or {}).items():
        assert rec["totals"][k] == v, f"{k}: {rec['totals'][k]} != {v}"
    text = out["explanation"]["text"]
    for s in exp.get("explain_contains", []):
        assert s in text, f"{s!r} not in explanation:\n{text}"
    if out["profile"].get("lang") == "hi":
        assert re.search(r"[ऀ-ॿ]", text)

    if "toggles" in sc:
        q = apply_toggles(rec, sc["toggles"])
        errs = {e["product_id"]: e["error"] for e in q["toggle_errors"]}
        for pid, err in exp["toggle_errors"].items():
            assert errs.get(pid) == err
        qon = {i["product_id"] for i in q["items"] if i["on"]}
        assert "P01" in qon and "P15" not in qon
        for k, v in exp["totals_after_toggles"].items():
            assert q["totals"][k] == v


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_every_item_is_eligible_and_catalogue_priced(sc):
    rec = run(sc)["recommendation"]
    ctx = rec["context"]
    on = {i["product_id"] for i in rec["items"] if i["on"]}
    cat = catalogue()
    for it in rec["items"]:
        present = on - {it["product_id"]}
        assert eligibility(it["product_id"], ctx, present) == [], (it["product_id"], eligibility(it["product_id"], ctx, present))
        assert it["unit_price"] == int(cat.loc[it["product_id"], "price_min_inr_per_month"])
        assert it["setup_each"] == int(cat.loc[it["product_id"], "one_time_setup_inr"])
    t = rec["totals"]
    assert t["monthly"] == sum(i["qty"] * i["unit_price"] for i in rec["items"] if i["on"])


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_template_explanation_is_grounded(sc):
    out = run(sc)
    rec, lang = out["recommendation"], out["profile"]["lang"]
    facts = facts_for_llm(rec, lang, out["asked_discount"])
    assert grounding_violations(template_explanation(rec, lang, out["asked_discount"]), facts) == []


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_faithful_llm_reply_is_accepted(sc):
    def faithful(system, user):
        assert "ALREADY" in system and "FACTS" in user
        rec = run(sc)["recommendation"]
        return template_explanation(rec, "en")
    out = run(sc, llm=faithful)
    assert out["explanation"]["source"] == "llm", out["explanation"]["violations"]


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_hallucinating_llm_reply_is_rejected(sc):
    lie = sc.get("lying_llm_reply") or "Special offer today: 10% off, so you pay only ₹777 a month, plus a free Fleet Tracker (P25)."
    out = run(sc, llm=lambda s, u: lie)
    assert out["explanation"]["source"] == "template"
    assert out["explanation"]["violations"]
    assert out["explanation"]["text"] == template_explanation(
        out["recommendation"], out["profile"]["lang"], out["asked_discount"])


def test_llm_failure_falls_back_to_template():
    def boom(s, u):
        raise TimeoutError("network")
    out = run(SCENARIOS[0], llm=boom)
    assert out["explanation"]["source"] == "template"


def test_free_text_word_boundaries():
    p = parse_free_text("I need billing and possibly a website")
    assert "pos" in p["needs"] and "website" in p["needs"]
    assert "leased_line" not in p["needs"]      # 'ill' inside 'billing' must not match


@pytest.mark.skipif(not os.environ.get("ADVISOR_MODEL") or not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")),
                    reason="live LLM test needs ADVISOR_MODEL and ANTHROPIC_API_KEY")
@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_live_llm_never_changes_the_bundle(sc):
    out = run(sc, llm="auto")
    # Whatever the model says, the guard either accepted a grounded reply or fell back.
    exp = out["explanation"]
    if exp["source"] == "llm":
        facts = facts_for_llm(out["recommendation"], out["profile"]["lang"], out["asked_discount"])
        assert grounding_violations(exp["text"], facts) == []
    for k, v in (sc["expect"].get("totals") or {}).items():
        assert out["recommendation"]["totals"][k] == v
