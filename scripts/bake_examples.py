"""Pre-bake example Account Action Plans so the demo loads them instantly and reliably.

Runs the real pipeline once per showcase account and saves the serialized AccountIntel to
examples/showcase.json. The app loads these for one-click instant results (with a clear
"sample" badge), and can still run any account live. Re-bake with: python scripts/bake_examples.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.agent import research_account  # noqa: E402
from brightdata_gtm.config import Settings  # noqa: E402

ACCOUNTS = ["salesforce.com", "vercel.com", "nvidia.com"]
OUT = os.path.join(os.path.dirname(__file__), "..", "examples", "showcase.json")


def main() -> int:
    settings = Settings.load()
    baked: dict[str, dict] = {}
    for dom in ACCOUNTS:
        print(f"[bake] {dom} ...", flush=True)
        try:
            intel = research_account(dom, settings=settings, include_jobs=True, deep=False, verbose=False)
            baked[dom] = intel.model_dump()
            print(f"[bake] {dom}: {len(intel.signals)} signals, conf {intel.confidence}", flush=True)
        except Exception as e:  # noqa: BLE001 - one bad account must not stop the bake
            print(f"[bake] {dom} FAILED: {e}", flush=True)
    with open(OUT, "w") as f:
        json.dump(baked, f, indent=2)
    print(f"[bake] wrote {len(baked)} accounts -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
