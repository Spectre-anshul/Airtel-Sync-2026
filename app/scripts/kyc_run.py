"""Run Smart KYC on all 12 specimen applicants and print verdicts."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.kyc.service import specimen_ids, verify_specimen  # noqa: E402

for k in specimen_ids():
    r = verify_specimen(k)
    print(f"{k}: {r.verdict}  fixes={r.auto_fixes}")
    for c in r.checks:
        if not c.ok:
            print(f"    x {c.code} [{c.severity}] {c.detail} -> {c.action}")
