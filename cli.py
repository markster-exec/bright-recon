"""CLI: python cli.py "Anthropic" [--location "United States"] [--no-jobs] [--json] [-v]"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from brightdata_gtm.agent import research_account  # noqa: E402
from brightdata_gtm.config import Settings  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Live GTM account intelligence on Bright Data.")
    p.add_argument("company", help="Company name or domain.")
    p.add_argument("--location", default="United States", help="Location hint for hiring signal.")
    p.add_argument("--no-jobs", action="store_true", help="Skip LinkedIn jobs (faster).")
    p.add_argument("--deep", action="store_true", help="Run Deep Lookup structured research (async, slower).")
    p.add_argument("--crm", action="store_true", help="Also print the CRM action package (preview).")
    p.add_argument("--memory", action="store_true", help="Compare to the prior run (change detection) and remember this one.")
    p.add_argument("--push-hubspot", action="store_true", help="Plan the HubSpot push (dry-run unless --hubspot-live).")
    p.add_argument("--hubspot-live", action="store_true", help="With --push-hubspot: actually write to HubSpot.")
    p.add_argument("--json", action="store_true", help="Print raw JSON.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    intel = research_account(
        args.company,
        location=args.location,
        settings=Settings.load(),
        include_jobs=not args.no_jobs,
        deep=args.deep,
        verbose=args.verbose,
    )

    if args.json:
        print(intel.model_dump_json(indent=2))
        return 0

    print(f"\n=== Markster Recon - Account Action Plan: {intel.company} ===")
    print(f"{intel.one_liner}\n")
    print(f"THE READ\n  {intel.the_read}\n")
    if intel.terrain:
        print(f"TERRAIN\n  {intel.terrain}\n")
    if intel.routes:
        print("ROUTES TO ENTER")
        for r in intel.routes:
            print(f"  - {r}")
        print()
    if intel.who_decides:
        print("WHO SHAPES THE DECISION")
        for w in intel.who_decides:
            print(f"  - {w}")
        print()
    print("LIVE SIGNALS")
    for s in intel.signals:
        print(f"  [{s.category}] ({s.confidence:.0%}) {s.summary}")
        print(f"      source: {s.provenance.source_url}  ({s.provenance.method})")
    print()
    if intel.evidence_gaps:
        print("EVIDENCE GAPS (verify before acting)")
        for g in intel.evidence_gaps:
            print(f"  - {g}")
        print()
    print("NEXT ACTIONS (most urgent first)")
    for i, a in enumerate(intel.next_actions, 1):
        print(f"  {i}. {a}")
    print(f"\nconfidence={intel.confidence:.0%} (coverage x signal strength) | llm={intel.llm_used} | sources={len(intel.sources)}")

    if args.memory:
        from brightdata_gtm.memory import remember_and_diff

        change = remember_and_diff(intel)
        print(f"\nCHANGE SINCE LAST RUN  (cognee: {change['cognee']})\n  {change['summary']}")
        if change["cognee"] == "unavailable":
            print(f"  WARNING: Cognee is configured but the endpoint rejected the request "
                  f"({change.get('cognee_endpoint', '?')}); using local memory only. Check COGNEE_API_KEY.")

    if args.crm:
        from brightdata_gtm.crm import build_action_package

        pkg = build_action_package(intel)
        print("\n=== CRM ACTION PACKAGE (preview - exactly what would be written) ===")
        print(f"Company match key: {pkg.company}  | action-ready: {pkg.action_ready}")
        if pkg.caveat:
            print(f"  WARNING: {pkg.caveat}")
        print("Properties:")
        for k, v in pkg.properties.items():
            print(f"  {k} = {v}")
        print(f"Task: [{pkg.task.priority}] {pkg.task.subject}  (suggested due {pkg.task.due_date})")
        print("\nNote (markdown):\n" + pkg.note_markdown)

    if args.push_hubspot:
        from brightdata_gtm.crm import build_action_package
        from brightdata_gtm.hubspot import HubSpotClient, HubSpotError

        pkg = build_action_package(intel)
        domain = args.company.strip().lower()
        mode = "LIVE" if args.hubspot_live else "DRY-RUN"
        print(f"\n=== HubSpot push ({mode}) ===")
        try:
            res = HubSpotClient(Settings.load()).push(
                pkg, domain, dry_run=not args.hubspot_live, create_if_missing=True
            )
            print({k: v for k, v in res.items() if k not in ("note_payload", "task_payload")})
        except HubSpotError as e:
            print(f"HubSpot push failed: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
