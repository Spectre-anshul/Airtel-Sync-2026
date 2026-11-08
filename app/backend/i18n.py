"""English / Hindi strings shared by the advisor (explanations) and the Streamlit UI."""
from __future__ import annotations

LANGS = {"en": "English", "hi": "हिन्दी"}

T: dict[str, dict[str, str]] = {
    # ---- advisor explanation -------------------------------------------------------------
    "intro": {
        "en": "For your {business} ({employees} staff, {sites} site{s_plural}, {city}) we recommend the **{bundle}** bundle.",
        "hi": "आपके {business} ({employees} कर्मचारी, {sites} जगह, {city}) के लिए हम **{bundle}** बंडल सुझाते हैं।",
    },
    "item_line": {
        "en": "- {qty} × {name}: {why}",
        "hi": "- {qty} × {name}: {why}",
    },
    "total": {
        "en": "One monthly bill: **₹{monthly}/month** (list price up to ₹{monthly_max}), one-time setup ₹{setup}, {contract}-month contract. Typical installation: {days} days.",
        "hi": "एक ही मासिक बिल: **₹{monthly}/महीना** (सूची मूल्य ₹{monthly_max} तक), एक बार का सेटअप ₹{setup}, {contract} महीने का अनुबंध। सामान्य इंस्टॉलेशन: {days} दिन।",
    },
    "refused_header": {"en": "Not included, and why:", "hi": "शामिल नहीं, और क्यों:"},
    "locked_header": {
        "en": "Unlocks later: {names} (need an active GSTIN).",
        "hi": "बाद में मिल सकते हैं: {names} (सक्रिय GSTIN ज़रूरी)।",
    },
    "toggle_hint": {
        "en": "You can switch the optional add-ons on or off on the quote page; the price updates instantly.",
        "hi": "कोटेशन पेज पर आप अतिरिक्त सेवाएँ चालू या बंद कर सकते हैं; कीमत तुरंत बदलती है।",
    },
    "fixed_price": {
        "en": "Prices come straight from the Accel catalogue, so the advisor cannot change them or offer discounts.",
        "hi": "कीमतें सीधे Accel कैटलॉग से आती हैं, इसलिए सलाहकार इन्हें बदल नहीं सकता या छूट नहीं दे सकता।",
    },
    # refusal reasons
    "r_city_tier": {"en": "{name} is only sold in Tier-{need} cities; {city} is Tier-{have}.",
                    "hi": "{name} सिर्फ़ Tier-{need} शहरों में मिलता है; {city} Tier-{have} है।"},
    "r_min_employees": {"en": "{name} needs at least {need} staff; you have {have}.",
                        "hi": "{name} के लिए कम से कम {need} कर्मचारी चाहिए; आपके पास {have} हैं।"},
    "r_min_sites": {"en": "{name} needs at least {need} sites; you have {have}.",
                    "hi": "{name} के लिए कम से कम {need} जगह चाहिए; आपके पास {have} हैं।"},
    "r_requires_gstin": {"en": "{name} needs an active GSTIN{status}.",
                         "hi": "{name} के लिए सक्रिय GSTIN चाहिए{status}।"},
    "r_requires_one_of": {"en": "{name} needs a matching broadband line in the same bundle.",
                          "hi": "{name} के लिए उसी बंडल में सही ब्रॉडबैंड लाइन चाहिए।"},
    "r_no_fibre": {"en": "{name} needs a fibre connection, which is not available at your site.",
                   "hi": "{name} के लिए फाइबर कनेक्शन चाहिए, जो आपकी जगह पर उपलब्ध नहीं है।"},
    "r_substitute": {"en": " We offer {sub} instead.", "hi": " इसकी जगह हम {sub} दे रहे हैं।"},
    "gst_status_cancelled": {"en": " (your GSTIN is cancelled)", "hi": " (आपका GSTIN रद्द है)"},
    "gst_status_suspended": {"en": " (your GSTIN is suspended)", "hi": " (आपका GSTIN निलंबित है)"},
    "gst_status_invalid": {"en": " (the GSTIN entered is not valid)", "hi": " (दर्ज किया गया GSTIN मान्य नहीं है)"},
}

