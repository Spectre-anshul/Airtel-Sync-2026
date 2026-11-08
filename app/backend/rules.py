"""Rules engine: the ONLY component that chooses products and prices.

Every catalogue eligibility column is enforced:
  available_city_tiers, min_employees, min_sites, requires_gstin (registry status Active only),
  requires_one_of (dependency on a connectivity product in the same bundle).
Prices come only from data/product_catalogue.csv. The quoted unit price is price_min_inr_per_month
(the list ceiling price_max is shown alongside). Quantities follow fixed segment templates.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field

from .data import business_type_segments, catalogue, city_tiers
from .registry import lookup_gstin

SEGMENTS = ("micro", "prof", "multi", "mfg")
BUNDLE_NAMES = {
    "micro": "Dukaan Starter",
    "prof": "Clinic & Office Pro",
    "multi": "Multi-site One-Bill",
    "mfg": "Factory Connect",
}

# Need tags the advisor collects -> catalogue product.
NEED_PRODUCTS = {
    "pos": "P19", "cctv": "P23", "guest_wifi": "P22", "whatsapp": "P15", "sms": "P14",
    "email": "P16", "backup": "P17", "antivirus": "P20", "telephony": "P12", "tollfree": "P13",
    "website": "P18", "failover": "P09", "sdwan": "P10", "machine_iot": "P24", "fleet": "P25",
    "static_ip": "P11", "firewall": "P21", "high_speed": "P03", "leased_line": "P05",
}
CONNECTIVITY = ["P06", "P05", "P03", "P02", "P01", "P04"]   # fastest -> lightest
FIBRE = {"P01", "P02", "P03"}
WIRED = FIBRE | {"P05", "P06"}                             # needs a fibre/leased-line footprint
# Fallback chain when a wanted connectivity product is not allowed.
CONN_FALLBACK = {"P06": ["P05", "P03", "P02"], "P05": ["P03", "P02"], "P03": ["P02"], "P02": ["P01"],
                 "P01": ["P04"], "P04": []}

PROFESSIONAL_WORDS = ("clinic", "dental", "doctor", "ca ", "chartered", "law", "legal", "advocate", "coaching",
                      "tuition", "consult", "diagnostic", "physio", "insurance", "architect", "realty", "office")
MANUFACTURING_WORDS = ("manufactur", "factory", "unit", "plant", "fabricat", "auto-parts", "auto parts",
                       "textile", "machining", "workshop", "printing press")


@dataclass
class Profile:
    business_type: str = ""
    segment: str | None = None          # micro | prof | multi | mfg; inferred when None
    employees: int = 1
    sites: int = 1
    city: str | None = None
    city_tier: int | None = None        # inferred from city when None
    gstin: str | None = None
    fibre_available: bool = True
    needs: list[str] = field(default_factory=list)
    requested: list[str] = field(default_factory=list)   # product ids asked for by name
    mobile_lines: int | None = None
    lang: str = "en"


def infer_segment(p: Profile) -> str:
    if p.segment in SEGMENTS:
        return p.segment
    bt = (p.business_type or "").strip()
    seg = None
    for k, v in business_type_segments().items():
        if k.lower() == bt.lower():
            seg = v
    if seg is None:
        low = f" {bt.lower()} "
        if any(w in low for w in MANUFACTURING_WORDS):
            seg = "mfg"
        elif any(w in low for w in PROFESSIONAL_WORDS):
            seg = "prof"
        else:
            seg = "micro"
    if p.sites >= 2 and seg in ("micro", "prof"):
        seg = "multi"
    return seg


def infer_tier(p: Profile) -> int:
    if p.city_tier in (1, 2):
        return int(p.city_tier)
    return city_tiers().get(p.city or "", 2)    # unknown city -> Tier-2 (the stricter tier)


def product(pid: str) -> dict:
    r = catalogue().loc[pid]
    return {"product_id": pid, **r.to_dict()}


def eligibility(pid: str, ctx: dict, present: set[str]) -> list[dict]:
    """Return the list of failed rules for product `pid` (empty list = eligible)."""
    r = product(pid)
    fails = []
    tiers = {int(t) for t in str(r["available_city_tiers"]).split(";") if t}
    if ctx["tier"] not in tiers:
        fails.append({"rule": "city_tier", "need": sorted(tiers), "have": ctx["tier"]})
    if ctx["employees"] < int(r["min_employees"]):
        fails.append({"rule": "min_employees", "need": int(r["min_employees"]), "have": ctx["employees"]})
    if ctx["sites"] < int(r["min_sites"]):
        fails.append({"rule": "min_sites", "need": int(r["min_sites"]), "have": ctx["sites"]})
    if r["requires_gstin"] == "Y" and not ctx["gst_active"]:
        fails.append({"rule": "requires_gstin", "gst_status": ctx["gst_status"]})
    deps = [d for d in str(r["requires_one_of"]).split("|") if d]
    if deps and not (set(deps) & present):
        fails.append({"rule": "requires_one_of", "need": deps})
    if pid in WIRED and not ctx["fibre_available"]:
        fails.append({"rule": "no_fibre"})
    return fails


def _template(seg: str, p: Profile, sites: int) -> list[tuple[str, int, str]]:
    """(product, qty, role) — role is core | recommended."""
    emp = max(1, p.employees)
    if seg == "micro":
        lines = p.mobile_lines or 1
        return [("P01", sites, "core"), ("P07", lines, "core"), ("P19", sites, "recommended"),
                ("P22", sites, "recommended")]
    if seg == "prof":
        users = min(emp, 50)
        return [("P02", sites, "core"), ("P08", p.mobile_lines or 1, "core"), ("P07", 1, "core"),
                ("P16", users, "recommended"), ("P20", users, "recommended"), ("P17", 1, "recommended")]
    if seg == "multi":
        return [("P02", sites, "core"), ("P08", p.mobile_lines or sites, "core"), ("P09", sites, "recommended"),
                ("P19", sites, "recommended"), ("P23", 2 * sites, "recommended"), ("P10", sites, "recommended")]
    # mfg
    office = min(emp, 10)
    conn = "P06" if (emp >= 25 and ("high_speed" in p.needs or "leased_line" in p.needs)) else "P05"
    return [(conn, sites, "core"), ("P08", p.mobile_lines or 3, "core"), ("P16", office, "recommended"),
            ("P20", office, "recommended"), ("P21", sites, "recommended"), ("P11", 1, "recommended")]


def _qty_for(pid: str, seg: str, p: Profile, sites: int) -> int:
    unit = product(pid)["unit"]
    if unit == "per site":
        return sites
    if unit == "per user":
        return min(max(1, p.employees), 50 if seg == "prof" else 10)
    if unit == "per device":
        return min(max(1, p.employees), 10)
    if unit == "per camera":
        return 2 * sites
    if unit == "per counter":
        return sites
    if unit == "per vehicle":
        return 1
    return 1


def _item(pid: str, qty: int, role: str, on: bool, why: str) -> dict:
    r = product(pid)
    return {
        "product_id": pid, "name": r["product_name"], "category": r["category"], "unit": r["unit"],
        "qty": int(qty), "unit_price": int(r["price_min_inr_per_month"]),
        "unit_price_max": int(r["price_max_inr_per_month"]), "setup_each": int(r["one_time_setup_inr"]),
        "min_contract_months": int(r["min_contract_months"]), "install_days": int(r["typical_install_days"]),
        "role": role, "on": on, "why": why,
    }


def totals(items: list[dict]) -> dict:
    on = [i for i in items if i["on"]]
    return {
        "monthly": sum(i["qty"] * i["unit_price"] for i in on),
        "monthly_max": sum(i["qty"] * i["unit_price_max"] for i in on),
        "setup": sum(i["qty"] * i["setup_each"] for i in on),
        "contract_months": max((i["min_contract_months"] for i in on), default=0),
        "install_days": max((i["install_days"] for i in on), default=0),
    }


def recommend(p: Profile) -> dict:
    seg = infer_segment(p)
    tier = infer_tier(p)
    sites = max(1, p.sites)
    gl = lookup_gstin(p.gstin) if p.gstin else None
    gst_active = bool(gl and gl["found"] and gl["checksum_ok"] and gl["active"])
    gst_status = (gl["status"] if gl and gl["found"] else ("invalid" if gl else "none"))
    ctx = {"tier": tier, "employees": max(1, p.employees), "sites": sites, "gst_active": gst_active,
           "gst_status": gst_status, "fibre_available": p.fibre_available}

    refused: list[dict] = []   # asked for / template item that the rules do not allow
    template = _template(seg, p, sites)

    # 1) connectivity: requested connectivity overrides the template's
    requested_conn = [r for r in p.requested if r in CONNECTIVITY]
    need_conn = [NEED_PRODUCTS[n] for n in p.needs if NEED_PRODUCTS.get(n) in CONNECTIVITY]
    if requested_conn:                      # asked for by name: try exactly that first
        conn = requested_conn[0]
    else:                                   # a need may only upgrade the template's link
        conn = min([template[0][0]] + need_conn, key=CONNECTIVITY.index)
    base = template[0][0]
    if conn != base:   # refused request/upgrade falls back to the segment's own link, never an upsell
        chain = [conn, base] + CONN_FALLBACK.get(base, [])
    else:
        chain = [conn] + CONN_FALLBACK.get(conn, [])
    if not p.fibre_available:
        chain += ["P04"]
    chosen = None
    for c in chain:
        f = eligibility(c, ctx, set())
        if not f:
            chosen = c
            break
        if c == conn:
            refused.append({"product_id": c, "name": product(c)["product_name"], "reasons": f})
    if chosen is None:
        chosen = "P04"
    if refused:
        refused[-1]["substitute"] = chosen
    items = [_item(chosen, sites, "core", True, "connectivity")]
    present = {chosen}

    # 2) rest of the template
    for pid, qty, role in template[1:]:
        f = eligibility(pid, ctx, present)
        if f:
            refused.append({"product_id": pid, "name": product(pid)["product_name"], "reasons": f, "template": True})
            continue
        items.append(_item(pid, qty, role, True, "segment_template"))
        present.add(pid)

    # 3) needs + explicit requests (non-connectivity) -> recommended add-ons, switched on
    asked = [NEED_PRODUCTS[n] for n in p.needs if n in NEED_PRODUCTS] + list(p.requested)
    for pid in dict.fromkeys(asked):
        if pid in present or pid in CONNECTIVITY or pid not in catalogue().index:
            continue
        f = eligibility(pid, ctx, present)
        if f:
            prior = next((r for r in refused if r["product_id"] == pid), None)
            if prior:
                prior["asked"] = True       # owner asked for it: the explanation must say why not
            else:
                refused.append({"product_id": pid, "name": product(pid)["product_name"], "reasons": f, "asked": True})
            continue
        items.append(_item(pid, _qty_for(pid, seg, p, sites), "recommended", True, "asked"))
        present.add(pid)

    # 4) optional add-ons for this segment (off by default) and locked ones (not eligible)
    locked: list[dict] = []
    for pid, r in catalogue().iterrows():
        if pid in present or pid in CONNECTIVITY or seg not in str(r["target_segments"]).split(";"):
            continue
        if any(x["product_id"] == pid for x in refused):
            continue
        f = eligibility(pid, ctx, present)
        if f:
            locked.append({"product_id": pid, "name": r["product_name"], "reasons": f})
        else:
            items.append(_item(pid, _qty_for(pid, seg, p, sites), "optional", False, "segment_addon"))

    name = BUNDLE_NAMES[seg] + (" (wireless)" if chosen == "P04" else "")
    return {
        "bundle_name": name,
        "segment": seg,
        "context": {**ctx, "city": p.city, "business_type": p.business_type, "gstin_checked": bool(p.gstin)},
        "items": items,
        "refused": refused,
        "locked": locked,
        "totals": totals(items),
        "pricing_rule": "unit price = catalogue price_min_inr_per_month; quantities from segment template",
    }


def apply_toggles(rec: dict, toggles: dict[str, bool]) -> dict:
    """Quote step: switch add-ons on/off. Core items cannot be switched off; locked items cannot be
    switched on; every switched-on item is re-checked against the rules."""
    out = copy.deepcopy(rec)
    ctx = out["context"]
    errors = []
    for it in out["items"]:
        pid = it["product_id"]
        if pid in toggles:
            if it["role"] == "core" and not toggles[pid]:
                errors.append({"product_id": pid, "error": "core_item"})
                continue
            it["on"] = bool(toggles[pid])
    for pid, v in toggles.items():
        if v and any(lk["product_id"] == pid for lk in out["locked"] + out["refused"]):
            errors.append({"product_id": pid, "error": "not_eligible"})
        if not any(i["product_id"] == pid for i in out["items"]) and not any(
                lk["product_id"] == pid for lk in out["locked"] + out["refused"]):
            errors.append({"product_id": pid, "error": "unknown_item"})
    # re-validate the switched-on set (defence in depth)
    present = {i["product_id"] for i in out["items"] if i["on"]}
    for it in out["items"]:
        if it["on"] and eligibility(it["product_id"], ctx, present - {it["product_id"]}):
            it["on"] = False
            errors.append({"product_id": it["product_id"], "error": "revalidation_failed"})
    out["totals"] = totals(out["items"])
    out["toggle_errors"] = errors
    return out


def profile_from_dict(d: dict) -> Profile:
    fields = Profile.__dataclass_fields__
    return Profile(**{k: v for k, v in d.items() if k in fields})


def profile_to_dict(p: Profile) -> dict:
    return asdict(p)
