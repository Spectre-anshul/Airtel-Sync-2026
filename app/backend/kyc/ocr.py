"""Image clean-up + Tesseract OCR for KYC specimens."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

import cv2
import numpy as np
import pytesseract

_DEFAULT_WIN = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
_cmd = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract") or (_DEFAULT_WIN if os.path.exists(_DEFAULT_WIN) else None)
if _cmd:
    pytesseract.pytesseract.tesseract_cmd = _cmd

BLUR_THRESHOLD = 150.0   # variance of Laplacian on the cleaned image; calibrated on the 47 specimens
SKEW_MIN_DEG = 0.7       # below this we don't bother rotating


@dataclass
class OcrResult:
    text: str
    blur_score: float
    skew_deg: float
    deskewed: bool
    image: np.ndarray | None = None   # cleaned, deskewed, binarised image used for OCR

    @property
    def blurred(self) -> bool:
        return self.blur_score < BLUR_THRESHOLD


def load(path_or_bytes) -> np.ndarray:
    if isinstance(path_or_bytes, (bytes, bytearray)):
        arr = np.frombuffer(path_or_bytes, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return cv2.imread(str(path_or_bytes), cv2.IMREAD_COLOR)


def to_gray_without_watermark(img: np.ndarray) -> np.ndarray:
    """The specimen watermark and footer are pink/red. In the red channel they are
    near-white while the black and navy text stays dark, so the red channel is a
    watermark-free grayscale image."""
    return img[:, :, 2].copy()


def _text_mask(gray: np.ndarray) -> np.ndarray:
    return (gray < 110).astype(np.uint8)


def estimate_skew(gray: np.ndarray) -> float:
    """Projection-profile search: the angle that makes text rows sharpest."""
    small = cv2.resize(gray, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
    mask = _text_mask(small) * 255
    h, w = mask.shape
    centre = (w / 2, h / 2)
    best, best_score = 0.0, -1.0
    for coarse in (np.arange(-15, 15.01, 1.0), None):
        angles = coarse if coarse is not None else np.arange(best - 1, best + 1.01, 0.1)
        for a in angles:
            m = cv2.getRotationMatrix2D(centre, a, 1.0)
            rot = cv2.warpAffine(mask, m, (w, h), flags=cv2.INTER_NEAREST, borderValue=0)
            score = float(np.var(rot.sum(axis=1)))
            if score > best_score:
                best, best_score = float(a), score
    return best


def rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))


def blur_score(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def ocr_image(src) -> OcrResult:
    img = load(src)
    if img is None:
        raise ValueError("could not decode image")
    gray = to_gray_without_watermark(img)
    score = blur_score(gray)
    angle = estimate_skew(gray)
    deskewed = abs(angle) >= SKEW_MIN_DEG
    if deskewed:
        gray = rotate(gray, angle)
    # upscale a bit; binarise to drop leftover tint
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(bw, config="--psm 6")
    return OcrResult(text=text, blur_score=score, skew_deg=angle, deskewed=deskewed, image=bw)


ID_WHITELIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-"


def read_field(res: OcrResult, label: str, whitelist: str = ID_WHITELIST) -> str | None:
    """Re-OCR a single value: find the line whose left column starts with `label`,
    crop the value column and read it as one text line with a character whitelist.
    Monospace IDs (GSTIN, Udyam) read far more reliably this way."""
    if res.image is None:
        return None
    img = res.image
    h, w = img.shape[:2]
    data = pytesseract.image_to_data(img, config="--psm 6", output_type=pytesseract.Output.DICT)
    first = label.split()[0].lower()
    for i, word in enumerate(data["text"]):
        if word.strip().lower() != first or data["left"][i] > 0.3 * w:
            continue
        top, height = data["top"][i], data["height"][i]
        y0, y1 = max(0, top - int(height * 0.6)), min(h, top + int(height * 1.8))
        x0 = int(0.38 * w)
        crop = img[y0:y1, x0:]
        crop = cv2.copyMakeBorder(crop, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
        txt = pytesseract.image_to_string(crop, config=f"--psm 7 -c tessedit_char_whitelist={whitelist}")
        return txt.strip().replace(" ", "")
    return None
