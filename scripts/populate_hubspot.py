"""Populate HubSpot for the demo: push a real Recon action package (gtm_* fields + sourced
note + urgent task) onto each demo account, so the CRM side is live during the demo.

Uses pre-baked examples where available (instant) and runs live for the rest.
Run: python scripts/populate_hubspot.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.agent import research_account  # noqa: E402
from brightdata_gtm.config import Settings  # noqa: E402
from brightdata_gtm.crm import build_action_package  # noqa: E402
from brightdata_gtm.hubspot import HubSpotClient, HubSpotError  # noqa: E402
from brightdata_gtm.models import AccountIntel  # noqa: E402

DEMO = ["salesforce.com", "vercel.com", "nvidia.com", "linear.app", "notion.so", "webflow.com"]
SHOWCASE_PATH = os.path.join(os.path.dirname(__file__), "..", "examples", "showcase.json")


def main() -> int:
    settings = Settings.load()
    showcase = {}
    if os.path.exists(SHOWCASE_PATH):
        showcase = json.load(open(SHOWCASE_PATH))
    client = HubSpotClient(settings)

    for dom in DEMO:
        try:
            if dom in showcase:
                intel = AccountIntel.model_validate(showcase[dom])
                src = "baked"
            else:
                intel = research_account(dom, settings=settings, include_jobs=True, deep=False)
                src = "live"
            pkg = build_action_package(intel)
            res = client.push(pkg, dom, dry_run=False, create_if_missing=True)
            if res.get("error"):
                print(f"[push] {dom} ({src}): ERROR {res['error']}", flush=True)
            else:
                print(f"[push] {dom} ({src}): company {res.get('company_id')} "
                      f"props={res.get('properties_updated')} note={res.get('note_id')} task={res.get('task_id')} "
                      f"conf={intel.confidence} ready={pkg.action_ready}", flush=True)
        except (HubSpotError, Exception) as e:  # noqa: BLE001 - keep going on one failure
            print(f"[push] {dom}: FAILED {e}", flush=True)
    print("[done] HubSpot population complete.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
