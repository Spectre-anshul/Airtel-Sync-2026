# Project Udyam Digital — Fact Base & 7-Slide Blueprint

Prepared for the Airtel SYNC 2026 Digital Track (Track A). Every number comes from the case pack (`smb_leads.csv`, the two registries, the product catalogue and 47 KYC images) unless a source is named. The model behind each figure is in **Udyam_Digital_Model.xlsx**.

---

## 0. What changed now that we have the real case

The case PDF answers the open questions we had to infer before.

| Earlier assumption | What the brief actually says | What it means for the deck |
|---|---|---|
| The problem is generic SMB acquisition analytics | Fictional operator **Accel Telecom / Accel Business**. Build a **digital-first acquisition and onboarding journey**: discover bundle → buy → activate, on a phone, in the owner's language | Name the company **Accel** on every slide; Airtel is the host, not the client |
| The deliverable is analysis | **Working prototype** (Advisor, Quote & checkout, Smart KYC, Tracker), architecture, business case of ≤10 slides, privacy note | Our 7 slides are the business case. The prototype is shown on slide 4 with screenshots and a QR code |
| Judges score generically | Judges hold **15 live advisor test scenarios, a KYC answer key and the "signals planted in the leads data"** | We must find the planted signals (Section 1) and get all 12 KYC cases right (Section 2) |
| Five key questions | Q1 segments & bundles · Q2 advisor without a salesperson · Q3 near-instant KYC under DPDP · Q4 field force & partner role · Q5 3–5 metrics with targets | Every question is answered on a named slide (Section 6) |
| Real-world market figures | All case data is synthetic; MSME base given as "6 crore+" | Use external facts only for context and the competitive slide, and keep sources on screen |

---

## 1. Fact base: the planted signals we found (all computed)

### 1.1 Funnel and cost (matches Appendix A1 exactly)
5,000 → 3,406 → 1,974 → 861 → 588 → 368, i.e. **7.4% from lead to activation**. The steepest drop is from needs assessed to quote accepted, where only **44%** pass. Blended CAC is **₹15,053** per activation. On average, activation takes **17.6 days** and the customer makes **3.0 status-chase calls**. The median bundle is **₹6,900 a month** and the mean is ₹12,351.

### 1.2 Signals, ranked by how much they matter

