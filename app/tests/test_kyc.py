"""Smart KYC against the 'KYC Answer Key' sheet in model/Udyam_Digital_Model.xlsx (12 applicants)."""
from __future__ import annotations

import pytest

from backend import gstin as gst
from backend.kyc.ocr import pytesseract
from backend.kyc.service import verify_specimen
from backend.privacy import mask_gstin, mask_udyam, scrub
from backend.registry import gstin_exists

try:
    pytesseract.get_tesseract_version()
    HAVE_TESS = True
except Exception:
    HAVE_TESS = False

# verdict, failing check that must be present (None = none), auto-fix keyword, authority flag expected
ANSWER_KEY = {
    "K01": ("REJECT", ["gst.status", "udyam.number"], None, False),
    "K02": ("AUTO_FIX", [], "deskewed", False),
    "K03": ("PASS", [], None, False),
    "K04": ("RECAPTURE", ["gst_certificate.legible"], None, False),
    "K05": ("AUTO_FIX", [], "auto-filled", True),
    "K06": ("REJECT", ["gst.checksum"], None, False),
    "K07": ("REJECT", ["gst.legal_name"], None, False),
    "K08": ("PASS", [], None, False),
    "K09": ("PASS", [], None, False),
    "K10": ("HOLD", ["signatory.is_contact"], None, True),
    "K11": ("RECAPTURE", ["address_proof.age"], None, True),
    "K12": ("PASS", [], None, False),
}


@pytest.mark.skipif(not HAVE_TESS, reason="tesseract not installed")
@pytest.mark.parametrize("applicant", sorted(ANSWER_KEY))
def test_answer_key(applicant):
    verdict, must_fail, fix, authority = ANSWER_KEY[applicant]
    r = verify_specimen(applicant)
    failed = {c.code for c in r.checks if not c.ok}
    assert r.verdict == verdict, (r.verdict, failed)
    for code in must_fail:
        assert code in failed
    if fix:
        assert any(fix in f for f in r.auto_fixes)
    assert ("signatory.authority" in failed) == authority


@pytest.mark.skipif(not HAVE_TESS, reason="tesseract not installed")
def test_summary_counts():
    counts = {}
    for k in ANSWER_KEY:
        v = verify_specimen(k).verdict
        counts[v] = counts.get(v, 0) + 1
    assert counts == {"PASS": 4, "AUTO_FIX": 2, "RECAPTURE": 2, "REJECT": 3, "HOLD": 1}


def test_k11_bill_age_is_257_days():
    r = verify_specimen("K11") if HAVE_TESS else None
    if r:
        assert r.resolved["bill_age_days"] == 257


def test_checksum_and_x_exception():
    assert gst.is_valid("27XUIXG0767D1ZP")          # 'X' at PAN position 4 accepted
    assert not gst.is_valid("08YKZXS8189L1ZO")      # K06 tampered digit
    assert gst.is_valid("08YKZXS5189L1ZO")


def test_ocr_correction_never_fixes_a_real_alteration():
    c = gst.correct("08YKZXS8189L1ZO", gstin_exists)
    assert c["method"] == "unresolved" and not c["checksum_ok"]


def test_position_normalisation_k08():
    assert gst.correct("24X0RXG9365M1Z3", gstin_exists)["gstin"] == "24XORXG9365M1Z3"


def test_masking():
    assert mask_gstin("27XUIXG0767D1ZP") == "27•••••••••D1ZP"
    assert mask_udyam("UDYAM-MH-00-9516696") == "UDYAM-MH-00-•••6696"
    s = scrub("lead 27XUIXG0767D1ZP UDYAM-MH-00-9516696 call 9876543210")
    assert "27XUIXG0767D1ZP" not in s and "9516696" not in s and "9876543210" not in s