# One plain-language "why" per product.
WHY: dict[str, dict[str, str]] = {
    "P01": {"en": "reliable fibre internet for UPI, billing and daily work", "hi": "UPI, बिलिंग और रोज़ के काम के लिए भरोसेमंद फाइबर इंटरनेट"},
    "P02": {"en": "faster fibre for a team working online all day", "hi": "पूरे दिन ऑनलाइन काम करने वाली टीम के लिए तेज़ फाइबर"},
    "P03": {"en": "very high speed with priority support", "hi": "बहुत तेज़ स्पीड और प्राथमिकता सपोर्ट"},
    "P04": {"en": "wireless 5G broadband, plug-and-play where fibre is not available", "hi": "जहाँ फाइबर नहीं है वहाँ वायरलेस 5G ब्रॉडबैंड, लगाओ और चलाओ"},
    "P05": {"en": "dedicated internet with an uptime guarantee for production", "hi": "उत्पादन के लिए अपटाइम गारंटी वाला समर्पित इंटरनेट"},
    "P06": {"en": "high-capacity dedicated internet for machines and ERP", "hi": "मशीनों और ERP के लिए बड़ी क्षमता वाला समर्पित इंटरनेट"},
    "P07": {"en": "a business mobile number for customers and suppliers", "hi": "ग्राहकों और सप्लायरों के लिए बिज़नेस मोबाइल नंबर"},
    "P08": {"en": "a business mobile with more data and priority care", "hi": "ज़्यादा डेटा और प्राथमिकता सेवा वाला बिज़नेस मोबाइल"},
    "P09": {"en": "keeps you online automatically if the main line goes down", "hi": "मुख्य लाइन बंद होने पर अपने आप इंटरनेट चालू रखता है"},
    "P10": {"en": "manage every site's network from one place", "hi": "सभी जगहों का नेटवर्क एक जगह से संभालें"},
    "P11": {"en": "a fixed IP for CCTV, servers or remote access", "hi": "CCTV, सर्वर या रिमोट एक्सेस के लिए स्थायी IP"},
    "P12": {"en": "office phone lines with IVR and call recording", "hi": "IVR और कॉल रिकॉर्डिंग वाली ऑफ़िस फ़ोन लाइनें"},
    "P13": {"en": "a toll-free number your customers can call", "hi": "ग्राहकों के लिए टोल-फ़्री नंबर"},
    "P14": {"en": "SMS alerts and offers to your customers", "hi": "ग्राहकों को SMS अलर्ट और ऑफ़र"},
    "P15": {"en": "a verified WhatsApp channel with your catalogue", "hi": "आपके कैटलॉग के साथ वेरिफ़ाइड WhatsApp चैनल"},
    "P16": {"en": "business email on your own domain, documents and meetings", "hi": "अपने डोमेन पर बिज़नेस ईमेल, दस्तावेज़ और मीटिंग"},
    "P17": {"en": "automatic backup so records are never lost", "hi": "अपने आप बैकअप, ताकि रिकॉर्ड कभी न खोएँ"},
    "P18": {"en": "a simple website so customers can find you", "hi": "एक आसान वेबसाइट ताकि ग्राहक आपको ढूँढ सकें"},
    "P19": {"en": "GST-ready billing with UPI and card acceptance", "hi": "UPI और कार्ड के साथ GST-तैयार बिलिंग"},
    "P20": {"en": "protects PCs and phones from viruses and ransomware", "hi": "PC और फ़ोन को वायरस और रैनसमवेयर से बचाता है"},
    "P21": {"en": "a managed firewall watched by the Accel security team", "hi": "Accel सुरक्षा टीम द्वारा संभाला गया फ़ायरवॉल"},
    "P22": {"en": "separate, safe Wi-Fi for customers", "hi": "ग्राहकों के लिए अलग और सुरक्षित Wi-Fi"},
    "P23": {"en": "cameras you can watch on your phone, with 30-day recording", "hi": "फ़ोन पर देखे जा सकने वाले कैमरे, 30 दिन की रिकॉर्डिंग"},
    "P24": {"en": "sensors that track machine uptime and energy use", "hi": "मशीन के चलने और बिजली खपत पर नज़र रखने वाले सेंसर"},
    "P25": {"en": "live GPS tracking of your vehicles", "hi": "आपकी गाड़ियों की लाइव GPS ट्रैकिंग"},
}

