"""Turn OCR text into structured fields for each of the four KYC document types."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ocr import OcrResult, read_field

DOC_TYPES = ("gst_certificate", "udyam_certificate", "signatory_id", "address_proof")

DATE_RE = re.compile(r"(20\d{2})\s*-\s*(\d{2})\s*-\s*(\d{2})")
UDYAM_RE = re.compile(r"[A-Z0-9]{3,6}\s*-\s*([A-Z]{2})\s*-\s*(\d{2})\s*-\s*(\d{7})")


@dataclass
class ParsedDoc:
    doc_type: str
    fields: dict = field(default_factory=dict)
    blur_score: float = 0.0
    blurred: bool = False
    deskewed: bool = False
    skew_deg: float = 0.0
    raw_text: str = ""


def detect_type(text: str, filename: str = "") -> str | None:
    t = (text or "").lower()
    for dt in DOC_TYPES:
        if dt in filename.lower():
            return dt
    if "gst registration" in t or "gstin" in t:
        return "gst_certificate"
    if "udyam" in t:
        return "udyam_certificate"
    if "signatory" in t or "designation" in t:
        return "signatory_id"
    if "bill" in t or "consumer no" in t:
        return "address_proof"
    return None


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _after_label(lines: list[str], label: str) -> str | None:
    """Value on the same line after `label` (case-insensitive prefix)."""
    lab = label.lower()
    for ln in lines:
        if ln.lower().startswith(lab):
            return ln[len(label):].strip(" :") or None
    return None


def _next_line(lines: list[str], label: str) -> str | None:
    """Value on the line after a stand-alone label (signatory card layout)."""
    for i, ln in enumerate(lines):
        if ln.strip().lower() == label.lower() and i + 1 < len(lines):
            return lines[i + 1].strip()
    return None


def _date(s: str | None) -> str | None:
    m = DATE_RE.search(s or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def _clean_name(s: str | None) -> str | None:
    if not s:
        return None
    return re.sub(r"[!|]", "", s).strip()


def parse(res: OcrResult, filename: str = "", doc_type: str | None = None) -> ParsedDoc:
    lines = _lines(res.text)
    dt = doc_type or detect_type(res.text, filename)
    p = ParsedDoc(doc_type=dt or "unknown", blur_score=res.blur_score, blurred=res.blurred,
                  deskewed=res.deskewed, skew_deg=res.skew_deg, raw_text=res.text)
    if res.blurred:
        return p  # nothing reliable to extract; the validator asks for a re-capture
    f = p.fields
    if dt == "gst_certificate":
        reads = [_after_label(lines, "GSTIN")]
        crop = read_field(res, "GSTIN")
        if crop:
            reads.append(crop)
        f["gstin_reads"] = [r for r in reads if r]
        f["legal_name"] = _clean_name(_after_label(lines, "Legal name"))
        # trade-name label is often garbled by the watermark; it is the line after legal name
        for i, ln in enumerate(lines):
            if ln.lower().startswith("legal name") and i + 1 < len(lines):
                parts = lines[i + 1].split(None, 2)
                f["trade_name"] = _clean_name(parts[2]) if len(parts) == 3 else None
        f["constitution"] = _after_label(lines, "Constitution")
    elif dt == "udyam_certificate":
        val = _after_label(lines, "Udyam reg. number")
        m = UDYAM_RE.search((val or "").upper())
        f["udyam_number"] = f"UDYAM-{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None
        f["udyam_number_blank"] = not (val or "").strip()
        f["enterprise_name"] = _clean_name(_after_label(lines, "Enterprise name"))
    elif dt == "signatory_id":
        f["name"] = _clean_name(_next_line(lines, "Name"))
        f["designation"] = _next_line(lines, "Designation")
        f["business"] = _clean_name(_next_line(lines, "For business"))
        f["valid_till"] = _date(_next_line(lines, "Valid till"))
    elif dt == "address_proof":
        f["billed_to"] = _clean_name(_after_label(lines, "Billed to"))
        f["bill_date"] = _date(_after_label(lines, "Bill date"))
    return p
