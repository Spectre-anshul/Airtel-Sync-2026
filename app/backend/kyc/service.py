"""KYC entry points used by the API, the UI and the tests."""
from __future__ import annotations

from pathlib import Path

from ..config import KYC_DIR
from ..data import leads
from ..privacy import get_logger
from .ocr import ocr_image
from .parse import DOC_TYPES, ParsedDoc, detect_type, parse
from .validate import KycResult, validate

log = get_logger("kyc")


def parse_upload(content: bytes | str | Path, filename: str = "", doc_type: str | None = None) -> ParsedDoc:
    res = ocr_image(content)
    return parse(res, filename=filename, doc_type=doc_type or detect_type(res.text, filename))


def specimen_ids() -> list[str]:
    return sorted({p.name.split("_")[0] for p in KYC_DIR.glob("K*_*.png")})


def specimen_files(applicant: str) -> dict[str, Path]:
    out = {}
    for dt in DOC_TYPES:
        p = KYC_DIR / f"{applicant}_{dt}.png"
        if p.exists():
            out[dt] = p
    return out


def lead_context(gstin: str | None = None, udyam: str | None = None, business_name: str | None = None) -> dict:
    """Find the applicant's lead record (what they told the advisor) by GSTIN, Udyam or name."""
    L = leads()
    m = L.iloc[0:0]
    if gstin:
        m = L[L.gstin == gstin]
    if m.empty and udyam:
        m = L[L.udyam_number == udyam]
    if m.empty and business_name:
        m = L[L.business_name == business_name]
        if len(m) != 1:
            m = m.iloc[0:0]
    if m.empty:
        return {}
    r = m.iloc[0]
    return {"lead_id": r.lead_id, "gstin": r.gstin or None, "udyam_number": r.udyam_number or None,
            "contact_name": r.contact_name, "business_name": r.business_name, "state": r.state, "city": r.city}


def _context_from_docs(docs: dict[str, ParsedDoc]) -> dict:
    from .. import gstin as gst
    from ..registry import gstin_exists
    g = docs.get("gst_certificate")
    if g and not g.blurred:
        for r in g.fields.get("gstin_reads", []):
            c = gst.correct(r, gstin_exists)
            if c["checksum_ok"] and gstin_exists(c["gstin"]):
                ctx = lead_context(gstin=c["gstin"])
                if ctx:
                    return ctx
    u = docs.get("udyam_certificate")
    if u and u.fields.get("udyam_number"):
        ctx = lead_context(udyam=u.fields["udyam_number"])
        if ctx:
            return ctx
    for dt, key in (("address_proof", "billed_to"), ("signatory_id", "business"), ("udyam_certificate", "enterprise_name")):
        d = docs.get(dt)
        if d and d.fields.get(key):
            ctx = lead_context(business_name=d.fields[key])
            if ctx:
                return ctx
    return {}


def verify(docs: dict[str, ParsedDoc], context: dict | None = None) -> KycResult:
    ctx = context or _context_from_docs(docs)
    result = validate(docs, ctx)
    result.resolved["lead_id"] = ctx.get("lead_id")
    result.resolved["business_name"] = ctx.get("business_name")
    result.resolved["contact_name"] = ctx.get("contact_name")
    log.info(f"kyc verdict={result.verdict} lead={ctx.get('lead_id')} gstin={result.resolved.get('gstin')}")
    return result


def verify_specimen(applicant: str) -> KycResult:
    docs = {dt: parse_upload(p, p.name, dt) for dt, p in specimen_files(applicant).items()}
    return verify(docs)
