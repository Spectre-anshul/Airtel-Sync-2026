# Udyam Express — prototype

Accel Business digital journey for small businesses: **Advisor → Quote → Smart KYC → Tracker**, in English and Hindi.
Built for Airtel SYNC 2026, Digital Track A (fictional client: Accel Telecom). All data is synthetic.

## Run

```bash
# once
python -m venv .venv
.venv/Scripts/pip install -r app/requirements.txt      # plus Tesseract OCR 5.x on PATH (or set TESSERACT_CMD)

# terminal 1 — API (http://127.0.0.1:8000/docs)
.venv/Scripts/python -m uvicorn backend.api:app --port 8000 --app-dir app

# terminal 2 — UI (http://localhost:8501)
.venv/Scripts/python -m streamlit run app/frontend/app.py

# tests (from app/)
../.venv/Scripts/python -m pytest -q
```

Optional: set `ADVISOR_MODEL` (the model id) and `ANTHROPIC_API_KEY` to let an LLM write the bundle explanation.
Without them, the advisor uses its own bilingual template. Either way, the rules engine
picks the bundle and sets the price.

## Architecture

```
Streamlit UI (EN/हिं)  ──HTTP──▶  FastAPI (backend/api.py)
                                   ├─ registry.py   mock GSTIN / Udyam lookups  ◀── data/mock_*_registry.csv
                                   ├─ rules.py      eligibility + bundle choice ◀── data/product_catalogue.csv
                                   ├─ advisor.py    free-text slots, LLM explainer + grounding guard
                                   ├─ kyc/          OCR (tesseract + deskew + blur) → parse → validate
                                   ├─ orders.py     SQLite orders, consent log, tracker, back-office hand-offs
                                   └─ privacy.py    masking of GSTIN / Udyam / phone / names in UI + logs
```

### Rules engine (`backend/rules.py`)
- Enforces every catalogue column: `available_city_tiers`, `min_employees`, `min_sites`,
  `requires_gstin` (the registry status must be **Active**; Cancelled, Suspended or a failed checksum count as none),
  and `requires_one_of`.
- Unit price = `price_min_inr_per_month`, with `price_max` shown as the list ceiling. Quantities come from segment
  templates: Dukaan Starter, Clinic & Office Pro, Multi-site One-Bill, Factory Connect.
- When a requested product is refused, the engine falls back to the segment's own connectivity product, never an upsell.
- Toggling on the quote page is re-validated on the server. Core items can't be switched off, and locked items
  can't be switched on. The quote endpoint rebuilds prices from the catalogue and ignores any prices the client sends.

### Advisor guard (`backend/advisor.py`)
The LLM receives only the chosen bundle as JSON. Its reply is rejected, and the template is used instead, if it
contains any number, product name or product code that isn't in those facts, or any percentage.

### Smart KYC (`backend/kyc/`)
Steps, in order:
1. Watermark removed (red channel) and image deskewed (projection profile).
2. Blur score (Laplacian variance) → re-capture if the image is too blurred to read.
3. Tesseract OCR.
4. GSTIN position-class normalisation (O/0, I/1 and so on). If the checksum still fails, the GSTIN is accepted only
   when a single swap of a known OCR look-alike character makes it **checksum-valid AND present in the registry**.
   A genuinely altered digit (K06: 5→8) is not a look-alike pair, so it is never "fixed".
5. Registry status → Udyam lookup (auto-filled when the certificate is missing).
6. Fuzzy name match → bill no more than 90 days old (today = 2026-07-15) → signatory is the lead contact, with
   authority for the constitution type.

Result on the 12 specimens: 4 PASS, 2 AUTO_FIX, 2 RECAPTURE, 3 REJECT + 1 HOLD. This matches the KYC Answer
Key sheet in `model/Udyam_Digital_Model.xlsx` exactly (`tests/test_kyc.py`).

### Privacy (DPDP)
- A consent screen comes before any upload, and every consent is logged with its purpose and fields.
- Consent can be withdrawn from the tracker.
- Uploaded images are processed in memory and never written to disk.
- GSTIN, Udyam number, people's names and phone numbers are masked in API responses, the UI and logs
  (`privacy.MaskingFilter`).

## Tests
- `tests/advisor_scenarios.yaml`: our **15 advisor scenarios**. Each expected price is worked out by hand from the catalogue.
- `tests/test_advisor_scenarios.py`: the scenarios themselves. For every scenario it also checks that each item is
  eligible and priced from the catalogue, that the template explanation passes the guard, that a faithful LLM reply
  is accepted and a lying one rejected, and that an LLM outage falls back to the template.
- `tests/test_rules_invariants.py`: 400 random profiles; no ineligible item and no off-catalogue price, ever.
- `tests/test_kyc.py`: the 12/12 answer key, checksum, OCR correction and masking.
- `tests/test_api.py`: the full journey through FastAPI, including client-side price tampering.
- `tests/test_frontend.py`: Streamlit `AppTest`, re-pricing on toggle and Hindi labels (needs the API running).

## Notes and deviations
- **Factory Connect has no Static IP.** The blueprint's Factory Connect pairs Static IP (P11) with a leased line,
  but the catalogue says P11 `requires_one_of` P01|P02|P03 (fibre only). The engine follows the catalogue and
  explains the refusal.
- The "Owner" designation on an LLP or Pvt Ltd (K05, K10, K11) adds an authority-confirmation step (e-sign or board
  resolution). It does not change the verdict on its own, as the answer key specifies.
- `scripts/` holds developer helpers: `kyc_run.py` prints all 12 verdicts, `show_scenarios.py` prints the advisor text,
  and `ocr_dump.py` and `field_dump.py` print raw OCR.
