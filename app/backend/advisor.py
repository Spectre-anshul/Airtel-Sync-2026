"""Advisor = needs discovery + rules engine + LLM explainer with a grounding guard.

The LLM never chooses products or prices. It receives the bundle the rules engine picked and is
asked to explain it. Every reply is checked by `grounding_violations`; any number, product name or
product id that is not in the facts sent to the model makes the reply fail, and the deterministic
template explanation is used instead.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable

from .config import ADVISOR_MODEL
from .data import business_type_segments, catalogue, city_tiers
from .i18n import WHY, t
from .privacy import get_logger
from .rules import NEED_PRODUCTS, Profile, profile_from_dict, recommend

log = get_logger("advisor")

LLM = Callable[[str, str], str]   # (system_prompt, user_prompt) -> text

# ---------------------------------------------------------------------------------------------
# Needs discovery from free text (English + Hindi), deterministic
# ---------------------------------------------------------------------------------------------
HINDI_CITIES = {
    "दिल्ली": "Delhi", "मुंबई": "Mumbai", "बेंगलुरु": "Bengaluru", "बैंगलोर": "Bengaluru", "चेन्नई": "Chennai",
    "हैदराबाद": "Hyderabad", "कोलकाता": "Kolkata", "पुणे": "Pune", "अहमदाबाद": "Ahmedabad", "जयपुर": "Jaipur",
    "लखनऊ": "Lucknow", "पटना": "Patna", "भोपाल": "Bhopal", "इंदौर": "Indore", "नागपुर": "Nagpur", "सूरत": "Surat",
    "वडोदरा": "Vadodara", "नासिक": "Nashik", "लुधियाना": "Ludhiana", "कोच्चि": "Kochi", "मैसूरु": "Mysuru",
    "कोयंबटूर": "Coimbatore", "विशाखापत्तनम": "Visakhapatnam",
}
HINDI_BUSINESS = {
    "किराना": "Kirana store", "दुकान": "Kirana store", "सैलून": "Salon", "पार्लर": "Salon", "दवा": "Pharmacy",
    "फार्मेसी": "Pharmacy", "मेडिकल": "Pharmacy", "क्लिनिक": "Dental clinic", "डेंटल": "Dental clinic",
    "कोचिंग": "Coaching centre", "सीए": "CA firm", "बेकरी": "Bakery", "मिठाई": "Sweet shop", "रेस्टोरेंट": "Restaurant chain",
    "फैक्ट्री": "Auto-parts unit", "कारखाना": "Auto-parts unit", "होटल": "Budget hotel group",
}
NEED_WORDS = {
    "pos": ["pos", "billing", "bill ", "invoice", "बिलिंग", "बिल "],
    "cctv": ["cctv", "camera", "कैमरा", "सीसीटीवी"],
    "guest_wifi": ["wifi", "wi-fi", "वाईफाई", "वाई-फाई"],
    "whatsapp": ["whatsapp", "व्हाट्सएप", "व्हाट्सऐप"],
    "sms": ["sms", "एसएमएस"],
    "email": ["email", "e-mail", "ईमेल"],
    "backup": ["backup", "बैकअप"],
    "antivirus": ["antivirus", "virus", "ransomware", "वायरस"],
    "telephony": ["ivr", "telephony", "call recording", "sip"],
    "tollfree": ["toll-free", "toll free", "1800", "टोल फ्री"],
    "website": ["website", "वेबसाइट", "domain"],
    "failover": ["failover", "backup internet", "never go down"],
    "machine_iot": ["machine monitoring", "iot", "मशीन"],
    "fleet": ["fleet", "gps", "vehicle", "गाड़ी", "गाड़ियों"],
    "static_ip": ["static ip", "fixed ip"],
    "firewall": ["firewall", "फ़ायरवॉल"],
    "leased_line": ["leased line", "ill", "लीज़्ड लाइन", "लीज्ड लाइन"],
}
REQUEST_WORDS = {"P03": ["1 gbps", "1gbps", "1g fibre", "1 gb fibre", "gigabit"], "P10": ["sd-wan", "sdwan"],
                 "P06": ["100 mbps leased", "ill 100"], "P05": ["ill 20"]}
DISCOUNT_WORDS = ["discount", "cheaper", "% off", "%off", "free", "less price", "छूट", "डिस्काउंट", "सस्ता", "कम कीमत"]
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
GSTIN_IN_TEXT = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")


def _has(low: str, word: str) -> bool:
    """Whole-word match for Latin keywords ('ill' must not match 'billing'); substring for Hindi."""
    w = word.strip()
    if re.fullmatch(r"[a-z0-9 \-%./]+", w):
        return re.search(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", low) is not None
    return w in low


def parse_free_text(text: str) -> dict:
    """Extract profile slots from what the owner typed. Unknown slots are left out."""
    raw = text or ""
    s = raw.translate(DEVANAGARI_DIGITS)
    low = s.lower()
    out: dict = {"needs": [], "requested": []}
    m = re.search(r"(\d+)\s*(?:staff|employees|people|workers|log|लोग|कर्मचारी|स्टाफ)", low)
    if m:
        out["employees"] = int(m.group(1))
    m = re.search(r"(\d+)\s*(?:sites|site|shops|stores|outlets|branches|offices|locations|दुकानें|दुकान|शाखा|ब्रांच|जगह)", low)
    if m:
        out["sites"] = int(m.group(1))
    for city in city_tiers():
        if city.lower() in low:
            out["city"] = city
    for hi, en in HINDI_CITIES.items():
        if hi in raw:
            out["city"] = en
    types = sorted(business_type_segments(), key=len, reverse=True)
    for bt in types:
        if bt.lower() in low:
            out["business_type"] = bt
            break
    else:
        for word, bt in [("kirana", "Kirana store"), ("clinic", "Dental clinic"), ("salon", "Salon"),
                         ("pharmacy", "Pharmacy"), ("chemist", "Pharmacy"), ("restaurant", "Restaurant chain"),
                         ("factory", "Auto-parts unit"), ("coaching", "Coaching centre"), ("ca firm", "CA firm"),
                         ("lawyer", "Law office"), ("bakery", "Bakery"), ("hotel", "Budget hotel group")]:
            if word in low:
                out["business_type"] = bt
                break
        else:
            for hi, bt in HINDI_BUSINESS.items():
                if hi in raw:
                    out["business_type"] = bt
                    break
    for need, words in NEED_WORDS.items():
        if any(_has(low, w) for w in words):
            out["needs"].append(need)
    for pid, words in REQUEST_WORDS.items():
        if any(_has(low, w) for w in words):
            out["requested"].append(pid)
    if any(w in low for w in ["no fibre", "no fiber", "fibre not available", "फाइबर नहीं"]):
        out["fibre_available"] = False
    g = GSTIN_IN_TEXT.search(s.upper())
    if g:
        out["gstin"] = g.group(0)
    out["asked_discount"] = any(w in low for w in DISCOUNT_WORDS)
    if re.search(r"[ऀ-ॿ]", raw):
        out["lang"] = "hi"
    return out


# ---------------------------------------------------------------------------------------------
# Template explanation (also the fallback)
# ---------------------------------------------------------------------------------------------
def _fmt_inr(n: int) -> str:
    """Indian digit grouping: 1234567 -> 12,34,567."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def _reason_text(r: dict, lang: str, ctx: dict) -> str:
    out = []
    for f in r["reasons"]:
        rule = f["rule"]
        kw = {"name": r["name"], "city": ctx.get("city") or "-"}
        if rule == "city_tier":
            kw.update(need="/".join(str(x) for x in f["need"]), have=f["have"])
        elif rule in ("min_employees", "min_sites"):
            kw.update(need=f["need"], have=f["have"])
        elif rule == "requires_gstin":
            st = (f.get("gst_status") or "none").lower()
            kw["status"] = t(f"gst_status_{st}", lang) if st in ("cancelled", "suspended", "invalid") else ""
        out.append(t(f"r_{rule}", lang, **kw))
    s = " ".join(out)
    if r.get("substitute"):
        s += t("r_substitute", lang, sub=catalogue().loc[r["substitute"], "product_name"])
    return s


