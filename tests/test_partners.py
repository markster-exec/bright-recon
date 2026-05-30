"""Offline tests for the optional partner clients (no network)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.speechmatics import SpeechmaticsClient, SpeechmaticsError  # noqa: E402
from brightdata_gtm.triggerware import TriggerWareClient, TriggerWareError, account_event  # noqa: E402


def test_speechmatics_requires_key():
    with pytest.raises(SpeechmaticsError):
        SpeechmaticsClient("")


def test_triggerware_requires_key_and_endpoint():
    with pytest.raises(TriggerWareError):
        TriggerWareClient("", "https://x")
    with pytest.raises(TriggerWareError):
        TriggerWareClient("k", "")


def test_triggerware_dry_run_plans_without_network():
    c = TriggerWareClient("k", "https://hooks.example/abc")
    res = c.fire("account.actionable", account_event("ACME", 0.62, True, "https://src/x"), dry_run=True)
    assert res["dry_run"] is True
    assert res["body"]["event"] == "account.actionable"
    assert res["body"]["data"]["account"] == "ACME"
    assert res["body"]["source"] == "markster-recon"
