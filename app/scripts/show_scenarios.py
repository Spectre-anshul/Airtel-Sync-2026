"""Print the advisor's explanation for selected scenarios (default: all)."""
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.advisor import advise  # noqa: E402

scs = yaml.safe_load((Path(__file__).parent.parent / "tests" / "advisor_scenarios.yaml").read_text(encoding="utf-8"))
want = set(sys.argv[1:])
for sc in scs:
    if want and sc["id"] not in want:
        continue
    out = advise(dict(sc.get("profile") or {}), sc.get("message"), None, llm=None)
    print(f"===== {sc['id']}: {sc['title']}")
    print(out["explanation"]["text"])
    print()
