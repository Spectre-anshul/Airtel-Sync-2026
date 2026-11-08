"""FastAPI app: mock registries, advisor, quote, Smart KYC, orders/tracker.

Run:  uvicorn backend.api:app --reload --port 8000   (from the app/ folder)
"""
from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import orders
from .advisor import advise
from .data import catalogue
from .kyc.service import lead_context, parse_upload, specimen_ids, verify, verify_specimen
from .privacy import get_logger, mask_gstin, mask_legal_name, mask_name, mask_udyam, scrub
from .registry import lookup_gstin, lookup_udyam
from .rules import apply_toggles

log = get_logger("api")
app = FastAPI(title="Accel Business · Udyam Express API", version="0.1.0")


# ---------------- mock registries ----------------------------------------------------------
@app.get("/api/gstin/{gstin}")
def gstin(gstin: str, masked: bool = True):
    r = lookup_gstin(gstin)
    log.info(f"gstin lookup {gstin} found={r['found']} status={r['status']}")
    if masked and r["record"]:
        r["record"] = {**r["record"], "gstin": mask_gstin(r["record"]["gstin"]),
                       "legal_name": mask_legal_name(r["record"]["legal_name"])}
        r["query"] = mask_gstin(r["query"])
        r["gstin"] = mask_gstin(r["gstin"])
    return r


@app.get("/api/udyam/{udyam}")
def udyam(udyam: str, masked: bool = True):
    r = lookup_udyam(udyam)
    log.info(f"udyam lookup {udyam} found={r['found']}")
    if masked and r["record"]:
        r["record"] = {**r["record"], "udyam_number": mask_udyam(r["record"]["udyam_number"])}
        r["query"] = mask_udyam(r["query"])
    return r


@app.get("/api/catalogue")
def get_catalogue():
    return catalogue().reset_index().to_dict("records")


# ---------------- advisor + quote ----------------------------------------------------------
class AdviseIn(BaseModel):
    profile: dict = Field(default_factory=dict)
    message: str | None = None
    lang: str | None = None


@app.post("/api/advise")
def api_advise(body: AdviseIn):
    out = advise(body.profile, body.message, body.lang)
    if out["recommendation"]["context"]["gst_status"] != "Active" and out["profile"].get("gstin"):
        orders.log_handoff("gst_not_active", out["profile"].get("business_type", ""),
                           f"status={out['recommendation']['context']['gst_status']}")
    return out


class QuoteIn(BaseModel):
    recommendation: dict
    toggles: dict[str, bool] = Field(default_factory=dict)


@app.post("/api/quote")
def api_quote(body: QuoteIn):
    # Never trust prices sent by the client: rebuild the recommendation from its context.
    from .rules import profile_from_dict, recommend
    prof = body.recommendation.get("_profile")
    if not prof:
        raise HTTPException(400, "recommendation must include _profile (as returned by /api/advise)")
    rec = recommend(profile_from_dict(prof))
    rec["_profile"] = prof
    return apply_toggles(rec, body.toggles)


# ---------------- Smart KYC -----------------------------------------------------------------
class ConsentIn(BaseModel):
    lang: str = "en"
    agreed: bool


@app.post("/api/kyc/consent")
def consent(body: ConsentIn):
    if not body.agreed:
        raise HTTPException(400, "consent required")
    cid = orders.record_consent("KYC for Accel Business order",
                                ["gstin", "udyam_number", "business_name", "constitution", "signatory_name",
                                 "signatory_designation", "bill_date"], body.lang)
    return {"consent_id": cid}


@app.post("/api/kyc/consent/{cid}/withdraw")
def withdraw(cid: str):
    return {"withdrawn": orders.withdraw_consent(cid)}


@app.post("/api/kyc/verify")
async def kyc_verify(consent_id: str = Form(...), gstin: str | None = Form(None), contact_name: str | None = Form(None),
                     gst_certificate: UploadFile | None = File(None), udyam_certificate: UploadFile | None = File(None),
                     signatory_id: UploadFile | None = File(None), address_proof: UploadFile | None = File(None)):
    if not consent_id:
        raise HTTPException(403, "consent required before KYC")
    docs = {}
    for dt_, f in (("gst_certificate", gst_certificate), ("udyam_certificate", udyam_certificate),
                   ("signatory_id", signatory_id), ("address_proof", address_proof)):
        if f is not None:
            docs[dt_] = parse_upload(await f.read(), f.filename or "", dt_)   # bytes stay in memory only
    ctx = lead_context(gstin=gstin) if gstin else None
    if ctx and contact_name:
        ctx["contact_name"] = contact_name
    return _masked(verify(docs, ctx).to_dict())


@app.get("/api/kyc/specimens")
def specimens():
    return specimen_ids()


@app.post("/api/kyc/specimen/{applicant}")
def kyc_specimen(applicant: str):
    if applicant not in specimen_ids():
        raise HTTPException(404, "unknown specimen")
    return _masked(verify_specimen(applicant).to_dict())


def _masked(d: dict) -> dict:
    res = d.get("resolved", {})
    if res.get("gstin"):
        res["gstin"] = mask_gstin(res["gstin"])
    if res.get("udyam_number"):
        res["udyam_number"] = mask_udyam(res["udyam_number"])
    if res.get("contact_name"):
        res["contact_name"] = mask_name(res["contact_name"])
    for c in d.get("checks", []):   # check details quote document text; mask IDs and people in them
        c["detail"] = scrub(c["detail"])
        for person in _people(c["detail"]):
            c["detail"] = c["detail"].replace(person, mask_name(person))
    return d


def _people(detail: str) -> list[str]:
    """Person names quoted in check details ('Signatory 'Nisha Arora' vs lead contact ...')."""
    import re
    out = re.findall(r"(?:Signatory|contact) '([^']+)'", detail)
    out += re.findall(r"'([^'(]+?) \(Prop\.", detail)
    return out


# ---------------- orders / tracker ---------------------------------------------------------
class OrderIn(BaseModel):
    quote: dict
    business: str
    contact_name: str | None = None
    gstin: str | None = None
    kyc_verdict: str
    consent_id: str | None = None
    lang: str = "en"


@app.post("/api/orders")
def create_order(body: OrderIn):
    return orders.create(body.quote, body.business, body.contact_name, body.gstin, body.kyc_verdict,
                         body.consent_id, body.lang)


@app.get("/api/orders/{oid}")
def get_order(oid: str):
    o = orders.get(oid)
    if not o:
        raise HTTPException(404, "order not found")
    return o


@app.post("/api/orders/{oid}/advance")
def advance_order(oid: str):
    o = orders.advance(oid)
    if not o:
        raise HTTPException(404, "order not found")
    return o


@app.get("/api/backoffice")
def backoffice():
    return orders.backoffice()


@app.get("/health")
def health():
    return {"ok": True}
