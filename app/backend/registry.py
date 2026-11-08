"""Mock GSTIN / Udyam lookups backed by data/*.csv."""
from __future__ import annotations

import re

from . import gstin as gst
from .data import gstin_registry, udyam_registry

UDYAM_FMT = re.compile(r"UDYAM-[A-Z]{2}-\d{2}-\d{7}")


def gstin_exists(g: str) -> bool:
    return g in gstin_registry().index


def lookup_gstin(g: str) -> dict:
    g = (g or "").strip().upper()
    v = gst.validate(g)
    out = {"query": g, **v, "found": False, "record": None, "active": False, "status": None}
    if g in gstin_registry().index:
        rec = gstin_registry().loc[g].to_dict()
        out.update(found=True, record={"gstin": g, **rec}, active=rec["status"] == "Active", status=rec["status"])
    return out


def lookup_udyam(u: str) -> dict:
    u = (u or "").strip().upper()
    out = {"query": u, "format_ok": bool(UDYAM_FMT.fullmatch(u)), "found": False, "record": None}
    if u in udyam_registry().index:
        out.update(found=True, record={"udyam_number": u, **udyam_registry().loc[u].to_dict()})
    return out


def find_udyam_by_name(name: str, state: str | None = None) -> list[dict]:
    df = udyam_registry()
    m = df[df["enterprise_name"].str.lower() == (name or "").strip().lower()]
    if state:
        m = m[m["state"] == state]
    return [{"udyam_number": k, **r} for k, r in m.to_dict("index").items()]


def gst_active(g: str | None) -> bool:
    """Eligibility helper: only a registry-listed, checksum-valid, Active GSTIN counts."""
    if not g:
        return False
    r = lookup_gstin(g)
    return bool(r["found"] and r["checksum_ok"] and r["active"])
