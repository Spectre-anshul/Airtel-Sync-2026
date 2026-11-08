"""Smart KYC validation rules -> one verdict per applicant.

Rule order (from the KYC Answer Key sheet in model/Udyam_Digital_Model.xlsx):
OCR -> GSTIN format + mod-36 checksum -> registry status -> Udyam lookup -> name match across
documents and registry -> address proof <= 90 days old -> signatory = lead contact and has
authority for the constitution.
Deliberately NOT checked: Udyam certificate date and major activity (they differ from the
registry on every specimen; checking them would reject good applicants).
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from .. import gstin as gst
from ..config import ADDRESS_PROOF_MAX_AGE_DAYS, TODAY
from ..registry import find_udyam_by_name, gstin_exists, lookup_gstin, lookup_udyam
from .parse import ParsedDoc

# Verdicts, most severe first.
REJECT, HOLD, RECAPTURE, AUTO_FIX, PASS = "REJECT", "HOLD", "RECAPTURE", "AUTO_FIX", "PASS"
SEVERITY = [REJECT, HOLD, RECAPTURE, AUTO_FIX, PASS]

NAME_MATCH_MIN = 90  # rapidfuzz ratio on normalised strings; OCR noise scores 95+, edits ~80

# Who may sign for each constitution type.
AUTHORISED = {
    "Proprietorship": None,  # any person the proprietor nominates (matched to the lead contact)
    "Limited Liability Partnership": {"designated partner", "partner"},
    "Partnership": {"partner", "managing partner"},
    "Private Limited Company": {"director", "managing director", "authorised signatory"},
    "Public Limited Company": {"director", "managing director", "authorised signatory"},
}


@dataclass
class Check:
    code: str
    ok: bool
    severity: str           # verdict this check forces when it fails (PASS for info-only)
    detail: str = ""
    action: str = ""


@dataclass
class KycResult:
    verdict: str
    checks: list[Check] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    auto_fixes: list[str] = field(default_factory=list)
    resolved: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "checks": [c.__dict__ for c in self.checks],
            "actions": self.actions,
            "auto_fixes": self.auto_fixes,
            "resolved": self.resolved,
        }


def norm(s: str | None) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower()).strip()


def names_match(a: str | None, b: str | None) -> bool:
    return bool(a and b) and fuzz.ratio(norm(a), norm(b)) >= NAME_MATCH_MIN


def business_part(legal_name: str | None) -> str | None:
    """'Joseph Singh (Prop. Ganesh Woodcraft)' -> 'Ganesh Woodcraft'."""
    m = re.search(r"\(Prop\.?\s*(.*?)\)?$", legal_name or "")
    return m.group(1).strip() if m else legal_name


def proprietor_part(legal_name: str | None) -> str | None:
    m = re.match(r"^(.*?)\s*\(Prop", legal_name or "")
    return m.group(1).strip() if m else None


def validate(docs: dict[str, ParsedDoc], context: dict | None = None) -> KycResult:
    """docs: doc_type -> ParsedDoc. context: what the applicant declared in the journey
    (gstin, udyam_number, contact_name, business_name, state) — usually from the advisor/lead."""
    ctx = context or {}
    checks: list[Check] = []
    fixes: list[str] = []
    resolved: dict = {}

    def add(code, ok, sev, detail="", action=""):
        checks.append(Check(code, ok, sev if not ok else PASS, detail, action if not ok else ""))

    # ---- image quality -------------------------------------------------------------------
    for dtype, d in docs.items():
        if d.blurred:
            add(f"{dtype}.legible", False, RECAPTURE, f"Image too blurred to read (sharpness {d.blur_score:.0f})",
                f"Ask for a sharper photo of the {dtype.replace('_', ' ')} in the chat"
                + (" or prefill from the GSTIN lookup" if dtype == "gst_certificate" else ""))
        if d.deskewed:
            fixes.append(f"{dtype}: deskewed {d.skew_deg:+.1f}° before OCR")

    # ---- GSTIN ----------------------------------------------------------------------------
    gst_doc = docs.get("gst_certificate")
    reg = None
    if gst_doc is None:
        add("gst.present", False, RECAPTURE, "GST certificate not uploaded", "Ask for the GST certificate")
    elif not gst_doc.blurred:
        reads = gst_doc.fields.get("gstin_reads") or []
        best = None
        for r in reads:
            c = gst.correct(r, gstin_exists)
            if c["checksum_ok"] and gstin_exists(c["gstin"]):
                best = c
                break
            best = best or c
        g = best["gstin"] if best else None
        resolved["gstin"] = g
        resolved["gstin_read_method"] = best["method"] if best else None
        if not g or not best["checksum_ok"]:
            declared = ctx.get("gstin")
            detail = f"GSTIN on certificate {g!r} fails the mod-36 checksum"
            if declared and declared != g:
                diff = [f"{a}->{b} at {i + 1}" for i, (a, b) in enumerate(zip(declared, g or ""))
                        if a != b and b not in gst.CONFUSABLE.get(a, "")]  # ignore OCR look-alikes
                detail += f" and differs from the declared/registry GSTIN ({', '.join(diff)})"
            add("gst.checksum", False, REJECT, detail, "Flag possible tampering; verify via lookup + human review")
        else:
            lk = lookup_gstin(g)
            if not lk["found"]:
                add("gst.registry", False, REJECT, "GSTIN not found in the GST registry", "Human review")
            else:
                reg = lk["record"]
                resolved["gst_status"] = lk["status"]
                add("gst.status", lk["active"], REJECT, f"GSTIN status in registry: {lk['status']}",
                    "Block GSTIN-only products; offer the non-GST bundle path; route to human")
                if ctx.get("gstin") and ctx["gstin"] != g:
                    add("gst.matches_declared", False, REJECT, "GSTIN on certificate differs from the one declared",
                        "Human review")
                legal = gst_doc.fields.get("legal_name")
                add("gst.legal_name", names_match(legal, reg["legal_name"]), REJECT,
                    f"Certificate legal name {legal!r} vs registry {reg['legal_name']!r}",
                    "Flag possible edited document; human review")

    # ---- Udyam ----------------------------------------------------------------------------
    business = (reg or {}).get("trade_name") or ctx.get("business_name")
    state = (reg or {}).get("state") or ctx.get("state")
    ud_doc = docs.get("udyam_certificate")
    if ud_doc is None:
        num = ctx.get("udyam_number")
        cands = [lookup_udyam(num)["record"]] if num and lookup_udyam(num)["found"] else find_udyam_by_name(business, state)
        if len(cands) == 1:
            resolved["udyam_number"] = cands[0]["udyam_number"]
            fixes.append("udyam_certificate: not uploaded; auto-filled from the Udyam registry lookup")
            add("udyam.present", True, PASS, "Auto-filled from registry")
        else:
            add("udyam.present", False, RECAPTURE, "Udyam certificate not uploaded and no unique registry match",
                "Ask for the Udyam number in the chat")
    elif not ud_doc.blurred:
        num = ud_doc.fields.get("udyam_number")
        if ud_doc.fields.get("udyam_number_blank") or not num:
            add("udyam.number", False, REJECT, "Udyam certificate has a blank registration number",
                "Treat certificate as invalid; offer the PAN path; route to human")
        else:
            lk = lookup_udyam(num)
            resolved["udyam_number"] = num
            add("udyam.registry", lk["found"], REJECT, "Udyam number " + ("found" if lk["found"] else "not found") + " in registry",
                "Human review")
            if lk["found"]:
                add("udyam.name", names_match(ud_doc.fields.get("enterprise_name"), lk["record"]["enterprise_name"]),
                    REJECT, f"Enterprise name vs registry {lk['record']['enterprise_name']!r}", "Human review")

    # ---- cross-document names -------------------------------------------------------------
    if business:
        for dtype, key in (("address_proof", "billed_to"), ("signatory_id", "business")):
            d = docs.get(dtype)
            if d and not d.blurred and d.fields.get(key):
                add(f"{dtype}.business_name", names_match(d.fields[key], business), REJECT,
                    f"{d.fields[key]!r} vs {business!r}", "Human review")

    # ---- address proof age ----------------------------------------------------------------
    ap = docs.get("address_proof")
    if ap is None:
        add("address_proof.present", False, RECAPTURE, "Address proof not uploaded", "Ask for a recent utility bill")
    elif not ap.blurred:
        bd = ap.fields.get("bill_date")
        if not bd:
            add("address_proof.date", False, RECAPTURE, "Bill date unreadable", "Ask for a clearer photo of the bill")
        else:
            age = (TODAY - dt.date.fromisoformat(bd)).days
            resolved["bill_age_days"] = age
            add("address_proof.age", age <= ADDRESS_PROOF_MAX_AGE_DAYS, RECAPTURE,
                f"Bill dated {bd} is {age} days old (limit {ADDRESS_PROOF_MAX_AGE_DAYS})",
                "Request a bill from the last 90 days")

    # ---- signatory ------------------------------------------------------------------------
    sig = docs.get("signatory_id")
    if sig is None:
        add("signatory.present", False, RECAPTURE, "Signatory ID not uploaded", "Ask for the signatory ID")
    elif not sig.blurred:
        sname, desig = sig.fields.get("name"), (sig.fields.get("designation") or "")
        contact = ctx.get("contact_name")
        proprietor = proprietor_part((reg or {}).get("legal_name"))
        if contact:
            ok = names_match(sname, contact) or names_match(sname, proprietor)
            add("signatory.is_contact", ok, HOLD,
                f"Signatory {sname!r} vs lead contact {contact!r}",
                "Ask for an authorisation letter from an authorised signatory + Aadhaar e-sign")
        const = (reg or {}).get("constitution")
        allowed = AUTHORISED.get(const)
        if allowed is not None:
            ok = desig.strip().lower() in allowed
            # Authority gap alone does not block; it adds an e-sign confirmation step.
            checks.append(Check("signatory.authority", ok, PASS,
                                f"Designation {desig!r} for a {const}",
                                "" if ok else ("Ask for designated-partner confirmation via e-sign" if "Partnership" in const
                                               else "Ask for a board resolution / director authorisation")))

    # ---- verdict --------------------------------------------------------------------------
    worst = PASS
    for c in checks:
        if not c.ok and SEVERITY.index(c.severity) < SEVERITY.index(worst):
            worst = c.severity
    if worst == PASS and fixes:
        worst = AUTO_FIX
    actions = [c.action for c in checks if not c.ok and c.action]
    return KycResult(verdict=worst, checks=checks, actions=actions, auto_fixes=fixes, resolved=resolved)