UI: dict[str, dict[str, str]] = {
    "app_title": {"en": "Accel Business · Udyam Express", "hi": "Accel Business · उद्यम एक्सप्रेस"},
    "tagline": {"en": "Get your business online in one sitting: bundle, price, KYC and tracking.",
                "hi": "एक ही बार में अपना बिज़नेस ऑनलाइन करें: बंडल, कीमत, KYC और ट्रैकिंग।"},
    "nav_advisor": {"en": "1 · Advisor", "hi": "1 · सलाहकार"},
    "nav_quote": {"en": "2 · Quote", "hi": "2 · कोटेशन"},
    "nav_kyc": {"en": "3 · Smart KYC", "hi": "3 · स्मार्ट KYC"},
    "nav_tracker": {"en": "4 · Tracker", "hi": "4 · ट्रैकर"},
    "nav_backoffice": {"en": "Back office", "hi": "बैक ऑफ़िस"},
    "q_business": {"en": "What kind of business do you run?", "hi": "आपका बिज़नेस किस तरह का है?"},
    "q_employees": {"en": "How many people work there?", "hi": "वहाँ कितने लोग काम करते हैं?"},
    "q_sites": {"en": "How many shops / offices / sites?", "hi": "कितनी दुकानें / ऑफ़िस / जगहें?"},
    "q_city": {"en": "Which city?", "hi": "कौन सा शहर?"},
    "q_gstin": {"en": "GSTIN (optional — unlocks WhatsApp, SMS, telephony)", "hi": "GSTIN (वैकल्पिक — WhatsApp, SMS, टेलीफ़ोनी के लिए)"},
    "q_fibre": {"en": "Is fibre broadband available at your site?", "hi": "क्या आपकी जगह पर फाइबर ब्रॉडबैंड उपलब्ध है?"},
    "q_needs": {"en": "What do you need? (pick any)", "hi": "आपको क्या चाहिए? (कोई भी चुनें)"},
    "q_free": {"en": "Or just tell us in your own words", "hi": "या अपने शब्दों में बताइए"},
    "free_ph": {"en": "e.g. I run a kirana in Lucknow with 2 staff, need billing and CCTV",
                "hi": "जैसे: लखनऊ में मेरी किराना दुकान है, 2 लोग काम करते हैं, बिलिंग और कैमरा चाहिए"},
    "btn_recommend": {"en": "Recommend my bundle", "hi": "मेरा बंडल सुझाएँ"},
    "btn_to_quote": {"en": "See my quote →", "hi": "मेरा कोटेशन देखें →"},
    "yes": {"en": "Yes", "hi": "हाँ"}, "no": {"en": "No / not sure", "hi": "नहीं / पता नहीं"},
    "gst_ok": {"en": "GSTIN verified: active", "hi": "GSTIN सत्यापित: सक्रिय"},
    "gst_bad": {"en": "GSTIN status: {status} — GST-only products stay locked", "hi": "GSTIN स्थिति: {status} — GST वाले उत्पाद बंद रहेंगे"},
    "quote_title": {"en": "Your quote", "hi": "आपका कोटेशन"},
    "included": {"en": "Included", "hi": "शामिल"},
    "addons": {"en": "Add-ons (switch on/off)", "hi": "अतिरिक्त सेवाएँ (चालू/बंद करें)"},
    "locked": {"en": "Locked", "hi": "उपलब्ध नहीं"},
    "per_month": {"en": "per month", "hi": "प्रति माह"},
    "setup": {"en": "One-time setup", "hi": "एक बार का सेटअप"},
    "contract": {"en": "Contract", "hi": "अनुबंध"},
    "months": {"en": "months", "hi": "महीने"},
    "install": {"en": "Typical installation", "hi": "सामान्य इंस्टॉलेशन"},
    "days": {"en": "days", "hi": "दिन"},
    "btn_checkout": {"en": "Accept & continue to KYC →", "hi": "स्वीकार करें और KYC पर जाएँ →"},
    "consent_title": {"en": "Your consent (DPDP Act, 2023)", "hi": "आपकी सहमति (DPDP अधिनियम, 2023)"},
    "consent_body": {
        "en": ("Accel Business will use the documents you upload **only to verify your business for this order** "
               "(KYC required by telecom licence rules). We read: GSTIN, Udyam number, business name, constitution, "
               "signatory name and designation, and bill date. We check them against the GST and Udyam registries. "
               "Images are deleted after verification; we keep only the verdict and the fields the telecom licence "
               "requires. GSTIN, Udyam number, names and phone numbers are masked in screens and logs. "
               "You can withdraw consent at any time from the tracker page."),
        "hi": ("Accel Business आपके अपलोड किए गए दस्तावेज़ों का उपयोग **सिर्फ़ इस ऑर्डर के लिए आपके बिज़नेस को सत्यापित करने** "
               "(टेलीकॉम लाइसेंस नियमों के तहत KYC) के लिए करेगा। हम पढ़ते हैं: GSTIN, उद्यम नंबर, बिज़नेस का नाम, संरचना, "
               "हस्ताक्षरकर्ता का नाम और पद, और बिल की तारीख़। इन्हें GST और उद्यम रजिस्ट्री से मिलाया जाता है। "
               "सत्यापन के बाद तस्वीरें हटा दी जाती हैं; हम केवल नतीजा और लाइसेंस के लिए ज़रूरी जानकारी रखते हैं। "
               "GSTIN, उद्यम नंबर, नाम और फ़ोन नंबर स्क्रीन और लॉग में छिपाए जाते हैं। "
               "आप ट्रैकर पेज से कभी भी सहमति वापस ले सकते हैं।"),
    },
    "consent_check": {"en": "I agree to this use of my documents", "hi": "मैं अपने दस्तावेज़ों के इस उपयोग से सहमत हूँ"},
    "btn_consent": {"en": "Give consent", "hi": "सहमति दें"},
    "upload_gst": {"en": "GST certificate", "hi": "GST प्रमाणपत्र"},
    "upload_udyam": {"en": "Udyam certificate (optional — we can look it up)", "hi": "उद्यम प्रमाणपत्र (वैकल्पिक — हम खोज सकते हैं)"},
    "upload_sig": {"en": "Authorised signatory ID", "hi": "अधिकृत हस्ताक्षरकर्ता पहचान पत्र"},
    "upload_addr": {"en": "Address proof (bill ≤ 90 days old)", "hi": "पते का प्रमाण (90 दिन से कम पुराना बिल)"},
    "btn_verify": {"en": "Verify documents", "hi": "दस्तावेज़ सत्यापित करें"},
    "specimen": {"en": "Demo: load specimen applicant", "hi": "डेमो: नमूना आवेदक लोड करें"},
    "v_PASS": {"en": "Verified ✓", "hi": "सत्यापित ✓"},
    "v_AUTO_FIX": {"en": "Verified after automatic fix ✓", "hi": "स्वचालित सुधार के बाद सत्यापित ✓"},
    "v_RECAPTURE": {"en": "Please re-upload", "hi": "कृपया दोबारा अपलोड करें"},
    "v_HOLD": {"en": "On hold — a specialist will call you", "hi": "रोका गया — एक विशेषज्ञ आपको कॉल करेगा"},
    "v_REJECT": {"en": "Could not verify — sent for human review", "hi": "सत्यापन नहीं हो सका — मानवीय जाँच के लिए भेजा गया"},
    "btn_place_order": {"en": "Place order", "hi": "ऑर्डर करें"},
    "order_placed": {"en": "Order placed! Your order ID is", "hi": "ऑर्डर हो गया! आपका ऑर्डर नंबर है"},
    "tracker_title": {"en": "Track your order", "hi": "अपना ऑर्डर ट्रैक करें"},
    "order_id": {"en": "Order ID", "hi": "ऑर्डर नंबर"},
    "btn_track": {"en": "Show status", "hi": "स्थिति दिखाएँ"},
    "eta": {"en": "Expected live by", "hi": "चालू होने की संभावित तारीख़"},
    "no_call": {"en": "No need to call — this page updates at every step, and we'll message you on WhatsApp.",
                "hi": "कॉल करने की ज़रूरत नहीं — यह पेज हर कदम पर अपडेट होता है, और हम WhatsApp पर संदेश भेजेंगे।"},
    "btn_advance": {"en": "Demo: advance to next step", "hi": "डेमो: अगले चरण पर जाएँ"},
    "withdraw": {"en": "Withdraw KYC consent", "hi": "KYC सहमति वापस लें"},
}

