"""Test the PDF export (valid PDF bytes, unicode-safe)."""
import os
import sys

import pytest

pytest.importorskip("fpdf")  # skip (not fail) where fpdf2 isn't installed; CI installs requirements

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.models import AccountIntel, Provenance, Signal, now_iso  # noqa: E402
from brightdata_gtm.pdf import build_account_pdf  # noqa: E402

EMDASH = chr(0x2014)
ARROW = chr(0x2192)


def _intel():
    prov = Provenance(source_url="https://x/y", captured_at=now_iso(), method="brightdata:web_unlocker:serp")
    # include unicode that core fonts can't encode, to prove sanitization
    sig = Signal(category="news", summary=f"raised funds {EMDASH} big {ARROW} growth", evidence="e",
                 provenance=prov, confidence=0.6)
    return AccountIntel(company="ACME Corp", one_liner="o", the_read=f"why now {EMDASH} yes",
                        routes=["a"], who_decides=["VP"], evidence_gaps=["x"], next_actions=["call"],
                        signals=[sig, sig], confidence=0.62, llm_used="azure", sources=[prov])


def test_build_account_pdf_returns_valid_pdf_bytes():
    data = build_account_pdf(_intel())
    assert isinstance(data, (bytes, bytearray))
    assert data[:5] == b"%PDF-"  # valid PDF header
    assert len(data) > 800  # non-trivial document


def test_build_account_pdf_handles_empty_low_signal_account():
    # The UI calls this for EVERY rendered account, including thin/low-signal ones.
    # build_action_package still yields a (gated, review-only) task, so the PDF must not crash.
    thin = AccountIntel(company="Thin Co", confidence=0.1, llm_used="fallback", signals=[], sources=[])
    data = build_account_pdf(thin)
    assert data[:5] == b"%PDF-"
    assert len(data) > 500
