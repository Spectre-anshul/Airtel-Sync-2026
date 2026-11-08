"""GSTIN format, mod-36 checksum and OCR-aware correction."""
from __future__ import annotations

import re
from typing import Callable

CH = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# 2 state digits, 5 PAN letters, 4 PAN digits, PAN check letter, entity code, 'Z', checksum.
# PAN position 4 (GSTIN index 5) is the holder-type letter. The case data puts an 'X' there,
# which real PANs never use; the project rules say to accept it, so any letter is allowed.
FORMAT = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]")

# Character class at each of the 15 positions: D = digit, L = letter, A = either.
CLASSES = "DDLLLLLDDDDLAAA"
TO_DIGIT = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "T": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "8": "B", "6": "G"}
# Same-class pairs Tesseract confuses. Used only together with a checksum + registry check.
CONFUSABLE = {
    "I": "JTL", "J": "I", "T": "I", "L": "I",
    "O": "0DQ", "0": "O9", "D": "O0", "Q": "O",
    "1": "I7", "7": "1", "9": "0", "8": "B", "B": "8",
    "Z": "2", "2": "Z", "S": "5", "5": "S", "G": "6", "6": "G",
}


def checksum_char(first14: str) -> str:
    s = 0
    for i, c in enumerate(first14):
        v = CH.index(c) * (1 if i % 2 == 0 else 2)
        s += v // 36 + v % 36
    return CH[(36 - s % 36) % 36]


def is_valid_format(g: str) -> bool:
    return bool(FORMAT.fullmatch(g or ""))


def is_valid(g: str) -> bool:
    return is_valid_format(g) and checksum_char(g[:14]) == g[14]


def validate(g: str) -> dict:
    g = (g or "").strip().upper()
    if not is_valid_format(g):
        return {"gstin": g, "format_ok": False, "checksum_ok": False, "error": "bad_format"}
    ok = checksum_char(g[:14]) == g[14]
    return {"gstin": g, "format_ok": True, "checksum_ok": ok, "error": None if ok else "bad_checksum"}


def clean(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (raw or "").upper())


def normalise_by_position(g: str) -> str:
    """Fix letter/digit swaps using the class of each position (24X0R... -> 24XOR...)."""
    if len(g) != 15:
        return g
    out = []
    for c, cls in zip(g, CLASSES):
        if cls == "D" and not c.isdigit():
            c = TO_DIGIT.get(c, c)
        elif cls == "L" and c.isdigit():
            c = TO_LETTER.get(c, c)
        out.append(c)
    g = "".join(out)
    return g[:13] + "Z" + g[14] if g[13] == "2" else g


def _length_variants(g: str) -> list[str]:
    """OCR sometimes inserts one character ('1Z' read as '12Z')."""
    if len(g) == 15:
        return [g]
    if len(g) == 16:
        return [g[:i] + g[i + 1:] for i in range(16)]
    return []


def correct(raw: str, exists: Callable[[str], bool] | None = None) -> dict:
    """Best reading of an OCR'd GSTIN.

    1. Position-class normalisation (a format rule, always applied).
    2. If the checksum still fails, try one confusable-character swap. A swap is accepted only
       if the result passes the checksum AND exists in the registry (when `exists` is given).
    A genuinely altered digit (e.g. 5 -> 8) is not a confusable pair, so it is never "fixed".
    """
    g0 = clean(raw)
    for g in _length_variants(g0):
        g = normalise_by_position(g)
        if is_valid(g) and (exists is None or exists(g)):
            return {"raw": raw, "gstin": g, "method": "exact" if g == g0 else "position", "checksum_ok": True}
    for g in _length_variants(g0):
        g = normalise_by_position(g)
        for i, c in enumerate(g):
            for alt in CONFUSABLE.get(c, ""):
                cand = g[:i] + alt + g[i + 1:]
                if is_valid(cand) and (exists is None or exists(cand)):
                    return {"raw": raw, "gstin": cand, "method": f"ocr_swap {c}->{alt} at {i + 1}", "checksum_ok": True}
    best = normalise_by_position(g0) if len(g0) == 15 else g0
    return {"raw": raw, "gstin": best, "method": "unresolved", "checksum_ok": is_valid(best)}
