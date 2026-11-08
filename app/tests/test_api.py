"""End-to-end through the FastAPI app: lookup -> advise -> quote -> consent -> KYC -> order -> tracker."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api import app

client = TestClient(app)


def test_gstin_lookup_is_masked():
    r = client.get("/api/gstin/37IHKXV5167L1ZS").json()
    assert r["found"] and r["status"] == "Cancelled" and not r["active"]
    assert "IHKXV" not in r["record"]["gstin"]
    assert "Neha" not in r["record"]["legal_name"]


def test_gstin_bad_checksum():
    r = client.get("/api/gstin/08YKZXS8189L1ZO").json()
    assert r["format_ok"] and not r["checksum_ok"] and not r["found"]


def test_udyam_lookup():
    r = client.get("/api/udyam/UDYAM-MH-00-9516696").json()
    assert r["found"] and r["record"]["enterprise_name"] == "Ganesh Woodcraft"
    assert r["record"]["udyam_number"].endswith("6696") and "9516696" not in r["record"]["udyam_number"]


def test_full_journey():
    adv = client.post("/api/advise", json={"profile": {"business_type": "Kirana store", "employees": 2,
                                                       "sites": 1, "city": "Lucknow"}, "lang": "en"}).json()
    rec = adv["recommendation"]
    assert rec["totals"]["monthly"] == 2296

    # client tries to tamper with a price: server rebuilds from the catalogue
    rec["items"][0]["unit_price"] = 1
    q = client.post("/api/quote", json={"recommendation": rec, "toggles": {"P23": True}}).json()
    assert q["totals"]["monthly"] == 2296 + 2 * 199

    assert client.post("/api/kyc/consent", json={"agreed": False}).status_code == 400
    cid = client.post("/api/kyc/consent", json={"agreed": True, "lang": "en"}).json()["consent_id"]
    kyc = client.post("/api/kyc/specimen/K03").json()
    assert kyc["verdict"] == "PASS"
    assert "•" in kyc["resolved"]["gstin"]

    o = client.post("/api/orders", json={"quote": q, "business": "Ganesh Woodcraft", "contact_name": "Joseph Singh",
                                         "gstin": "27XUIXG0767D1ZP", "kyc_verdict": kyc["verdict"],
                                         "consent_id": cid}).json()
    assert o["stage_index"] == 1 and o["gstin"].startswith("27") and "XUIXG" not in o["gstin"]
    assert o["contact"] != "Joseph Singh"
    t = client.get(f"/api/orders/{o['id']}").json()
    assert [s["key"] for s in t["stages"]][-1] == "live"
    for _ in range(10):
        t = client.post(f"/api/orders/{o['id']}/advance").json()
    assert t["stage_index"] == 5
    assert client.post(f"/api/kyc/consent/{cid}/withdraw").json()["withdrawn"]
    assert client.get(f"/api/orders/{o['id']}").json()["consent_withdrawn"]


def test_kyc_upload_endpoint():
    from backend.config import KYC_DIR
    cid = client.post("/api/kyc/consent", json={"agreed": True}).json()["consent_id"]
    files = {dt: (f"K11_{dt}.png", (KYC_DIR / f"K11_{dt}.png").read_bytes(), "image/png")
             for dt in ("gst_certificate", "udyam_certificate", "signatory_id", "address_proof")}
    r = client.post("/api/kyc/verify", data={"consent_id": cid, "gstin": "03KGZXT1320R1ZZ"}, files=files).json()
    assert r["verdict"] == "RECAPTURE"


def test_failed_kyc_goes_to_backoffice():
    adv = client.post("/api/advise", json={"profile": {"business_type": "Salon", "employees": 2, "city": "Jaipur"}}).json()
    o = client.post("/api/orders", json={"quote": adv["recommendation"], "business": "Saffron Unisex Salon",
                                         "kyc_verdict": "REJECT"}).json()
    assert o["stage_index"] == 0
    bo = client.get("/api/backoffice").json()
    assert any(h["detail"] == o["id"] for h in bo["handoffs"])
