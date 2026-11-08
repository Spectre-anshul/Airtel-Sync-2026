"""Udyam Express — Streamlit front end (English / हिन्दी), talks to the FastAPI backend.

Run (from app/):  streamlit run frontend/app.py
Backend URL:      API_URL env var, default http://127.0.0.1:8000
"""
from __future__ import annotations

import os
import sys

import httpx
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.i18n import LANGS, NEED_LABELS, STAGES, WHY, t  # noqa: E402  (strings only)

API = os.environ.get("API_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="Udyam Express · Accel Business", page_icon="📶", layout="centered")

st.markdown("""
<style>
.block-container {max-width: 760px; padding-top: 1.2rem;}
.price {font-size: 2.2rem; font-weight: 800; color: #E40000; line-height: 1.1}
.muted {color: #6b6b6b; font-size: .9rem}
.pill {display:inline-block; padding:.1rem .55rem; border-radius:999px; font-size:.78rem; font-weight:600}
.pill-ai {background:#fde8e8; color:#a10000} .pill-tpl {background:#eceff3; color:#333}
.verdict {padding: .8rem 1rem; border-radius: .6rem; font-weight: 700; font-size: 1.1rem}
.v-PASS,.v-AUTO_FIX {background:#e7f6ec; color:#0b6b2b} .v-RECAPTURE {background:#fff5db; color:#7a5200}
.v-HOLD,.v-REJECT {background:#fde8e8; color:#a10000}
.stage {padding:.35rem 0}
</style>""", unsafe_allow_html=True)

S = st.session_state
S.setdefault("lang", "en")
S.setdefault("page", "advisor")
S.setdefault("profile", {})
S.setdefault("advice", None)
S.setdefault("toggles", {})
S.setdefault("quote", None)
S.setdefault("consent_id", None)
S.setdefault("kyc", None)
S.setdefault("order_id", "")
S.setdefault("gst_check", None)


def L(key, **kw):
    return t(key, S.lang, **kw)


def inr(n: int) -> str:
    s = str(int(n))
    if len(s) <= 3:
        return "₹" + s
    head, tail, parts = s[:-3], s[-3:], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return "₹" + ",".join(([head] if head else []) + parts + [tail])


def api(method: str, path: str, **kw):
    try:
        r = httpx.request(method, API + path, timeout=120, **kw)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        st.error(f"Backend not reachable or returned an error ({e}). Is the API running at {API}?")
        st.stop()


# ---------------- header + navigation ------------------------------------------------------
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(f"### {L('app_title')}")
    st.caption(L("tagline"))
with c2:
    S.lang = st.radio("Language", list(LANGS), format_func=LANGS.get, index=list(LANGS).index(S.lang),
                      horizontal=True, label_visibility="collapsed")

PAGES = ["advisor", "quote", "kyc", "tracker", "backoffice"]
LABELS = {"advisor": L("nav_advisor"), "quote": L("nav_quote"), "kyc": L("nav_kyc"),
          "tracker": L("nav_tracker"), "backoffice": L("nav_backoffice")}
S.page = st.radio("nav", PAGES, index=PAGES.index(S.page), format_func=LABELS.get, horizontal=True,
                  label_visibility="collapsed")
st.divider()


def go(page):
    S.page = page
    st.rerun()


# ---------------- 1. Advisor ---------------------------------------------------------------
def page_advisor():
    cat_types = ["Kirana store", "Salon", "Pharmacy", "Bakery", "Sweet shop", "Boutique", "Hardware store",
                 "Mobile repair shop", "Dental clinic", "Diagnostic lab", "CA firm", "Law office", "Coaching centre",
                 "Insurance agency", "Real estate agency", "Restaurant chain", "Pharmacy chain", "Bakery chain",
                 "Gym chain", "Budget hotel group", "Auto-parts unit", "Textile unit", "Packaging unit",
                 "Food processing unit", "Furniture workshop", "Printing press"]
    cities = ["Ahmedabad", "Bengaluru", "Bhopal", "Chennai", "Coimbatore", "Delhi", "Hyderabad", "Indore", "Jaipur",
              "Kochi", "Kolkata", "Lucknow", "Ludhiana", "Mumbai", "Mysuru", "Nagpur", "Nashik", "Patna", "Pune",
              "Surat", "Vadodara", "Visakhapatnam"]
    p = S.profile
    with st.chat_message("assistant", avatar="📶"):
        st.write("Namaste! " + ("Tell me about your business and I'll build one bundle with one monthly price."
                                if S.lang == "en" else
                                "अपने बिज़नेस के बारे में बताइए, मैं एक बंडल और एक मासिक कीमत बनाऊँगा।"))
    with st.form("profile_form"):
        free = st.text_area(L("q_free"), placeholder=L("free_ph"), height=70)
        a, b = st.columns(2)
        bt = a.selectbox(L("q_business"), cat_types, index=cat_types.index(p.get("business_type", "Kirana store"))
                         if p.get("business_type") in cat_types else 0)
        city = b.selectbox(L("q_city"), cities, index=cities.index(p.get("city", "Lucknow")) if p.get("city") in cities else 11)
        emp = a.number_input(L("q_employees"), 1, 500, int(p.get("employees", 2)))
        sites = b.number_input(L("q_sites"), 1, 50, int(p.get("sites", 1)))
        gstin = st.text_input(L("q_gstin"), value=p.get("gstin") or "", max_chars=15).strip().upper()
        fibre = st.radio(L("q_fibre"), [True, False], format_func=lambda v: L("yes") if v else L("no"),
                         horizontal=True, index=0 if p.get("fibre_available", True) else 1)
        needs = st.multiselect(L("q_needs"), list(NEED_LABELS), default=p.get("needs", []),
                               format_func=lambda k: NEED_LABELS[k][S.lang])
        submitted = st.form_submit_button(L("btn_recommend"), type="primary", use_container_width=True)
    if submitted:
        prof = {"business_type": bt, "city": city, "employees": int(emp), "sites": int(sites),
                "gstin": gstin or None, "fibre_available": fibre, "needs": needs, "requested": []}
        S.gst_check = api("GET", f"/api/gstin/{gstin}") if gstin else None
        out = api("POST", "/api/advise", json={"profile": prof, "message": free or None, "lang": S.lang})
        _new_advice(out)
    if S.gst_check:
        g = S.gst_check
        if g["found"] and g["active"]:
            st.success(f"{L('gst_ok')} · {g['record']['gstin']} · {g['record']['legal_name']}")
        else:
            st.warning(L("gst_bad", status=g.get("status") or ("invalid checksum" if g["format_ok"] else "invalid format")))
    if S.advice:
        exp = S.advice["explanation"]
        with st.chat_message("assistant", avatar="📶"):
            if exp["source"] == "llm":
                txt = "AI explanation · checked against the rules engine" if S.lang == "en" else "AI व्याख्या · नियम इंजन से जाँची गई"
                badge = f'<span class="pill pill-ai">{txt}</span>'
            else:
                txt = "Rules-engine explanation" if S.lang == "en" else "नियम इंजन की व्याख्या"
                badge = f'<span class="pill pill-tpl">{txt}</span>'
            st.markdown(badge, unsafe_allow_html=True)
            st.markdown(exp["text"])
        msg = st.chat_input("Ask or change something… / कुछ पूछें या बदलें…")
        if msg:
            with st.chat_message("user"):
                st.write(msg)
            out = api("POST", "/api/advise", json={"profile": S.profile, "message": msg, "lang": S.lang})
            _new_advice(out)
            st.rerun()
        if st.button(L("btn_to_quote"), type="primary", use_container_width=True):
            go("quote")


# ---------------- 2. Quote -----------------------------------------------------------------
def _flip(pid: str):
    """Toggle callback: record the switch and drop the cached quote so it is re-priced server-side."""
    S.toggles[pid] = bool(S[f"tg_{pid}"])
    S.quote = None


def _new_advice(out: dict):
    S.profile, S.advice, S.toggles, S.quote = out["profile"], out, {}, None
    for k in [k for k in S.keys() if str(k).startswith("tg_")]:
        del S[k]


def page_quote():
    if not S.advice:
        st.info("Start with the advisor." if S.lang == "en" else "सलाहकार से शुरू करें।")
        return
    rec = S.advice["recommendation"]
    if S.quote is None:
        S.quote = api("POST", "/api/quote", json={"recommendation": rec, "toggles": S.toggles})
    q = S.quote
    st.markdown(f"#### {L('quote_title')}: {q['bundle_name']}")
    tt = q["totals"]
    st.markdown(f"<div class='price'>{inr(tt['monthly'])} <span class='muted'>{L('per_month')}</span></div>",
                unsafe_allow_html=True)
    upto = "list price up to" if S.lang == "en" else "सूची मूल्य"
    st.caption(f"{L('setup')}: {inr(tt['setup'])} · {L('contract')}: {tt['contract_months']} {L('months')} · "
               f"{L('install')}: {tt['install_days']} {L('days')} · {upto} {inr(tt['monthly_max'])}")

    st.markdown(f"**{L('included')}**")
    for it in [i for i in q["items"] if i["role"] == "core"]:
        st.markdown(f"✅ {it['qty']} × **{it['name']}** — {inr(it['unit_price'])} × {it['qty']} = "
                    f"**{inr(it['unit_price'] * it['qty'])}**  \n<span class='muted'>{WHY[it['product_id']][S.lang]}</span>",
                    unsafe_allow_html=True)
    st.markdown(f"**{L('addons')}**")
    for it in [i for i in q["items"] if i["role"] != "core"]:
        mo, su = ("/mo", "setup") if S.lang == "en" else ("/माह", "सेटअप")
        label = f"{it['qty']} × {it['name']} — {inr(it['unit_price'] * it['qty'])}{mo}" + (
            f" + {inr(it['setup_each'] * it['qty'])} {su}" if it["setup_each"] else "")
        key = f"tg_{it['product_id']}"
        if key not in S:
            S[key] = it["on"]
        st.toggle(label, key=key, help=WHY[it["product_id"]][S.lang], on_change=_flip, args=(it["product_id"],))
    if q["locked"] or [r for r in q["refused"] if r.get("asked")]:
        with st.expander(L("locked")):
            from backend.advisor import _reason_text   # same wording as the advisor
            for r in q["locked"] + [r for r in q["refused"] if r.get("asked")]:
                st.markdown(f"🔒 **{r['name']}** — {_reason_text(r, S.lang, q['context'])}")
    if st.button(L("btn_checkout"), type="primary", use_container_width=True):
        go("kyc")


# ---------------- 3. Smart KYC -------------------------------------------------------------
def page_kyc():
    if not S.consent_id:
        st.markdown(f"#### 🔐 {L('consent_title')}")
        st.markdown(L("consent_body"))
        agree = st.checkbox(L("consent_check"))
        if st.button(L("btn_consent"), type="primary", disabled=not agree, use_container_width=True):
            S.consent_id = api("POST", "/api/kyc/consent", json={"agreed": True, "lang": S.lang})["consent_id"]
            st.rerun()
        return
    st.caption(f"Consent {S.consent_id} ✓")
    tab_up, tab_demo = st.tabs(["Upload", L("specimen")])
    with tab_up:
        files = {
            "gst_certificate": st.file_uploader(L("upload_gst"), type=["png", "jpg", "jpeg"]),
            "udyam_certificate": st.file_uploader(L("upload_udyam"), type=["png", "jpg", "jpeg"]),
            "signatory_id": st.file_uploader(L("upload_sig"), type=["png", "jpg", "jpeg"]),
            "address_proof": st.file_uploader(L("upload_addr"), type=["png", "jpg", "jpeg"]),
        }
        if st.button(L("btn_verify"), type="primary", use_container_width=True):
            up = {k: (f.name, f.getvalue(), f.type) for k, f in files.items() if f is not None}
            with st.spinner("OCR + registry checks…"):
                S.kyc = api("POST", "/api/kyc/verify", files=up,
                            data={"consent_id": S.consent_id, "gstin": S.profile.get("gstin") or ""})
    with tab_demo:
        ids = api("GET", "/api/kyc/specimens")
        k = st.selectbox("Applicant", ids)
        if st.button("Run Smart KYC on " + k, use_container_width=True):
            with st.spinner("OCR + registry checks…"):
                S.kyc = api("POST", f"/api/kyc/specimen/{k}")
    if S.kyc:
        r = S.kyc
        st.markdown(f"<div class='verdict v-{r['verdict']}'>{L('v_' + r['verdict'])}</div>", unsafe_allow_html=True)
        res = r["resolved"]
        st.caption(" · ".join(x for x in [res.get("business_name"), res.get("gstin"), res.get("gst_status"),
                                          res.get("udyam_number")] if x))
        for f in r["auto_fixes"]:
            st.markdown(f"🛠️ {f}")
        for c in r["checks"]:
            icon = "✅" if c["ok"] else ("⚠️" if c["severity"] in ("RECAPTURE", "PASS") else "⛔")
            st.markdown(f"{icon} `{c['code']}` {c['detail']}" + (f"  \n→ **{c['action']}**" if c["action"] else ""))
        ok = r["verdict"] in ("PASS", "AUTO_FIX")
        label = L("btn_place_order") if ok else ("Submit for specialist review" if S.lang == "en" else "विशेषज्ञ जाँच के लिए भेजें")
        if S.quote and st.button(label, type="primary", use_container_width=True):
            o = api("POST", "/api/orders", json={
                "quote": S.quote, "business": res.get("business_name") or S.profile.get("business_type", ""),
                "contact_name": None, "gstin": None, "kyc_verdict": r["verdict"],
                "consent_id": S.consent_id, "lang": S.lang})
            S.order_id = o["id"]
            st.success(f"{L('order_placed')} **{o['id']}**")
            go("tracker")
        elif not S.quote:
            st.info("Build a quote first to place an order." if S.lang == "en" else "ऑर्डर के लिए पहले कोटेशन बनाएँ।")


# ---------------- 4. Tracker ---------------------------------------------------------------
def page_tracker():
    st.markdown(f"#### {L('tracker_title')}")
    oid = st.text_input(L("order_id"), value=S.order_id).strip().upper()
    if not oid:
        return
    o = api("GET", f"/api/orders/{oid}")
    S.order_id = oid
    st.markdown(f"**{o['bundle_name']}** · {o['business']} · {inr(o['totals']['monthly'])} {L('per_month')}")
    st.markdown(f"{L('eta')}: **{o['eta']}**")
    for s in o["stages"]:
        icon = "🟢" if s["done"] and not s["current"] else ("🔴" if s["current"] else "⚪")
        name = STAGES[s["key"]][S.lang]
        name = f"<b>{name}</b>" if s["current"] else name
        st.markdown(f"<div class='stage'>{icon} {name} "
                    f"<span class='muted'>· {s['planned']}</span></div>", unsafe_allow_html=True)
    if o["kyc_verdict"] not in ("PASS", "AUTO_FIX"):
        st.warning(L("v_" + o["kyc_verdict"]))
    st.info(L("no_call"))
    a, b = st.columns(2)
    if a.button(L("btn_advance"), use_container_width=True):
        api("POST", f"/api/orders/{oid}/advance")
        st.rerun()
    if o.get("consent_id") and not o["consent_withdrawn"] and b.button(L("withdraw"), use_container_width=True):
        api("POST", f"/api/kyc/consent/{o['consent_id']}/withdraw")
        st.rerun()
    if o["consent_withdrawn"]:
        st.caption("KYC consent withdrawn — documents and extracted fields are scheduled for deletion.")


# ---------------- back office (stretch goal) -----------------------------------------------
def page_backoffice():
    st.markdown("#### Back office — cases the digital journey could not close")
    bo = api("GET", "/api/backoffice")
    st.markdown("**Hand-offs** (KYC holds/rejects, inactive GSTINs)")
    st.dataframe(bo["handoffs"], use_container_width=True, hide_index=True)
    st.markdown("**Recent orders**")
    st.dataframe(bo["orders"], use_container_width=True, hide_index=True)


{"advisor": page_advisor, "quote": page_quote, "kyc": page_kyc, "tracker": page_tracker,
 "backoffice": page_backoffice}[S.page]()
