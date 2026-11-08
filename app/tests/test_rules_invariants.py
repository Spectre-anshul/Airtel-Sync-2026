"""Property-style check over many random profiles: the rules engine never puts an ineligible
product in a bundle and never prices anything off-catalogue."""
from __future__ import annotations

import random

import pytest

from backend.data import catalogue, city_tiers, gstin_registry
from backend.rules import NEED_PRODUCTS, Profile, eligibility, recommend

TYPES = ["Kirana store", "Salon", "Dental clinic", "CA firm", "Restaurant chain", "Auto-parts unit",
         "Textile unit", "Pharmacy chain", "Coaching centre", "Budget hotel group", "Bakery"]


def gstins():
    g = gstin_registry()
    out = [None, "27ABCDE1234F1Z5"]   # none, and a checksum-invalid one
    for st in ("Active", "Cancelled", "Suspended"):
        out.append(g[g.status == st].index[0])
    return out


@pytest.mark.parametrize("seed", range(400))
def test_random_profile(seed):
    rnd = random.Random(seed)
    p = Profile(
        business_type=rnd.choice(TYPES), employees=rnd.choice([1, 2, 3, 4, 5, 9, 10, 12, 24, 25, 60]),
        sites=rnd.choice([1, 1, 2, 3, 6]), city=rnd.choice(list(city_tiers())), gstin=rnd.choice(gstins()),
        fibre_available=rnd.random() > 0.2, needs=rnd.sample(list(NEED_PRODUCTS), rnd.randint(0, 5)),
        requested=rnd.sample(list(catalogue().index), rnd.randint(0, 2)),
    )
    rec = recommend(p)
    ctx = rec["context"]
    on = {i["product_id"] for i in rec["items"] if i["on"]}
    # exactly one connectivity core item, and it is eligible
    assert sum(1 for i in rec["items"] if i["role"] == "core" and i["category"] == "Connectivity"
               and i["product_id"] in ("P01", "P02", "P03", "P04", "P05", "P06")) == 1
    for it in rec["items"]:
        assert eligibility(it["product_id"], ctx, on - {it["product_id"]}) == []
        assert it["unit_price"] == int(catalogue().loc[it["product_id"], "price_min_inr_per_month"])
    assert not ({lk["product_id"] for lk in rec["locked"]} & on)
    if not ctx["gst_active"]:
        gst_only = set(catalogue()[catalogue().requires_gstin == "Y"].index)
        assert not (gst_only & on)
    if ctx["tier"] == 2:
        assert "P03" not in on