def template_explanation(rec: dict, lang: str = "en", asked_discount: bool = False) -> str:
    ctx = rec["context"]
    on = [i for i in rec["items"] if i["on"]]
    lines = [t("intro", lang, business=ctx.get("business_type") or "business", employees=ctx["employees"],
               sites=ctx["sites"], s_plural="" if ctx["sites"] == 1 else "s", city=ctx.get("city") or "-",
               bundle=rec["bundle_name"])]
    for i in on:
        lines.append(t("item_line", lang, qty=i["qty"], name=i["name"], why=WHY[i["product_id"]][lang]))
    tt = rec["totals"]
    lines.append(t("total", lang, monthly=_fmt_inr(tt["monthly"]), monthly_max=_fmt_inr(tt["monthly_max"]),
                   setup=_fmt_inr(tt["setup"]), contract=tt["contract_months"], days=tt["install_days"]))
    shown = [r for r in rec["refused"] if r.get("asked") or not r.get("template") or r.get("substitute")]
    if shown:
        lines.append(t("refused_header", lang))
        lines += [f"- {_reason_text(r, lang, ctx)}" for r in shown]
    # only items a GSTIN alone would unlock (not those that also fail size/tier rules)
    gst_locked = [lk["name"] for lk in rec["locked"] if [f["rule"] for f in lk["reasons"]] == ["requires_gstin"]]
    if gst_locked:
        lines.append(t("locked_header", lang, names=", ".join(gst_locked)))
    if asked_discount:
        lines.append(t("fixed_price", lang))
    lines.append(t("toggle_hint", lang))
    # Markdown: a paragraph straight after a list item is swallowed into it, so separate blocks
    out = []
    for i, ln in enumerate(lines):
        if i and not (ln.startswith("- ") and lines[i - 1].startswith("- ")) and not (
                ln.startswith("- ") and lines[i - 1].endswith(":")):
            out.append("")
        out.append(ln)
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------
# Grounding guard
# ---------------------------------------------------------------------------------------------
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def facts_for_llm(rec: dict, lang: str, asked_discount: bool) -> dict:
    ctx = rec["context"]
    return {
        "language": "Hindi" if lang == "hi" else "English",
        "customer": {"business_type": ctx.get("business_type"), "staff": ctx["employees"], "sites": ctx["sites"],
                     "city": ctx.get("city"), "city_tier": ctx["tier"], "gstin_status": ctx["gst_status"]},
        "bundle_name": rec["bundle_name"],
        "included": [{"product": i["name"], "qty": i["qty"], "price_per_unit_inr": i["unit_price"],
                      "line_total_inr": i["qty"] * i["unit_price"], "why": WHY[i["product_id"]]["en"]}
                     for i in rec["items"] if i["on"]],
        "optional_addons_off": [{"product": i["name"], "price_per_unit_inr": i["unit_price"]}
                                for i in rec["items"] if not i["on"]],
        "not_allowed": [{"product": r["name"], "reason": _reason_text(r, "en", ctx)} for r in rec["refused"]
                        if r.get("asked") or not r.get("template") or r.get("substitute")],
        "locked_until_gstin": [lk["name"] for lk in rec["locked"]],
        "totals": {"monthly_inr": rec["totals"]["monthly"], "list_price_ceiling_inr": rec["totals"]["monthly_max"],
                   "one_time_setup_inr": rec["totals"]["setup"], "contract_months": rec["totals"]["contract_months"],
                   "install_days": rec["totals"]["install_days"]},
        "customer_asked_for_discount": asked_discount,
    }