| # | Signal | Evidence | So what |
|---|---|---|---|
| S1 | **GSTIN is the KYC wall** | Conversion is 9.6% with a GSTIN and 2.0% without. The quote → KYC pass rate is **80.6% vs 24.7%**, and KYC takes 6.3 vs 3.5 days. Holding everything else constant (logistic model), a GSTIN has an **odds ratio of 3.85×** | Registry lookup plus a GST-free bundle path for non-GST micro firms. **47% of micro leads have no GSTIN** |
| S2 | **73% of time-to-activate is before installation** | Contact 2.0 + needs 3.0 + quote 4.1 + KYC 3.8 days = 12.8 of 17.6 days. Installation itself takes only 4.8 days | Digitising contact, quote and KYC removes about 12 days. Installation is not the bottleneck |
| S3 | **The quote is the leak** | At the needs → quote stage, 1,113 leads drop: price too high 414, competitor cheaper 207, quote too complex 206, quote too slow 179, decided to wait 107 | An instant, plain-language, single monthly price with add-ons the owner can toggle |
| S4 | **Visits kill deals** | 827 drops at the contact stage: owner had no time for a visit (531) and visit not scheduled by sales (296) | Needs discovery through a conversational advisor, with no visit |
| S5 | **Status chases drive churn and NPS** | Six-month churn by number of chase calls: 5.9% (1), 14.3% (2), 11.7% (3), 20.0% (4), **27.9% (5)**. NPS falls from −3 to −63. NPS when activation took more than 21 days: **−62** | An order tracker that the owner checks instead of calling. Modelled churn falls from 15.2% to **7.6%** at one chase |
| S6 | **Micro is value-destroying today** | Micro is 54% of leads but converts at 4.1%, with CAC ₹20,007, ARPU ₹2,505, churn 22.7% and **LTV/CAC 0.9×** | Micro only works on a digital, low-touch cost base |
| S7 | **Mis-selling and compliance breaches** | 56 of 368 activations (15%) break a catalogue rule. **21** were sold a GSTIN-only product without a valid, active GSTIN, and 24 got 1 Gbps fibre in Tier-2 where it isn't sold. **54%** bought none of the products they asked about | A rules-engine advisor recommends only bundles the customer is eligible for, which matches the brief's point that sales "pitches whatever is on target" |
| S8 | **Lead quality in digital channels** | WhatsApp campaign leads convert at 2.8%: 31.6% unreachable and 12.4% wrong numbers. Website form leads convert at 4.3%. Referral converts best at 14.8% | Verify with OTP or silent authentication at capture, and reply on WhatsApp so the owner can answer when free |
| S9 | **Vernacular gap at the quote** | Regional-language leads (8 languages, 34% of leads) convert at 6.2% vs 8.0% for Hindi/English. Their quote-stage pass is 39.9% vs 45.4%. Tamil 4.3%, Punjabi 4.2%, Kannada 5.1% | The advisor and quote work in 10 languages |
| S10 | **Tier-2 install gap** | KYC → activation is 51.8% in Tier-2 vs 72.7% in Tier-1, and install takes 5.9 vs 4.1 days. Vadodara, Lucknow and Mysuru convert below 5% | Feasibility pre-check with 5G FWA (P04) as the fallback, and an install-slot promise |
| S11 | **Partners are expensive** | Partner cost per activation is **₹900 + 1.5× MRR** (r = 0.99999). Field sales CAC is ₹24,335 per activation | Change the role: partners become local installers and assisted-digital agents, not the full sales cycle |
| S12 | **Propensity works** | A 5-fold cross-validated model (AUC 0.71) puts **53% of activations in the top 30% of leads**; the bottom 30% hold 8% | Back-office call list for the field force (a stretch goal in the brief) |

Checks that came back clean: names, states and cities match the registries exactly for every lead that has an ID; 167 GSTINs are cancelled and 101 suspended; bundle prices and setup fees all match the catalogue; there is no month-to-month trend. The registry joins are trivial, so the **trap in the leads data is the GST status, not name matching**.

---

## 2. Smart KYC answer key: 12 applicants

| Verdict | Applicants | Why |
|---|---|---|
| **Pass** (4) | K03, K08, K09, K12 | Consistent with both registries. K08 needs O/0 normalisation by GSTIN position |
| **Pass after auto-fix** (2) | K02 (skewed scan → deskew), K05 (Udyam certificate not uploaded → auto-filled from registry) | Shows the lookup replacing a document request |
| **Re-capture** (2) | K04 (GST certificate too blurred), K11 (electricity bill **257 days** old against the 90-day rule) | Ask for it again inside the chat |
| **Reject / hold** (4) | K01 (**GSTIN cancelled** and Udyam number blank), K06 (GSTIN on the certificate fails the checksum and differs from the registry, 8↔5), K07 (legal name on the certificate says "Shri Physio Clinic", the registry says "Neelgiri"), K10 ("Owner" designation for an LLP, and the signatory is not the lead contact) | Possible tampering or missing authority, so a human reviews |

