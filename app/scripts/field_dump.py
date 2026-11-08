import glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.kyc.ocr import ocr_image, read_field
root = os.path.join(os.path.dirname(__file__), "..", "..", "kyc_documents")
for f in sorted(glob.glob(os.path.join(root, "*_gst_certificate.png")) + glob.glob(os.path.join(root, "*_udyam_certificate.png"))):
    r = ocr_image(f)
    lab = "GSTIN" if "gst" in f else "Udyam"
    print(os.path.basename(f), read_field(r, lab))