def _allowed_numbers(facts: dict) -> set[int]:
    nums: set[int] = set()

    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            nums.add(int(x))
        elif isinstance(x, str):
            for m in NUM_RE.findall(x):
                nums.add(int(float(m.replace(",", ""))))
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(facts)
    return nums


def grounding_violations(text: str, facts: dict) -> list[str]:
    """Return problems with an LLM reply; an empty list means every number, product name and
    product id in the reply appears in the facts sent to the model."""
    problems = []
    s = (text or "").translate(DEVANAGARI_DIGITS)
    allowed = _allowed_numbers(facts)
    for m in NUM_RE.findall(s):
        try:
            v = int(float(m.replace(",", "").rstrip(".")))
        except ValueError:
            continue
        if v not in allowed:
            problems.append(f"number {m} is not in the bundle facts")
    if "%" in s:
        problems.append("percentage mentioned (no discounts exist)")
    named = {p["product"] for k in ("included", "optional_addons_off", "not_allowed") for p in facts[k]}
    named |= set(facts["locked_until_gstin"])
    for pid, name in catalogue()["product_name"].items():
        if name not in named and name.lower() in s.lower():
            problems.append(f"product {name!r} is not in the bundle facts")
        if re.search(rf"\b{pid}\b", s):
            problems.append(f"product id {pid} exposed")
    return problems


