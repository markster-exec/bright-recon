"""Smoke tests: lock the confidence fusion + the import path the CLI exercises every run."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.models import Provenance, Signal, now_iso  # noqa: E402
from brightdata_gtm.scoring import fuse_confidence  # noqa: E402


def _sig(category: str, confidence: float) -> Signal:
    prov = Provenance(source_url="https://example.com", captured_at=now_iso(), method="test")
    return Signal(category=category, summary="x", provenance=prov, confidence=confidence)


def test_fuse_confidence_empty_is_low():
    assert fuse_confidence([]) == 0.1


def test_fuse_confidence_is_bounded_and_monotone():
    one = fuse_confidence([_sig("news", 0.5)])
    many = fuse_confidence([_sig("hiring", 0.7), _sig("funding", 0.6), _sig("news", 0.5)])
    assert 0.0 <= one <= 0.95
    assert 0.0 <= many <= 0.95
    assert many >= one  # more, stronger, broader coverage -> not lower


def test_fuse_confidence_honors_weight_overrides():
    sigs = [_sig("news", 0.8)]
    high = fuse_confidence(sigs, weights={"news": 1.0})
    low = fuse_confidence(sigs, weights={"news": 0.1})
    assert high > low  # user-defined Signal priorities actually move the score


def test_research_account_import():
    # The synthesis path imports scoring.py on every run; lock that boundary.
    from brightdata_gtm.agent import research_account

    assert callable(research_account)


def _settings(**over):
    from brightdata_gtm.config import Settings

    base = dict(
        bd_token="t", bd_unlocker_zone="z", bd_serp_zone="z", bd_linkedin_jobs_dataset="d",
        bd_browser_cdp="", provider="featherless", azure_endpoint="", azure_key="",
        azure_deployment="", azure_api_version="v", aimlapi_key="", aimlapi_base_url="u",
        aimlapi_model="m", featherless_key="", featherless_base_url="u", featherless_model="m",
        speechmatics_key="", triggerware_key="", triggerware_webhook_url="",
        hubspot_token="",
    )
    base.update(over)
    return Settings(**base)


def test_provider_ready_reflects_configuration():
    # unconfigured -> not ready (UI shows fallback), configured -> ready
    assert _settings().provider_ready("featherless") is False
    assert _settings(featherless_key="k").provider_ready("featherless") is True
    assert _settings(aimlapi_key="k").provider_ready("aimlapi") is True
    assert _settings(azure_endpoint="e", azure_key="k", azure_deployment="d").provider_ready("azure") is True
    assert _settings().provider_ready("nope") is False


def test_domain_validation_rejects_unsafe_hosts():
    from brightdata_gtm.agent import _brand, _domain_of

    assert _domain_of("stripe.com") == "stripe.com"
    assert _domain_of("foo.bar.com") is None  # subdomain rejected
    assert _domain_of("metadata.google.internal") is None
    assert _domain_of("Stripe") is None  # bare name is not a domain
    assert _brand("stripe.com") == "Stripe"
    assert _brand("GitHub") == "GitHub"  # name passed through verbatim
