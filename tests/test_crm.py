"""Tests for the CRM action package builder (Phase 3 preview)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.crm import build_action_package, gtm_properties  # noqa: E402
from brightdata_gtm.models import AccountIntel, Provenance, Signal, now_iso  # noqa: E402

# The 13 company properties that actually exist in the HubSpot "GTM Intelligence"
# group (docs/hubspot-crm-setup.md). The push must emit exactly these names.
HUBSPOT_GTM_FIELDS = {
    "gtm_one_liner", "gtm_why_now", "gtm_recommended_action", "gtm_confidence",
    "gtm_signal_count", "gtm_hiring_signal", "gtm_funding_signal", "gtm_pricing_signal",
    "gtm_news_signal", "gtm_top_source_url", "gtm_llm_used", "gtm_generated_at", "gtm_source",
}


def _intel(confidence: float, llm_used: str = "azure", n_signals: int = 2) -> AccountIntel:
    prov = Provenance(source_url="https://src.example/x", captured_at=now_iso(), method="brightdata:test")
    sig = Signal(category="news", summary="news for X", evidence="ev", provenance=prov, confidence=0.5)
    return AccountIntel(
        company="X",
        one_liner="o",
        the_read="r",
        routes=["route a"],
        next_actions=["do the thing"],
        signals=[sig] * n_signals,
        confidence=confidence,
        llm_used=llm_used,
        sources=[prov],
    )


def test_gtm_properties_match_hubspot_schema_with_correct_types():
    prov = Provenance(source_url="https://src.example/x", captured_at=now_iso(), method="brightdata:test")
    hiring = Signal(category="hiring", summary="12 roles", evidence="e", provenance=prov, confidence=0.72)
    fund = Signal(category="funding", summary="Series C", evidence="e", provenance=prov, confidence=0.6)
    intel = AccountIntel(
        company="X", one_liner="o", the_read="why now", next_actions=["call"],
        signals=[hiring, fund], confidence=0.71, llm_used="aimlapi", sources=[prov],
    )
    props = gtm_properties(intel)
    assert set(props) == HUBSPOT_GTM_FIELDS  # exactly the real portal fields, nothing else
    assert props["gtm_confidence"] == "0.71"  # number-typed property
    assert props["gtm_signal_count"] == "2"   # number-typed property
    assert len(props["gtm_generated_at"]) == 10  # date-typed property: YYYY-MM-DD
    assert props["gtm_hiring_signal"] == "12 roles"
    assert props["gtm_funding_signal"] == "Series C"
    assert props["gtm_llm_used"] == "aimlapi"


def test_ready_priority_buckets():
    assert build_action_package(_intel(0.80)).task.priority == "HIGH"
    assert build_action_package(_intel(0.55)).task.priority == "MEDIUM"


def test_note_includes_sourced_signal_and_props():
    pkg = build_action_package(_intel(0.70))
    assert "https://src.example/x" in pkg.note_markdown  # signal source link present
    assert "Live signals" in pkg.note_markdown
    # CRM properties mirror the real HubSpot "GTM Intelligence" group (gtm_*).
    assert pkg.properties["gtm_confidence"] == "0.70"
    assert pkg.properties["gtm_signal_count"] == "2"
    assert pkg.properties["gtm_source"] == "brightdata-gtm-agent"
    assert "recon_" not in " ".join(pkg.properties)  # no orphan recon_* props
    assert pkg.task.subject.startswith("Recon:")
    assert pkg.action_ready is True


def test_due_date_is_suggestion_shaped():
    pkg = build_action_package(_intel(0.70))
    assert len(pkg.task.due_date) == 10  # YYYY-MM-DD, derived from run time
    assert "suggestion" in pkg.task.body.lower()


def test_thin_run_is_gated_not_action_ready():
    # fallback LLM + low confidence + single signal must NOT look operationally ready
    pkg = build_action_package(_intel(0.30, llm_used="fallback", n_signals=1))
    assert pkg.action_ready is False
    assert pkg.task.priority == "LOW"
    assert "review only" in pkg.task.subject.lower()
    assert pkg.properties["gtm_signal_count"] == "1"
    assert pkg.caveat
