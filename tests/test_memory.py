"""Tests for cross-run change detection (pure diff) and the local memory store."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from brightdata_gtm.memory import LocalMemory, diff_snapshots, remember_and_diff, snapshot  # noqa: E402
from brightdata_gtm.models import AccountIntel, Provenance, Signal, now_iso  # noqa: E402


def _intel(conf, cats, headline="h", one="o"):
    prov = Provenance(source_url="https://s/x", captured_at=now_iso(), method="brightdata:test")
    sigs = [Signal(category=c, summary=(headline if i == 0 else c), provenance=prov, confidence=0.5)
            for i, c in enumerate(cats)]
    return AccountIntel(company="ACME", one_liner=one, signals=sigs, confidence=conf, sources=[prov])


def test_first_seen_has_no_prior():
    d = diff_snapshots(None, snapshot(_intel(0.6, ["hiring"])))
    assert d["first_seen"] is True
    assert d["new_categories"] == ["hiring"]


def test_detects_new_and_dropped_categories_and_confidence_move():
    prev = snapshot(_intel(0.50, ["news"]))
    curr = snapshot(_intel(0.70, ["news", "funding"]))
    d = diff_snapshots(prev, curr)
    assert d["first_seen"] is False
    assert d["new_categories"] == ["funding"]
    assert d["dropped_categories"] == []
    assert d["confidence_delta"] == 0.20
    assert "funding" in d["summary"]


def test_detects_headline_change():
    prev = snapshot(_intel(0.6, ["news"], headline="old story"))
    curr = snapshot(_intel(0.6, ["news"], headline="new story"))
    d = diff_snapshots(prev, curr)
    assert d["headline_changed"] is True
    assert "lead story changed" in d["summary"]


def test_no_material_change():
    snap = snapshot(_intel(0.6, ["news"], headline="same"))
    d = diff_snapshots(snap, snap)
    assert d["confidence_delta"] == 0.0
    assert "no material change" in d["summary"]


def test_local_memory_roundtrip_and_diff(tmp_path, monkeypatch):
    # Keep the unit test offline/deterministic regardless of a local .env.
    monkeypatch.delenv("COGNEE_API_KEY", raising=False)
    mem = LocalMemory(tmp_path / "mem.json")
    assert mem.prior("ACME") is None
    first = remember_and_diff(_intel(0.50, ["news"]), local=mem)
    assert first["first_seen"] is True
    assert first["cognee"] == "disabled"  # no COGNEE_API_KEY in test env
    second = remember_and_diff(_intel(0.65, ["news", "hiring"]), local=mem)
    assert second["first_seen"] is False
    assert second["confidence_delta"] == 0.15
    assert "hiring" in second["new_categories"]
