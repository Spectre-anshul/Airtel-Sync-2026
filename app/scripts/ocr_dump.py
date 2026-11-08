"""Dev helper: print raw OCR for every specimen image."""
import glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.kyc.ocr import ocr_image
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "kyc_documents", "*.png"))):
    r = ocr_image(f)
    print("=====", os.path.basename(f), "blur=%.0f skew=%.1f" % (r.blur_score, r.skew_deg))
    print(r.text.strip())
