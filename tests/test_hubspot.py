"""Offline tests for the HubSpot push (dry-run path - no network)."""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.crm import build_action_package  # noqa: E402
from brightdata_gtm.hubspot import HubSpotClient  # noqa: E402
from brightdata_gtm.models import AccountIntel, Provenance, Signal, now_iso  # noqa: E402


def _pkg():
    prov = Provenance(source_url="https://src.example/x", captured_at=now_iso(), method="brightdata:test")
    sig = Signal(category="news", summary="s", evidence="e", provenance=prov, confidence=0.5)
    intel = AccountIntel(
        company="X", one_liner="o", the_read="r", next_actions=["do a"],
        signals=[sig, sig], confidence=0.70, llm_used="azure", sources=[prov],
    )
    return build_action_package(intel)


def test_token_override_and_no_env_needed():
    # token override avoids needing Settings/env; __init__ does no network
    client = HubSpotClient(SimpleNamespace(hubspot_token=""), token="x")
    assert client.http.headers["Authorization"] == "Bearer x"


def test_push_dry_run_plans_without_network():
    client = HubSpotClient(SimpleNamespace(hubspot_token=""), token="x")
    res = client.push(_pkg(), "x.com", dry_run=True)
    assert res["dry_run"] is True
    assert "hs_note_body" in res["note_payload"]
    assert res["task_payload"]["hs_task_subject"].startswith("Recon:")
    assert res["task_payload"]["hs_task_status"] == "NOT_STARTED"
