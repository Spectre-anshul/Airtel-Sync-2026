# "The journey on a phone": screenshots and values for the slide

Screenshots are 390×844 phone viewport at 3× density (1170×2532 px), captured from the running prototype.
Regenerate them with `app/scripts/screenshots.py hi|en` while the API (port 8000) and UI (port 8501) are running.
Every value below is taken from the prototype's output, which comes from `data/product_catalogue.csv` and the KYC specimens.
The prices in the design mock-up (₹1,198, 5G AirFiber, Cloud POS +₹499) are not in the catalogue. Don't use them.

Demo run: kirana store, Lucknow (Tier 2), 4 staff, 1 site, no GSTIN. Hindi input: "लखनऊ में किराना दुकान है, 4 लोग काम करते हैं".

| Phone | Use file | Replacement text for the card |
|---|---|---|
| **Advisor** | `hi_1_advisor.png` (question) or `hi_1b_advisor_reply.png` (answer) | नमस्ते! अपने बिज़नेस के बारे में बताइए… › 4 people › 1 site, Tier 2 (Lucknow) › GSTIN: none → **Dukaan Starter** |
| **Quote** | `hi_2_quote.png` / `en_2_quote.png` | Dukaan Starter **₹2,296 / month** · setup ₹3,500 · 12-month contract · ✅ Biz Fibre 100 ₹999 · ✅ Business Postpaid 299 ₹299 · ☑ Cloud POS & Billing ₹599 · ☑ Secure Wi-Fi ₹399 · ☐ Website ₹299 · ☐ Cloud CCTV ×2 ₹398 |
| **Smart KYC** | `hi_3a_consent.png` (consent) then `en_3c_kyc_checks.png` (result) | Consent: data used only to verify your business (DPDP Act 2023) · GSTIN ✓ Active · Udyam ✓ found · Address ✓ 46 days old (limit 90) · **Verified ✓** |
| **Tracker** | `hi_4_tracker.png` / `en_4_tracker.png` | ✓ Order placed 15 Jul · ✓ KYC verified 15 Jul · ✓ Slot booked 16 Jul · ● Engineer assigned 18 Jul · ○ Installed Mon 20 Jul · ○ Live Tue 21 Jul · No calls needed |

## Bottom bar
- **Advisor test scenarios: 15 / 15 passed.** (`app/tests/test_advisor_scenarios.py`. The full suite is 503 passed; the 15 skipped tests are the live-LLM runs, which need an API key.)
- Optional second stat: **Smart KYC: 12 / 12 match the answer key** (4 pass, 2 auto-fix, 2 re-capture, 4 reject/hold).
- **Repo:** https://github.com/Spectre-anshul/Airtel-Sync-2026 (use this for the QR code). Demo video: not recorded yet.

## Notes
- The KYC demo uses specimen K03 (Ganesh Woodcraft), so the tracker shows that business name next to the kirana bundle. On a slide this looks like one customer's journey, so leave the name out of any card text you retype.
- "Verified in 2 min" from the mock-up isn't measured anywhere. Don't use it unless we time it.
- The dates are the tracker's planned dates, counted from the model's "today" (Wed 15 Jul 2026). The quote shows a typical installation time of 5 days.
