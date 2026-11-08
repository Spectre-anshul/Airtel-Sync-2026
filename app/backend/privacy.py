"""Masking helpers (DPDP data minimisation in UI and logs)."""
from __future__ import annotations

import logging
import re

GSTIN_RE = re.compile(r"\b\d{2}[A-Z0-9]{13}\b")
UDYAM_RE = re.compile(r"\bUDYAM-([A-Z]{2})-(\d{2})-(\d{7})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[- ]?)?[6-9]\d{9}(?!\d)")


def mask_gstin(g: str | None) -> str:
    """'27XUIXG0767D1ZP' -> '27••••••••D1ZP' (state code + last 4 kept)."""
    if not g:
        return ""
    g = str(g)
    return g[:2] + "•" * 9 + g[11:] if len(g) == 15 else "•" * len(g)


def mask_udyam(u: str | None) -> str:
    if not u:
        return ""
    m = UDYAM_RE.fullmatch(str(u))
    return f"UDYAM-{m.group(1)}-{m.group(2)}-•••{m.group(3)[-4:]}" if m else "•" * len(str(u))


def mask_phone(p: str | None) -> str:
    digits = re.sub(r"\D", "", p or "")
    return ("•" * (len(digits) - 4) + digits[-4:]) if len(digits) >= 4 else ""


def mask_name(n: str | None) -> str:
    """'Joseph Singh' -> 'J••••• S••••'. Keeps the first letter of each word."""
    if not n:
        return ""
    return " ".join(w[0] + "•" * (len(w) - 1) if len(w) > 1 else w for w in str(n).split())


def mask_legal_name(n: str | None) -> str:
    """'Joseph Singh (Prop. Ganesh Woodcraft)' -> 'J••••• S•••• (Prop. Ganesh Woodcraft)'."""
    if not n:
        return ""
    m = re.match(r"^(.*?)\s*\((Prop\..*)\)$", str(n))
    return f"{mask_name(m.group(1))} ({m.group(2)})" if m else str(n)


def scrub(text: str) -> str:
    """Mask any Udyam number, GSTIN or phone number found in free text (for logs)."""
    text = UDYAM_RE.sub(lambda m: mask_udyam(m.group(0)), text)
    text = GSTIN_RE.sub(lambda m: mask_gstin(m.group(0)), text)
    text = PHONE_RE.sub(lambda m: mask_phone(m.group(0)), text)
    return text


class MaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # ASCII mask in logs: Windows consoles and many log shippers mangle '•'
        record.msg = scrub(str(record.getMessage())).replace("•", "*")
        record.args = ()
        return True


def get_logger(name: str) -> logging.Logger:
    log = logging.getLogger(name)
    if not any(isinstance(f, MaskingFilter) for f in log.filters):
        log.addFilter(MaskingFilter())
    if not log.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
        log.addHandler(h)
        log.setLevel(logging.INFO)
    return log