NEED_LABELS = {
    "pos": {"en": "Billing / POS", "hi": "बिलिंग / POS"},
    "cctv": {"en": "CCTV cameras", "hi": "CCTV कैमरे"},
    "guest_wifi": {"en": "Customer Wi-Fi", "hi": "ग्राहकों के लिए Wi-Fi"},
    "whatsapp": {"en": "WhatsApp for business", "hi": "बिज़नेस WhatsApp"},
    "sms": {"en": "SMS to customers", "hi": "ग्राहकों को SMS"},
    "email": {"en": "Business email", "hi": "बिज़नेस ईमेल"},
    "backup": {"en": "Data backup", "hi": "डेटा बैकअप"},
    "antivirus": {"en": "Antivirus", "hi": "एंटीवायरस"},
    "telephony": {"en": "Office phone lines / IVR", "hi": "ऑफ़िस फ़ोन लाइन / IVR"},
    "tollfree": {"en": "Toll-free number", "hi": "टोल-फ़्री नंबर"},
    "website": {"en": "Website", "hi": "वेबसाइट"},
    "failover": {"en": "Backup internet (failover)", "hi": "बैकअप इंटरनेट"},
    "sdwan": {"en": "Manage all sites centrally (SD-WAN)", "hi": "सभी जगहों का एक जगह से प्रबंधन (SD-WAN)"},
    "machine_iot": {"en": "Machine monitoring", "hi": "मशीन मॉनिटरिंग"},
    "fleet": {"en": "Vehicle tracking", "hi": "गाड़ी ट्रैकिंग"},
    "static_ip": {"en": "Static IP", "hi": "स्टैटिक IP"},
    "firewall": {"en": "Firewall", "hi": "फ़ायरवॉल"},
    "high_speed": {"en": "Very high speed", "hi": "बहुत तेज़ इंटरनेट"},
    "leased_line": {"en": "Leased line", "hi": "लीज़्ड लाइन"},
}

STAGES = {
    "placed": {"en": "Order placed", "hi": "ऑर्डर हुआ"},
    "kyc_verified": {"en": "KYC verified", "hi": "KYC सत्यापित"},
    "slot_booked": {"en": "Installation slot booked", "hi": "इंस्टॉलेशन स्लॉट बुक"},
    "engineer_assigned": {"en": "Engineer assigned", "hi": "इंजीनियर नियुक्त"},
    "installed": {"en": "Installed", "hi": "इंस्टॉल हुआ"},
    "live": {"en": "Live — welcome to Accel Business", "hi": "चालू — Accel Business में स्वागत है"},
}


def t(key: str, lang: str = "en", **kw) -> str:
    entry = T.get(key) or UI.get(key) or {}
    s = entry.get(lang) or entry.get("en") or key
    return s.format(**kw) if kw else s
