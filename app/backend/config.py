"""Paths and fixed settings for the prototype."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent          # app/
PROJECT_DIR = APP_DIR.parent                              # udyam-digital/
DATA_DIR = PROJECT_DIR / "data"
KYC_DIR = PROJECT_DIR / "kyc_documents"
RUNTIME_DIR = APP_DIR / "runtime"                         # sqlite + consent log (gitignored)
RUNTIME_DIR.mkdir(exist_ok=True)

# "Today" for every date rule in the case brief.
TODAY = dt.date(2026, 7, 15)
ADDRESS_PROOF_MAX_AGE_DAYS = 90

ADVISOR_MODEL = os.environ.get("ADVISOR_MODEL", "")   # LLM explanations are off unless a model is set