The validation rules are: OCR → GSTIN format + mod-36 checksum (with the README's X exception) → registry status → Udyam lookup → fuzzy match of names across documents → address-proof age ≤ 90 days (today = 2026-07-15) → signatory matches the contact and has authority for the constitution type.

---

## 3. Strategic analysis (answers to Q1 and Q4)

### 3.1 Segment priority: where to go first

| Segment | Share of leads | Conv. today | CAC today | ARPU | 6-mo churn | LTV/CAC today → Base | Play |
|---|---|---|---|---|---|---|---|
| **Professional offices** | 25% | 11.1% | ₹10,695 | ₹6,796 | 13.8% | 6.1× → **18.4×** | **Wave 1, fully digital.** Single site, install in 4.4 days, 86% have a GSTIN |
| **Micro retail & services** | 54% | 4.1% | ₹20,007 | ₹2,505 | 22.7% | **0.9× → 5.2×** | **Wave 1, digital only.** Volume play; viable only at CAC < ₹5k. Needs a GST-free path |
| **Small multi-site** | 15% | 11.0% | ₹15,614 | ₹31,233 | 10.8% | 21× → 27× | **Wave 2, assisted-digital.** Advisor qualifies; field rep closes and surveys sites |
| **Small manufacturers** | 6% | 12.8% | ₹15,324 | ₹19,980 | 8.1% | 15× → 22× | **Wave 2, assisted.** Leased line installs take 21–30 days, so a tracker is critical |

LTV assumes a 40% contribution margin and is capped at 36 months. The margin is an assumption; the Sensitivity tab tests 30–50%.

### 3.2 Starter bundles, priced from the catalogue

Prices are catalogue ranges. Each bundle checks every eligibility and dependency rule.

| Bundle | Contents | Price per month | Setup | Contract | Install | GSTIN needed |
|---|---|---|---|---|---|---|
| **Dukaan Starter** (micro) | Biz Fibre 100 + 1 Postpaid 299 + Cloud POS + Secure Wi-Fi | ₹2,296–3,096 | ₹3,500 | 12 mo | 5 days | **No** |
| Dukaan Starter, wireless | 5G AirFiber + 1 Postpaid + Cloud POS | ₹1,797–2,397 | ₹2,500 | 12 mo | 3 days | No |
| **Clinic & Office Pro** | Biz Fibre 300 + 5 Cloud Email + 5 Endpoint + Postpaid 599 + Postpaid 299 + Backup | ₹4,016–5,191 | ₹0 | 12 mo | 5 days | No |
| Multi-site One-Bill (5 sites) | Fibre 300 ×5 + Failover ×5 + Postpaid 599 ×5 + POS ×5 + CCTV ×10 + SD-WAN ×5 | ₹30,470–40,970 | ₹63,000 | 24 mo | 14 days | Yes |
| Factory Connect | ILL 20 + Postpaid 599 ×3 + 10 Email + 10 Endpoint + Firewall + Static IP | ₹14,236–20,686 | ₹14,000 | 24 mo | 21 days | Yes |

These sit close to the medians actually bought (micro ₹2,470; professional ₹6,575; multi-site ₹28,080; manufacturers ₹15,910). WhatsApp API (P15) and Business SMS (P14) need a GSTIN, so they appear as **toggles** that unlock once a GSTIN is verified.

### 3.3 Field force and partners (Q4)
- **Field sales** shrinks to the high-value end: multi-site and manufacturing, plus a daily call list from the propensity score. Today's field CAC is ₹24,335 per activation, and visits cause 827 drops.
- **Channel partners → "Udyam Mitra"**:
  - Their role becomes local installation, a walk-in assisted sign-up on the same app, and document help for the owner.
  - They earn a commission on any activation in their pin-code territory, even if it closed digitally. This prevents channel conflict.
  - The commission moves from 1.5× MRR towards a per-task fee as volume grows. We keep it at 1.5× in the model to stay conservative.
- **Inside sales** handles advisor hand-offs: Amber/Red KYC cases, quotes the advisor could not close, and customers who ask for a human. This is the "back-office view" in the brief.

---

## 4. Competitive brief

Accel is the fictional client; competitors are real-world analogues. Ratings are our read of public sources, so the deck should label them "indicative".

| Capability | Accel today | Jio Business | Vi Business | Tata Tele Business | Local ISP / reseller | Fintech / SaaS (PhonePe Business, Zoho…) | **Udyam Express** |
|---|---|---|---|---|---|---|---|
| One bundle, one bill | ✗ (each product billed separately) | ◐ (fibre + JioMeet/JioAttendance/JioGate bundles) | ◐ | ◐ (SmartOffice) | ✗ | ✗ (no connectivity) | ✓ |
| Self-serve discovery | ✗ (field visit) | ◐ | ◐ (ReadyForNext assessment) | ◐ | ✗ | ✓ (app-native) | ✓ (GenAI advisor) |
| Vernacular | ✗ | ◐ | ◐ | ◐ | ✓ (local, informal) | ◐ | ✓ (10 languages) |
| Instant KYC through registries | ✗ (physical/email) | unverified | unverified | unverified | ✗ | ✓ (PhonePe offers Udyam Assist registration in-app) | ✓ (GSTIN + Udyam + OCR + e-sign) |
| Order tracker | ✗ (3 chase calls) | ◐ | ◐ | ◐ | ✗ | n/a | ✓ |
| Trust and anti-fraud layer | ◐ | ◐ | ◐ | ◐ | ✗ | ◐ | ✓ (tamper checks + network signals such as Airtel's IQ Verify, launched 5 Oct 2026) |
| Physical reach (install, partners) | ✓ | ✓ | ◐ | ◐ | ✓ | ✗ | ✓ (Udyam Mitra) |

**Positioning line:** *Others sell a product online; Accel sets up the whole business, verified and live in under a week, in the owner's language.*

**Threats:**
- Jio's price-led bundles. We answer with right-sized starter packs, not discounts.
- Fintechs owning the relationship with formalising MSMEs. This is also a partnership opportunity: embed "Get your business online" at the Udyam or UPI moment, as roadmap Phase 3.

---

## 5. Impact and economics (answers to Q5)

### 5.1 How the model works
- Each of the 20 drop reasons is mapped to the solution component that fixes it, and given a **recovery rate at full effect**. For example, "quote took too long" recovers 85% with an instant quote; "owner had no time for a visit" recovers 50% with no visit needed; "locked in with current provider" recovers 0%.
- Every recovery rate is then multiplied by a **scenario factor**: 0.3 Conservative, **0.5 Base**, 1.0 Upside.
- We rebuild every segment funnel stage by stage. The new pass rate is (passed + recovered) ÷ entering, and conversion is the product of the five pass rates.
- "Only wanted a mobile plan" is excluded. Wrong numbers are prevented at capture, not counted as recovered.

### 5.2 Results for one quarter of the same 5,000 leads

| Metric | Today | Conservative | **Base** | Upside |
|---|---|---|---|---|
| Lead → activation | 7.4% | 10.8% | **13.8%** | 24.1% |
| Activations | 368 | 541 | **689 (+87%)** | 1,203 |
| CAC per activation | ₹15,053 | ₹8,325 | **₹7,143 (−53%)** | ₹5,237 |
| Micro LTV/CAC | 0.9× | 3.5× | **5.2×** | 9.3× |
| New ARR at this run-rate (×4 quarters) | ₹21.8 cr | ₹30.2 cr | **₹37.0 cr (+₹15.2 cr)** | ₹59.6 cr |
| Days lead → activation | 17.6 | — | **~6 (micro/prof), ~9 (multi/mfg)** | — |
| Six-month churn (activation-weighted) | 15.2% | 11.0% | **~8%** | 7.5% |

**Scale rule of thumb:** at Base, every 1 lakh leads a year adds about **₹185 crore of ARR**. The case gives the MSME base as "6 crore+", so the ceiling is distribution, not demand.

### 5.3 Metrics and targets (Q5)

| North-star metric | Today | 12-month target |
|---|---|---|
| Lead → activation | 7.4% | **≥ 13%** |
| Days lead → activation | 17.6 | **≤ 7** (single site) |
| CAC per activation | ₹15,053 | **≤ ₹7,500** |
| Six-month churn | 15.2% | **≤ 8%** |
| Status chases per customer (guardrail) | 3.0 | **≤ 0.5** |

Two diagnostic metrics sit alongside these: KYC auto-pass rate (target 60%; 6 of 12 specimens pass automatically) and NPS (−25 today, target ≥ 0).

---

## 6. Roadmap and governance (process excellence + implementation planning + governance)

### 6.1 Process redesign (value-stream view)
- **Today:** 5 hand-offs (lead, call, visit, PDF quote, physical KYC, install). 12.8 days of the 17.6 are wait time before installation, and the customer makes 3 status calls.
- **To be:** one WhatsApp or app session covers the advisor, the quote and Smart KYC. Install is booked against a slot, and the tracker pushes updates. A human steps in only for exceptions:
  - Amber/Red KYC cases
  - multi-site site surveys
  - leads the propensity score marks as high value

### 6.2 Phased rollout with stage gates

| Phase | When | Scope | Gate to move on |
|---|---|---|---|
| 0. Prototype hardening | Months 0–2 | Advisor + quote + Smart KYC + tracker; DPDP notice and consent flow; red-team the 15 judge scenarios | 95% of advisor recommendations eligible; KYC answer key 12/12 |
| 1. Pilot | Months 3–5 | Micro + professional offices in **4 test cities** (Delhi and Bengaluru in Tier-1; Lucknow and Vadodara, the lowest-converting Tier-2 cities) **against 4 matched holdout cities**, in Hindi, English, Kannada and Gujarati | Conversion ≥ 1.5× holdout; CAC ≤ ₹9k; no compliance breach |
| 2. Scale | Months 6–12 | All 22 cities and 10 languages; Udyam Mitra partner app; propensity call list for the field force | KPI targets in 5.3 met at city level |
| 3. Extend | Months 12–18 | Assisted-digital for multi-site and manufacturers; voice advisor; embedded journeys with UPI and accounting apps at the Udyam registration moment | DPDP full obligations live by **13 May 2027** |

### 6.3 Governance
- **Steering committee (monthly):**
  - Chair: Head of SMB, Accel Business
  - Members: CDO, CISO/DPO, Head of Channel, Finance BP
  - Decides: stage gates, pricing guardrails
- **Weekly working team:** product, data science, KYC operations, channel.
- **RACI:**
  - The product owner is accountable for journey KPIs.
  - The DPO is accountable for consent and retention.
  - The channel head is accountable for the partner commission policy.
  - Finance is consulted on bundle discounts.

**Top risks:**

| Risk | Mitigation |
|---|---|
| GenAI states a wrong price | Prices come only from the catalogue rules engine; the LLM explains, it never prices. Run the 15 test scenarios every release |
| KYC fraud | Registry and checksum checks, tamper flags, and human review of Red cases; network fraud signals |
| Partner backlash | Pin-code commission protection |
| DPDP | Consent screen, purpose-limited fields, masked IDs in logs, and documents deleted after verification except what DoT licence rules require |
| Tier-2 install delays | Feasibility pre-check with FWA fallback |

---

## 7. The 7-slide blueprint (modelled on BrAINWARS, kept to our storyline)

### 7.1 What we borrow from the BrAINWARS deck
- An **action title** (the insight as a sentence) plus a grey sub-headline.
- **Three or four red-header panels per slide**, each a mini-exhibit: chart, table or icon list.
- A **"so-what" bumper box** at the bottom of each slide.
- **KPI tiles** across the top of the economics slide.
- A **funnel graphic** for selection logic.
- SCQ → solution arrows on the opening slide.
- An **appendix** with methodology, assumptions, model tabs, sensitivity, and a link to the Excel model.

### 7.2 What we fix from it
- Font size never below 10 pt.
- A source line on every exhibit.
- No unexplained claims like "99% predictive accuracy".
- Fewer, larger numbers.
- Use the **SYNC submission template and Airtel red**, not Bain branding.

| # | Action title (draft) | Panels | Bumper (so-what) | Case question answered |
|---|---|---|---|---|
| 1 | **The Leak: only 7 in 100 SMB leads go live, and 73% of the 17.6-day wait happens before anyone installs anything** | SCQ strip (Situation / Complication / Question / Answer) · funnel 5,000 → 368 with stage % · top drop reasons by stage (visits 827, quote 1,113, KYC 273) · KPI tiles: 17.6 days, 3 chases, ₹15k CAC, NPS −25 | "The problem isn't demand; it's a journey built for corporates." | Context |
| 2 | **Root cause: a GSTIN wall, a confusing quote and silent installs; micro customers lose money at LTV/CAC 0.9×** | GSTIN effect (9.6% vs 2.0%; KYC pass 81% vs 25%; OR 3.85×) · segment economics table · status chases vs churn curve (5.9% → 27.9%) · audit: 15% of bundles break catalogue rules, 21 GST breaches, 54% never got what they asked for | "Fix the journey and micro flips from value-destroying to 5× LTV/CAC." | Q1 (evidence) |
| 3 | **The answer: Udyam Express, one phone session from 'what do I need' to 'it's live'** | Journey flow (Advisor → Quote → Smart KYC → Tracker) with the drop reasons each step kills · segment priority (Wave 1 professional + micro; Wave 2 multi-site + manufacturers) · 4 starter bundles with prices · role of the field force and partners (Udyam Mitra) | "Digital for the 79%, assisted-digital for the 21% who are worth a visit." | Q1, Q2, Q4 |
| 4 | **Prototype: the advisor recommends only bundles the customer can legally buy, and Smart KYC catches 6 of 12 bad files** | 4 screenshots (chat in Hindi, toggle quote, KYC consent + verdict, tracker) · architecture strip (WhatsApp/RCS → LLM + rules engine → GSTIN/Udyam mock APIs → OCR → order system) · KYC answer key summary (4 pass, 2 auto-fix, 2 re-capture, 4 reject) · DPDP by design (consent, minimisation, masking, retention) · QR to demo video and repo | "GenAI explains; the rules engine decides." | Q2, Q3 |
| 5 | **Competitive edge: others sell a product online; Accel sets up the whole business, verified, in under a week** | Capability matrix (above) · positioning map (speed to live vs breadth of bundle) · threats and our response · moat: network trust signals + physical install reach + partner pin-code model | "We win on breadth + trust + speed, not price." | Competitive analysis |
| 6 | **Impact: activations up 87%, CAC down 53%, +₹15 cr ARR from the same leads (Base case)** | KPI tiles (13.8% conversion, ₹7.1k CAC, ~6 days, ≤8% churn, +₹15.2 cr ARR) · waterfall of recovered activations by component · segment LTV/CAC before → after · scenario band (Conservative / Base / Upside) + assumptions note | "Even the Conservative case pays: CAC −45%, +47% activations." | Q5, impact |
| 7 | **Roadmap: pilot in 4 cities vs 4 holdouts, scale to 22 cities in 12 months, DPDP-complete before May 2027** | Gantt with stage gates · 5 KPIs with targets · governance (steering, RACI) · risk register (top 5) · "the ask": 4 pilot cities, catalogue + registry API access, partner policy sign-off | "Measured, gated, reversible." | Q5, rollout, risks |

The appendix is outside the 7: methodology and assumptions, the Excel tabs, the KYC answer key, sensitivity, and sources.

---

## 8. Red-team notes

The independent review is in Section 9. Before that, we fixed these issues ourselves:
- Earlier drafts of the impact model gave 3.5× conversion. We haircut it to a 0.5 Base factor, excluded mobile-only drops, and stopped crediting junk numbers as recoveries.
- The NPS forecast relied on extrapolation, so we dropped the projection. We now show the observed cohort gradient and set a target of ≥ 0.
- Registry name matching is trivially clean in this data, so we don't claim the "AI entity resolution" that we argued for earlier.
- External figures are kept to the competitive and context panels, each with a dated source.
