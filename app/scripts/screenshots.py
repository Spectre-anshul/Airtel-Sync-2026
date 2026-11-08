"""Phone-size screenshots of the 4-step journey for the deck (needs api :8000 and web :8501 running).

    ../.venv/Scripts/python scripts/screenshots.py [en|hi]
Writes deck/screenshots/<lang>_<n>_<step>.png at 390x844 CSS px, 3x density.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

LANG = sys.argv[1] if len(sys.argv) > 1 else "hi"
OUT = Path(__file__).resolve().parents[2] / "deck" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
HI = LANG == "hi"
TXT = {
    "lang": "हिन्दी" if HI else "English",
    "free": "लखनऊ में किराना दुकान है, 4 लोग काम करते हैं" if HI else "Kirana store in Lucknow, 4 people work here",
    "recommend": "मेरा बंडल सुझाएँ" if HI else "Recommend my bundle",
    "to_quote": "मेरा कोटेशन देखें" if HI else "See my quote",
    "checkout": "KYC पर जाएँ" if HI else "continue to KYC",
    "consent_check": "सहमत हूँ" if HI else "I agree to this use",
    "consent_btn": "सहमति दें" if HI else "Give consent",
    "specimen_tab": "डेमो" if HI else "Demo: load specimen",
    "order": "ऑर्डर करें" if HI else "Place order",
    "advance": "अगले चरण" if HI else "advance to next step",
}
SPECIMEN = "K03"


def settle(page, ms=1500):
    page.wait_for_timeout(ms)


def shot(page, name, scroll_to=None):
    """Scroll so the target (default: the divider under the app header) sits at the top, then capture."""
    target = page.get_by_text(scroll_to).first if scroll_to else page.locator("hr").first
    target.evaluate("e => e.scrollIntoView({block: 'start'})")
    page.wait_for_timeout(600)
    path = OUT / f"{LANG}_{name}.png"
    page.screenshot(path=str(path))
    print("saved", path)


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge")
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True,
                              has_touch=True, color_scheme="light")
    page = ctx.new_page()
    page.goto("http://localhost:8501", wait_until="networkidle")
    page.get_by_text("Namaste!").first.wait_for(timeout=60000)
    page.add_style_tag(content="[data-testid=stToolbar],[data-testid=stDecoration],header{display:none!important}")

    if HI:
        page.get_by_text(TXT["lang"], exact=True).first.click()
        settle(page)

    # 1 · Advisor
    page.locator("textarea").first.fill(TXT["free"])
    page.locator("input[type=number]").first.fill("4")
    page.get_by_role("button", name=TXT["recommend"]).click()
    page.get_by_role("button", name=TXT["to_quote"]).wait_for(timeout=60000)
    settle(page)
    shot(page, "1_advisor")
    shot(page, "1b_advisor_reply", scroll_to=TXT["to_quote"])

    # 2 · Quote
    page.get_by_role("button", name=TXT["to_quote"]).click()
    page.get_by_role("button", name=TXT["checkout"]).wait_for(timeout=60000)
    settle(page)
    shot(page, "2_quote")

    # 3 · Smart KYC: consent, then a specimen run
    page.get_by_role("button", name=TXT["checkout"]).click()
    page.get_by_text(TXT["consent_check"]).first.wait_for(timeout=60000)
    settle(page)
    shot(page, "3a_consent", scroll_to="DPDP")
    page.get_by_text(TXT["consent_check"]).first.click()
    settle(page, 800)
    page.get_by_role("button", name=TXT["consent_btn"]).click()
    page.get_by_role("tab", name=TXT["specimen_tab"]).wait_for(timeout=60000)
    page.get_by_role("tab", name=TXT["specimen_tab"]).click()
    settle(page, 800)
    page.locator("[data-testid=stSelectbox]").last.click()
    page.get_by_role("option", name=SPECIMEN).click()
    settle(page, 800)
    page.get_by_role("button", name="Run Smart KYC on " + SPECIMEN).click()
    page.get_by_role("button", name=TXT["order"]).wait_for(timeout=120000)
    settle(page)
    shot(page, "3b_kyc_result", scroll_to="Run Smart KYC on " + SPECIMEN)
    shot(page, "3c_kyc_checks", scroll_to="gst.status")

    # 4 · Tracker: place order, advance to "engineer assigned"
    page.get_by_role("button", name=TXT["order"]).click()
    page.get_by_role("button", name=TXT["advance"]).wait_for(timeout=60000)
    settle(page)
    for _ in range(2):   # -> slot booked -> engineer assigned
        before = page.locator(".stage b").inner_text()
        page.get_by_role("button", name=TXT["advance"]).click()
        page.wait_for_function("b => document.querySelector('.stage b')?.innerText !== b", arg=before,
                               timeout=30000)
        settle(page)
    shot(page, "4_tracker")
    browser.close()