SYSTEM_PROMPT = (
    "You are the Accel Business advisor for small-business owners in India. A rules engine has ALREADY "
    "chosen the bundle and every price. Your only job is to explain it in plain, friendly {language}. "
    "Rules: (1) Do not add, remove or change any product, quantity, price, total or term. "
    "(2) Use only numbers that appear in the JSON facts; write rupee amounts exactly as given. "
    "(3) Never offer or hint at discounts, percentages or free items; if the customer asked for a discount, "
    "say politely that prices come from the catalogue. (4) If something the customer wanted is in "
    "'not_allowed', say why, using the reason given. (5) Never mention product codes. "
    "(6) At most 140 words, short paragraphs or bullets, no tables."
)


def anthropic_llm() -> LLM | None:
    if not ADVISOR_MODEL or not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic()

    def call(system: str, user: str) -> str:
        msg = client.messages.create(model=ADVISOR_MODEL, max_tokens=600, system=system,
                                     messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    return call


def explain(rec: dict, lang: str = "en", asked_discount: bool = False, llm: LLM | None = None) -> dict:
    facts = facts_for_llm(rec, lang, asked_discount)
    fallback = template_explanation(rec, lang, asked_discount)
    if llm is None:
        return {"text": fallback, "source": "template", "violations": []}
    try:
        reply = llm(SYSTEM_PROMPT.format(language=facts["language"]),
                    "Explain this bundle to the customer.\nFACTS:\n" + json.dumps(facts, ensure_ascii=False))
    except Exception as e:  # network / auth problems never break the journey
        log.info(f"llm error {type(e).__name__}; using template")
        return {"text": fallback, "source": "template", "violations": [f"llm_error: {type(e).__name__}"]}
    problems = grounding_violations(reply, facts)
    if problems:
        log.info(f"llm reply rejected by grounding guard: {problems[:3]}")
        return {"text": fallback, "source": "template", "violations": problems, "rejected_reply": reply}
    return {"text": reply, "source": "llm", "violations": []}


def advise(profile: dict | Profile, message: str | None = None, lang: str | None = None,
           llm: LLM | None | str = "auto") -> dict:
    """Full advisor turn: merge free text into the profile, run the rules engine, explain."""
    pdict = dict(profile.__dict__ if isinstance(profile, Profile) else profile)
    asked_discount = False
    if message:
        parsed = parse_free_text(message)
        asked_discount = parsed.pop("asked_discount", False)
        for k, v in parsed.items():
            if k in ("needs", "requested"):
                pdict[k] = list(dict.fromkeys(list(pdict.get(k) or []) + v))
            elif k == "lang" and (lang or pdict.get("lang")):
                continue
            else:
                pdict[k] = v
    lang = lang or pdict.get("lang") or "en"
    pdict["lang"] = lang
    p = profile_from_dict(pdict)
    rec = recommend(p)
    rec["_profile"] = {k: v for k, v in pdict.items() if k in Profile.__dataclass_fields__}
    model = anthropic_llm() if llm == "auto" else llm
    exp = explain(rec, lang, asked_discount, model)
    return {"profile": pdict, "recommendation": rec, "explanation": exp, "asked_discount": asked_discount}


__all__ = ["advise", "explain", "grounding_violations", "facts_for_llm", "parse_free_text",
           "template_explanation", "NEED_PRODUCTS"]
