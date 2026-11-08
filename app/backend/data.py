"""CSV-backed reference data. Loaded once, read-only."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from .config import DATA_DIR


@lru_cache
def gstin_registry() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "mock_gstin_registry.csv", dtype=str).set_index("gstin")


@lru_cache
def udyam_registry() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "mock_udyam_registry.csv", dtype=str).set_index("udyam_number")


@lru_cache
def catalogue() -> pd.DataFrame:
    return pd.read_csv(
        DATA_DIR / "product_catalogue.csv",
        dtype={"available_city_tiers": str, "requires_one_of": str, "target_segments": str},
        keep_default_na=False,
    ).set_index("product_id")


@lru_cache
def leads() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "smb_leads.csv", dtype=str, keep_default_na=False)


@lru_cache
def city_tiers() -> dict[str, int]:
    df = leads()[["city", "city_tier"]].drop_duplicates()
    return {r.city: int(r.city_tier) for r in df.itertuples()}


SEGMENT_CODES = {
    "Micro retail & services": "micro",
    "Professional offices": "prof",
    "Small multi-site businesses": "multi",
    "Small manufacturers": "mfg",
}


@lru_cache
def business_type_segments() -> dict[str, str]:
    """Most common segment for each business_type in the leads file -> segment code."""
    df = leads()
    return {bt: SEGMENT_CODES[g["segment"].mode().iloc[0]] for bt, g in df.groupby("business_type")}
